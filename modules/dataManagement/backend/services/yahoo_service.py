"""
Servizio per interagire con Yahoo Finance
Principio SOLID: Single Responsibility - gestisce solo Yahoo Finance
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import time

from core.backend.base.base_service import BaseService
from core.backend.config.settings import YAHOO_API_TIMEOUT, YAHOO_MAX_RETRIES


class YahooFinanceService(BaseService):
    """Servizio per recuperare dati da Yahoo Finance"""
    
    def __init__(self):
        super().__init__()
        self.timeout = YAHOO_API_TIMEOUT
        self.max_retries = YAHOO_MAX_RETRIES
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Valida i parametri di input"""
        required_fields = ['symbol', 'start_date', 'end_date']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Campo richiesto mancante: {field}")
        
        # Normalizza e valida date
        try:
            # Assicurati che siano stringhe
            start_date_str = str(data['start_date']).strip()
            end_date_str = str(data['end_date']).strip()
            
            # Valida formato
            start = datetime.strptime(start_date_str, '%Y-%m-%d')
            end = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            # Controlli logici
            if start > end:
                raise ValueError("La data di inizio deve essere prima della data di fine")
            
            now = datetime.now()
            if end > now:
                raise ValueError("La data di fine non può essere nel futuro")
                
            # Controlla che il periodo non sia troppo lungo
            period_days = (end - start).days
            if period_days > 5 * 365:  # 5 anni
                raise ValueError("Il periodo richiesto è troppo lungo (massimo 5 anni)")
            
            # Controlla che il periodo non sia troppo vecchio
            years_ago = (now - start).days / 365
            if years_ago > 20:
                raise ValueError("Dati non disponibili per periodi superiori a 20 anni fa")
                
        except ValueError as e:
            if "time data" in str(e) or "does not match format" in str(e):
                raise ValueError(f"Formato data non valido. Usa YYYY-MM-DD. Ricevuto: start_date='{data.get('start_date')}', end_date='{data.get('end_date')}'")
            raise e
        except Exception as e:
            raise ValueError(f"Errore nella validazione delle date: {str(e)}")
        
        return True
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str, 
                      interval: str = '1d') -> Dict[str, Any]:
        """Recupera i dati storici di un titolo"""
        try:
            # Normalizza parametri
            symbol = str(symbol).strip().upper()
            start_date = str(start_date).strip()
            end_date = str(end_date).strip()
            
            self.log_info(f"=== INIZIO RECUPERO DATI ===")
            self.log_info(f"Simbolo: {symbol}")
            self.log_info(f"Date: {start_date} -> {end_date}")
            self.log_info(f"Intervallo: {interval}")
            
            # Valida input
            self.validate_input({
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date
            })
            
            # Verifica che le date siano ragionevoli
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            now = datetime.now()
            
            if end_dt > now:
                self.log_error(f"Data di fine nel futuro: {end_date} > {now.strftime('%Y-%m-%d')}")
                raise ValueError(f"La data di fine {end_date} è nel futuro")
            
            self.log_info(f"Validazione date OK")
            
            # Prova con retry
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    self.log_info(f"=== TENTATIVO {attempt + 1}/{self.max_retries} ===")
                    
                    # Crea oggetto Ticker
                    ticker = yf.Ticker(symbol)
                    self.log_info(f"Ticker creato per {symbol}")
                    
                    # Recupera dati storici
                    self.log_info(f"Chiamata ticker.history...")
                    data = ticker.history(
                        start=start_date,
                        end=end_date,
                        interval=interval,
                        timeout=self.timeout
                    )
                    
                    self.log_info(f"Risposta Yahoo Finance: {len(data)} record")
                    self.log_info(f"Dati vuoti: {data.empty}")
                    
                    if not data.empty:
                        self.log_info(f"Colonne disponibili: {list(data.columns)}")
                        self.log_info(f"Prima data: {data.index[0]}")
                        self.log_info(f"Ultima data: {data.index[-1]}")
                    
                    if data.empty:
                        self.log_info(f"Dati vuoti per {symbol}, provo alternative...")
                        
                        # Prova con un periodo più recente per test
                        test_end = datetime(2024, 12, 31)
                        test_start = datetime(2024, 12, 1)
                        
                        self.log_info(f"Test con periodo: {test_start.strftime('%Y-%m-%d')} -> {test_end.strftime('%Y-%m-%d')}")
                        
                        test_data = ticker.history(
                            start=test_start.strftime('%Y-%m-%d'),
                            end=test_end.strftime('%Y-%m-%d'),
                            interval=interval,
                            timeout=self.timeout
                        )
                        
                        if not test_data.empty:
                            self.log_info(f"Test period OK: {len(test_data)} record")
                            raise ValueError(
                                f"Il simbolo {symbol} esiste ma non ha dati per il periodo {start_date} - {end_date}. "
                                f"Prova con un periodo diverso (es. dicembre 2024)."
                            )
                        else:
                            self.log_info(f"Anche test period fallito, provo simboli alternativi...")
                            
                            # Prova varianti del simbolo
                            alternative_symbols = self._get_symbol_alternatives(symbol)
                            for alt_symbol in alternative_symbols[:3]:  # Limita a 3 per evitare troppi tentativi
                                self.log_info(f"Tentativo con simbolo alternativo: {alt_symbol}")
                                try:
                                    alt_ticker = yf.Ticker(alt_symbol)
                                    alt_data = alt_ticker.history(
                                        start=test_start.strftime('%Y-%m-%d'),
                                        end=test_end.strftime('%Y-%m-%d'),
                                        interval=interval,
                                        timeout=self.timeout
                                    )
                                    if not alt_data.empty:
                                        self.log_info(f"Successo con simbolo alternativo: {alt_symbol}")
                                        # Ora prova con il periodo originale
                                        data = alt_ticker.history(
                                            start=start_date,
                                            end=end_date,
                                            interval=interval,
                                            timeout=self.timeout
                                        )
                                        if not data.empty:
                                            symbol = alt_symbol
                                            break
                                except Exception as alt_error:
                                    self.log_info(f"Errore con {alt_symbol}: {str(alt_error)}")
                                    continue
                            
                            if data.empty:
                                raise ValueError(
                                    f"Nessun dato trovato per {symbol}. "
                                    f"Possibili cause:\n"
                                    f"• Simbolo non valido: prova AAPL, MSFT, GOOG\n"
                                    f"• Periodo non disponibile: prova 2024-01-01 to 2024-12-31\n"
                                    f"• Problemi temporanei con Yahoo Finance"
                                )
                    
                    # Se arriviamo qui, abbiamo dati
                    result = self._prepare_data_response(data, symbol)
                    self.log_info(f"✓ Successo: {len(data)} record per {symbol}")
                    return result
                    
                except Exception as e:
                    last_error = e
                    error_msg = str(e)
                    self.log_error(f"Tentativo {attempt + 1} fallito: {error_msg}")
                    
                    if attempt < self.max_retries - 1:
                        self.log_info(f"Aspetto 2 secondi prima del prossimo tentativo...")
                        time.sleep(2)
                        continue
                    else:
                        raise e
            
        except Exception as e:
            error_msg = str(e)
            self.log_error(f"ERRORE FINALE per {symbol}: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'context': f"get_stock_data({symbol})"
            }
    
    def _get_symbol_alternatives(self, symbol: str) -> List[str]:
        """Genera simboli alternativi per il ticker"""
        alternatives = []
        
        # Mappings comuni per simboli specifici
        common_mappings = {
            'META': ['FB'],  # Meta Platforms (ex Facebook)
            'FB': ['META'],  # Facebook -> Meta
            'GOOGL': ['GOOG'],  # Alphabet Class A -> Class C
            'GOOG': ['GOOGL'],  # Alphabet Class C -> Class A
            'BRK.A': ['BRK-A', 'BRKA'],  # Berkshire Hathaway variants
            'BRK.B': ['BRK-B', 'BRKB'],
            'TSLA': [],  # Tesla - no alternatives needed usually
            'AAPL': [],  # Apple - no alternatives needed
            'MSFT': [],  # Microsoft - no alternatives needed
            'AMZN': [],  # Amazon - no alternatives needed
            'NVDA': [],  # Nvidia - no alternatives needed
        }
        
        if symbol in common_mappings:
            alternatives.extend(common_mappings[symbol])
        
        # Se non ha già il suffisso, prova ad aggiungere suffissi di mercato
        if '.' not in symbol and '-' not in symbol and symbol not in ['META', 'FB', 'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'TSLA', 'AMZN', 'NVDA']:
            # Solo per simboli meno comuni aggiungi suffissi internazionali
            alternatives.extend([
                f"{symbol}.TO",  # Toronto
                f"{symbol}.L",   # London
            ])
        
        # Varianti comuni di formato
        if symbol.endswith('L') and len(symbol) > 1:
            alternatives.append(symbol[:-1])  # Rimuovi L finale
        
        if '.' in symbol:
            alternatives.append(symbol.replace('.', '-'))  # . -> -
        if '-' in symbol:
            alternatives.append(symbol.replace('-', '.'))  # - -> .
        
        # Rimuovi duplicati e limita
        alternatives = list(dict.fromkeys(alternatives))  # Remove duplicates
        return alternatives[:3]  # Limita a 3 tentativi per velocizzare
    
    def get_multiple_stocks(self, symbols: List[str], start_date: str, 
                          end_date: str) -> Dict[str, Any]:
        """Recupera dati per multipli titoli"""
        try:
            results = {}
            errors = []
            
            for symbol in symbols:
                result = self.get_stock_data(symbol, start_date, end_date)
                
                if result['success']:
                    results[symbol] = result['data']
                else:
                    errors.append({
                        'symbol': symbol,
                        'error': result.get('error', 'Errore sconosciuto')
                    })
            
            return {
                'success': True,
                'data': results,
                'errors': errors if errors else None
            }
            
        except Exception as e:
            return self.handle_error(e, "get_multiple_stocks")
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """Recupera informazioni dettagliate su un titolo"""
        try:
            symbol = symbol.strip().upper()
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            if not info or len(info) < 5:  # Info troppo scarse
                raise ValueError(f"Informazioni non disponibili per {symbol}")
            
            # Estrai informazioni principali con fallback
            return {
                'success': True,
                'data': {
                    'symbol': symbol,
                    'name': info.get('longName', info.get('shortName', symbol)),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'currency': info.get('currency', 'USD'),
                    'exchange': info.get('exchange', 'N/A'),
                    'market_cap': info.get('marketCap', 0),
                    'current_price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                    'previous_close': info.get('previousClose', 0),
                    'day_high': info.get('dayHigh', 0),
                    'day_low': info.get('dayLow', 0),
                    'volume': info.get('volume', 0)
                }
            }
            
        except Exception as e:
            return self.handle_error(e, f"get_stock_info({symbol})")
    
    def test_connection(self) -> Dict[str, Any]:
        """Testa la connessione a Yahoo Finance"""
        try:
            self.log_info("=== TEST CONNESSIONE YAHOO FINANCE ===")
            
            # Prova con un simbolo molto comune
            ticker = yf.Ticker("AAPL")
            
            # Test 1: Info simbolo
            self.log_info("Test 1: Info simbolo...")
            try:
                info = ticker.info
                if not info or len(info) < 3:
                    self.log_info("Warning: Info simbolo insufficienti")
                else:
                    self.log_info(f"✓ Info simbolo OK: {info.get('longName', 'N/A')}")
            except Exception as e:
                self.log_info(f"Warning info simbolo: {str(e)}")
            
            # Test 2: Dati storici con date sicure
            self.log_info("Test 2: Dati storici...")
            
            # Usa date del 2024 che sono sicuramente nel passato
            test_start = "2024-12-01"
            test_end = "2024-12-31"
            
            self.log_info(f"Periodo test: {test_start} -> {test_end}")
            
            recent_data = ticker.history(
                start=test_start,
                end=test_end,
                timeout=self.timeout
            )
            
            if recent_data.empty:
                # Prova con un periodo più lungo
                test_start = "2024-01-01"
                test_end = "2024-12-31"
                self.log_info(f"Secondo tentativo: {test_start} -> {test_end}")
                
                recent_data = ticker.history(
                    start=test_start,
                    end=test_end,
                    timeout=self.timeout
                )
            
            if recent_data.empty:
                raise Exception("Impossibile recuperare dati storici anche con periodo esteso")
            
            self.log_info(f"✓ Dati storici OK: {len(recent_data)} record")
            
            last_price = float(recent_data['Close'].iloc[-1])
            last_date = recent_data.index[-1].strftime('%Y-%m-%d')
            
            self.log_info("✓ ✓ ✓ CONNESSIONE YAHOO FINANCE OK")
            
            return {
                'success': True,
                'data': {
                    'connection': 'OK',
                    'test_symbol': 'AAPL',
                    'sample_price': last_price,
                    'data_points': len(recent_data),
                    'last_date': last_date,
                    'test_period': f"{test_start} to {test_end}"
                }
            }
            
        except Exception as e:
            error_msg = f"Test connessione fallito: {str(e)}"
            self.log_error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'context': 'test_connection'
            }
    
    def _prepare_data_response(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Prepara la risposta con i dati del DataFrame"""
        # Reset index per avere la data come colonna
        data_reset = data.reset_index()
        
        # Converti in formato JSON-friendly
        records = []
        for _, row in data_reset.iterrows():
            records.append({
                'date': row['Date'].strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume'])
            })
        
        return {
            'success': True,
            'data': {
                'symbol': symbol,
                'records': records,
                'count': len(records),
                'first_date': records[0]['date'] if records else None,
                'last_date': records[-1]['date'] if records else None
            }
        }