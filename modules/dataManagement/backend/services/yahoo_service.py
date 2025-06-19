"""
Servizio per interagire con Yahoo Finance
Principio SOLID: Single Responsibility - gestisce solo Yahoo Finance
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

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
        
        # Valida date
        try:
            start = datetime.strptime(data['start_date'], '%Y-%m-%d')
            end = datetime.strptime(data['end_date'], '%Y-%m-%d')
            
            if start > end:
                raise ValueError("La data di inizio deve essere prima della data di fine")
            
            if end > datetime.now():
                raise ValueError("La data di fine non può essere nel futuro")
                
        except ValueError as e:
            raise ValueError(f"Formato data non valido: {str(e)}")
        
        return True
    
    def get_stock_data(self, symbol: str, start_date: str, end_date: str, 
                      interval: str = '1d') -> Dict[str, Any]:
        """Recupera i dati storici di un titolo"""
        try:
            self.log_info(f"Recupero dati per {symbol} dal {start_date} al {end_date}")
            
            # Crea oggetto Ticker
            ticker = yf.Ticker(symbol)
            
            # Recupera dati storici
            data = ticker.history(
                start=start_date,
                end=end_date,
                interval=interval,
                timeout=self.timeout
            )
            
            if data.empty:
                raise ValueError(f"Nessun dato trovato per il simbolo {symbol}")
            
            # Prepara risposta
            result = self._prepare_data_response(data, symbol)
            
            self.log_info(f"Recuperati {len(data)} record per {symbol}")
            return result
            
        except Exception as e:
            return self.handle_error(e, f"get_stock_data({symbol})")
    
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
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Estrai informazioni principali
            return {
                'success': True,
                'data': {
                    'symbol': symbol,
                    'name': info.get('longName', symbol),
                    'sector': info.get('sector', 'N/A'),
                    'industry': info.get('industry', 'N/A'),
                    'currency': info.get('currency', 'USD'),
                    'exchange': info.get('exchange', 'N/A'),
                    'market_cap': info.get('marketCap', 0),
                    'current_price': info.get('currentPrice', 0)
                }
            }
            
        except Exception as e:
            return self.handle_error(e, f"get_stock_info({symbol})")
    
    def _prepare_data_response(self, data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
        """Prepara la risposta con i dati del DataFrame"""
        # Reset index per avere la data come colonna
        data_reset = data.reset_index()
        
        # Converti in formato JSON-friendly
        records = []
        for _, row in data_reset.iterrows():
            records.append({
                'date': row['Date'].strftime('%Y-%m-%d'),
                'open': round(row['Open'], 2),
                'high': round(row['High'], 2),
                'low': round(row['Low'], 2),
                'close': round(row['Close'], 2),
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