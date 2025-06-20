"""
Servizio per interagire con Yahoo Finance - Enhanced Version
Principio SOLID: Single Responsibility - gestisce solo Yahoo Finance
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import time

from core.backend.base.base_service import BaseService
from core.backend.config.settings import YAHOO_API_TIMEOUT, YAHOO_MAX_RETRIES
from ..services.file_manager import FileManagerService
from ..services.adjusted_data import AdjustedDataService


class YahooFinanceService(BaseService):
    """Servizio per recuperare dati da Yahoo Finance con cache e download incrementale"""
    
    def __init__(self):
        super().__init__()
        self.timeout = YAHOO_API_TIMEOUT
        self.max_retries = YAHOO_MAX_RETRIES
        self.file_manager = FileManagerService()
        self.adjusted_service = AdjustedDataService()
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Valida i parametri di input"""
        required_fields = ['symbol', 'start_date', 'end_date']
        
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Campo richiesto mancante: {field}")
        
        # Normalizza e valida date
        try:
            start_date_str = str(data['start_date']).strip()
            end_date_str = str(data['end_date']).strip()
            
            start = datetime.strptime(start_date_str, '%Y-%m-%d')
            end = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            if start > end:
                raise ValueError("La data di inizio deve essere prima della data di fine")
            
            now = datetime.now()
            if end > now:
                raise ValueError("La data di fine non può essere nel futuro")
                
            period_days = (end - start).days
            if period_days > 5 * 365:
                raise ValueError("Il periodo richiesto è troppo lungo (massimo 5 anni)")
            
            years_ago = (now - start).days / 365
            if years_ago > 20:
                raise ValueError("Dati non disponibili per periodi superiori a 20 anni fa")
                
        except ValueError as e:
            if "time data" in str(e) or "does not match format" in str(e):
                raise ValueError(f"Formato data non valido. Usa YYYY-MM-DD")
            raise e
        except Exception as e:
            raise ValueError(f"Errore nella validazione delle date: {str(e)}")
        
        return True
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str, 
                      interval: str = '1d', use_cache: bool = True,
                      adjusted: bool = True) -> Dict[str, Any]:
        """
        Recupera i dati storici di un titolo con supporto cache e download incrementale
        
        Args:
            symbol: Simbolo del titolo
            start_date: Data inizio
            end_date: Data fine
            interval: Intervallo dati (1d, 1m, etc)
            use_cache: Se True, usa dati salvati e scarica solo i mancanti
            adjusted: Se True, scarica e calcola prezzi adjusted
        """
        try:
            symbol = str(symbol).strip().upper()
            start_date = str(start_date).strip()
            end_date = str(end_date).strip()
            
            # Determina il tipo di dati
            data_type = self._get_data_type(interval, adjusted)
            
            self.log_info(f"=== RECUPERO DATI {data_type} ===")
            self.log_info(f"Simbolo: {symbol}, Periodo: {start_date} -> {end_date}")
            
            # Valida input
            self.validate_input({
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date
            })
            
            # Se use_cache, prova a usare dati esistenti
            if use_cache:
                cached_data, missing_start, missing_end = self._check_cached_data(
                    symbol, data_type, start_date, end_date
                )
                
                if cached_data is not None and missing_start is None:
                    # Tutti i dati sono già presenti
                    self.log_info("Tutti i dati richiesti sono già in cache")
                    return self._prepare_response_from_cache(
                        cached_data, symbol, start_date, end_date
                    )
                
                if missing_start and missing_end:
                    # Scarica solo i dati mancanti
                    self.log_info(f"Download incrementale: {missing_start} -> {missing_end}")
                    new_data = self._download_from_yahoo(
                        symbol, missing_start, missing_end, interval
                    )
                    
                    if new_data['success']:
                        # Processa dati adjusted se richiesto
                        if adjusted:
                            records = self.adjusted_service.calculate_adjusted_prices(
                                new_data['data']['records'],
                                has_adjusted=True
                            )
                            new_data['data']['records'] = records
                        
                        # Salva nuovi dati
                        self.file_manager.append_data(
                            symbol, data_type, new_data['data']['records']
                        )
                        
                        # Ricarica tutti i dati
                        all_data = self.file_manager.load_data(symbol, data_type)
                        return self._prepare_response_from_cache(
                            all_data, symbol, start_date, end_date
                        )
            
            # Download completo
            result = self._download_from_yahoo(symbol, start_date, end_date, interval)
            
            if result['success']:
                # Processa dati adjusted se richiesto
                if adjusted:
                    records = self.adjusted_service.calculate_adjusted_prices(
                        result['data']['records'],
                        has_adjusted=True
                    )
                    result['data']['records'] = records
                
                # Salva in cache
                if use_cache:
                    self.file_manager.save_data(
                        symbol, data_type, result['data']['records'],
                        metadata={
                            'source': 'yahoo_finance',
                            'interval': interval,
                            'adjusted': adjusted
                        }
                    )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            self.log_error(f"Errore per {symbol}: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'context': f"get_stock_data({symbol})"
            }
    
    def get_full_history(self, symbol: str, adjusted: bool = True) -> Dict[str, Any]:
        """Scarica lo storico completo disponibile per un simbolo"""
        try:
            symbol = str(symbol).strip().upper()
            self.log_info(f"Download storico completo per {symbol}")
            
            # Yahoo Finance di solito ha dati dal 1970 circa
            start_date = "1900-01-01"  # Yahoo ignorerà date troppo vecchie
            end_date = datetime.now().strftime('%Y-%m-%d')
            
            return self.get_stock_data(
                symbol, start_date, end_date,
                interval='1d', use_cache=True, adjusted=adjusted
            )
            
        except Exception as e:
            return self.handle_error(e, f"get_full_history({symbol})")
    
    def _get_data_type(self, interval: str, adjusted: bool) -> str:
        """Determina il tipo di dati basato su intervallo e adjusted"""
        if interval == '1m':
            return 'minute'
        elif adjusted:
            return 'dailyAdjusted'
        else:
            return 'daily'
    
    def _check_cached_data(self, symbol: str, data_type: str, 
                          start_date: str, end_date: str) -> Tuple[Optional[pd.DataFrame], 
                                                                   Optional[str], 
                                                                   Optional[str]]:
        """
        Controlla dati in cache e determina periodo mancante
        
        Returns:
            (cached_data, missing_start_date, missing_end_date)
        """
        try:
            # Carica dati esistenti
            cached_df = self.file_manager.load_data(symbol, data_type)
            
            if cached_df is None or cached_df.empty:
                # Nessun dato in cache
                return None, start_date, end_date
            
            # Converti date richieste
            req_start = pd.to_datetime(start_date)
            req_end = pd.to_datetime(end_date)
            
            # Date disponibili in cache
            cache_start = cached_df['date'].min()
            cache_end = cached_df['date'].max()
            
            self.log_info(f"Cache disponibile: {cache_start.strftime('%Y-%m-%d')} -> "
                         f"{cache_end.strftime('%Y-%m-%d')}")
            
            # Caso 1: Tutti i dati richiesti sono in cache
            if cache_start <= req_start and cache_end >= req_end:
                return cached_df, None, None
            
            # Caso 2: Necessario download prima dell'inizio cache
            if req_start < cache_start:
                missing_start = start_date
                missing_end = (cache_start - timedelta(days=1)).strftime('%Y-%m-%d')
                return cached_df, missing_start, missing_end
            
            # Caso 3: Necessario download dopo la fine cache
            if req_end > cache_end:
                missing_start = (cache_end + timedelta(days=1)).strftime('%Y-%m-%d')
                missing_end = end_date
                return cached_df, missing_start, missing_end
            
            # Altri casi: scarica tutto
            return None, start_date, end_date
            
        except Exception as e:
            self.log_error("Errore controllo cache", e)
            return None, start_date, end_date
    
    def _download_from_yahoo(self, symbol: str, start_date: str, 
                           end_date: str, interval: str = '1d') -> Dict[str, Any]:
        """Download diretto da Yahoo Finance (codice originale)"""
        try:
            self.log_info(f"Download Yahoo: {symbol} {start_date} -> {end_date}")
            
            last_error = None
            for attempt in range(self.max_retries):
                try:
                    ticker = yf.Ticker(symbol)
                    
                    data = ticker.history(
                        start=start_date,
                        end=end_date,
                        interval=interval,
                        timeout=self.timeout
                    )
                    
                    if not data.empty:
                        result = self._prepare_data_response(data, symbol)
                        self.log_info(f"✓ Download completato: {len(data)} record")
                        return result
                    
                    # Se vuoto, prova simboli alternativi
                    alternatives = self._get_symbol_alternatives(symbol)
                    for alt_symbol in alternatives[:3]:
                        try:
                            alt_ticker = yf.Ticker(alt_symbol)
                            alt_data = alt_ticker.history(
                                start=start_date,
                                end=end_date,
                                interval=interval,
                                timeout=self.timeout
                            )
                            if not alt_data.empty:
                                self.log_info(f"Successo con simbolo alternativo: {alt_symbol}")
                                return self._prepare_data_response(alt_data, alt_symbol)
                        except Exception:
                            continue
                    
                    raise ValueError(f"Nessun dato trovato per {symbol}")
                    
                except Exception as e:
                    last_error = e
                    if attempt < self.max_retries - 1:
                        time.sleep(2)
                        continue
                    else:
                        raise e
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'context': f"_download_from_yahoo({symbol})"
            }
    
    def _prepare_response_from_cache(self, df: pd.DataFrame, symbol: str,
                                   start_date: str, end_date: str) -> Dict[str, Any]:
        """Prepara risposta da dati cached"""
        try:
            # Filtra per periodo richiesto
            mask = (df['date'] >= start_date) & (df['date'] <= end_date)
            filtered_df = df[mask].copy()
            
            # Converti in formato risposta
            records = []
            for _, row in filtered_df.iterrows():
                record = {
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'open': round(float(row['open']), 2),
                    'high': round(float(row['high']), 2),
                    'low': round(float(row['low']), 2),
                    'close': round(float(row['close']), 2),
                    'volume': int(row['volume'])
                }
                
                # Aggiungi campi adjusted se presenti
                if 'adj_close' in row:
                    record['adj_close'] = round(float(row['adj_close']), 2)
                if 'adj_open' in row:
                    record['adj_open'] = round(float(row['adj_open']), 2)
                if 'adj_high' in row:
                    record['adj_high'] = round(float(row['adj_high']), 2)
                if 'adj_low' in row:
                    record['adj_low'] = round(float(row['adj_low']), 2)
                
                records.append(record)
            
            return {
                'success': True,
                'data': {
                    'symbol': symbol,
                    'records': records,
                    'count': len(records),
                    'first_date': records[0]['date'] if records else None,
                    'last_date': records[-1]['date'] if records else None,
                    'from_cache': True
                }
            }
            
        except Exception as e:
            self.log_error("Errore preparazione risposta da cache", e)
            raise
    
    def _prepare_data_response(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Prepara la risposta con i dati del DataFrame"""
        data_reset = data.reset_index()
        
        records = []
        for _, row in data_reset.iterrows():
            record = {
                'date': row['Date'].strftime('%Y-%m-%d'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume'])
            }
            
            # Aggiungi Adj Close se presente
            if 'Adj Close' in row:
                record['adj_close'] = round(float(row['Adj Close']), 2)
            
            records.append(record)
        
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
    
    def _get_symbol_alternatives(self, symbol: str) -> List[str]:
        """Genera simboli alternativi per il ticker"""
        alternatives = []
        
        common_mappings = {
            'META': ['FB'],
            'FB': ['META'],
            'GOOGL': ['GOOG'],
            'GOOG': ['GOOGL'],
            'BRK.A': ['BRK-A', 'BRKA'],
            'BRK.B': ['BRK-B', 'BRKB']
        }
        
        if symbol in common_mappings:
            alternatives.extend(common_mappings[symbol])
        
        if '.' in symbol:
            alternatives.append(symbol.replace('.', '-'))
        if '-' in symbol:
            alternatives.append(symbol.replace('-', '.'))
        
        return list(dict.fromkeys(alternatives))[:3]
    
    def get_multiple_stocks(self, symbols: List[str], start_date: str, 
                          end_date: str, adjusted: bool = True) -> Dict[str, Any]:
        """Recupera dati per multipli titoli"""
        try:
            results = {}
            errors = []
            
            for symbol in symbols:
                result = self.get_stock_data(
                    symbol, start_date, end_date, 
                    use_cache=True, adjusted=adjusted
                )
                
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
            
            if not info or len(info) < 5:
                raise ValueError(f"Informazioni non disponibili per {symbol}")
            
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
    
    def clear_cache(self, symbol: str, data_type: Optional[str] = None) -> Dict[str, Any]:
        """Cancella la cache per un simbolo"""
        try:
            success = self.file_manager.clear_data(symbol, data_type)
            
            if success:
                message = f"Cache cancellata per {symbol}"
                if data_type:
                    message += f" ({data_type})"
                
                return {
                    'success': True,
                    'message': message
                }
            else:
                return {
                    'success': False,
                    'error': 'Errore nella cancellazione della cache'
                }
                
        except Exception as e:
            return self.handle_error(e, f"clear_cache({symbol})")
    
    def test_connection(self) -> Dict[str, Any]:
        """Testa la connessione a Yahoo Finance"""
        try:
            self.log_info("=== TEST CONNESSIONE YAHOO FINANCE ===")
            
            ticker = yf.Ticker("AAPL")
            
            test_start = "2024-12-01"
            test_end = "2024-12-31"
            
            recent_data = ticker.history(
                start=test_start,
                end=test_end,
                timeout=self.timeout
            )
            
            if recent_data.empty:
                raise Exception("Impossibile recuperare dati di test")
            
            last_price = float(recent_data['Close'].iloc[-1])
            last_date = recent_data.index[-1].strftime('%Y-%m-%d')
            
            self.log_info("✓ CONNESSIONE YAHOO FINANCE OK")
            
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