"""
Servizio per gestire dati a 1 minuto
Principio SOLID: Single Responsibility - gestisce solo dati intraday
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import pandas as pd
import time

from core.backend.base.base_service import BaseService
from core.backend.config.settings import YAHOO_API_TIMEOUT, YAHOO_MAX_RETRIES
from modules.dataManagement.backend.services.file_manager import FileManagerService


class MinuteDataService(BaseService):
    """Servizio specializzato per dati a 1 minuto"""
    
    def __init__(self):
        super().__init__()
        self.timeout = YAHOO_API_TIMEOUT
        self.max_retries = YAHOO_MAX_RETRIES
        self.file_manager = FileManagerService()
        self.max_days_per_request = 7  # Yahoo limita i dati minuto a 7 giorni
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Valida i parametri di input per dati minuto"""
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
            
            # Yahoo Finance limita i dati a 1 minuto a 30 giorni
            max_period = timedelta(days=30)
            if (end - start) > max_period:
                raise ValueError("I dati a 1 minuto sono disponibili solo per gli ultimi 30 giorni")
            
            # Verifica che non sia troppo nel passato
            days_ago = (datetime.now() - start).days
            if days_ago > 30:
                raise ValueError("I dati a 1 minuto non sono disponibili per date oltre 30 giorni fa")
                
        except ValueError as e:
            if "time data" in str(e):
                raise ValueError("Formato data non valido. Usa YYYY-MM-DD")
            raise e
            
        return True
    
    def get_minute_data(self, symbol: str, start_date: str, end_date: str,
                       use_cache: bool = True) -> Dict[str, Any]:
        """
        Recupera dati a 1 minuto con supporto cache
        """
        try:
            symbol = str(symbol).strip().upper()
            self.log_info(f"Recupero dati minuto per {symbol}: {start_date} -> {end_date}")
            
            # Valida input
            self.validate_input({
                'symbol': symbol,
                'start_date': start_date,
                'end_date': end_date
            })
            
            data_type = 'minute'
            
            # Controlla cache se abilitata
            if use_cache:
                cached_data, missing_periods = self._check_minute_cache(
                    symbol, start_date, end_date
                )
                
                if cached_data is not None and not missing_periods:
                    self.log_info("Tutti i dati minuto richiesti sono in cache")
                    return self._prepare_response_from_cache(
                        cached_data, symbol, start_date, end_date
                    )
                
                # Download incrementale per periodi mancanti
                if missing_periods:
                    all_new_records = []
                    
                    for period_start, period_end in missing_periods:
                        self.log_info(f"Download periodo mancante: {period_start} -> {period_end}")
                        new_data = self._download_minute_data(
                            symbol, period_start, period_end
                        )
                        
                        if new_data['success']:
                            all_new_records.extend(new_data['data']['records'])
                    
                    if all_new_records:
                        # Aggiungi nuovi dati alla cache
                        self.file_manager.append_data(symbol, data_type, all_new_records)
                        
                        # Ricarica tutti i dati
                        all_data = self.file_manager.load_data(symbol, data_type)
                        return self._prepare_response_from_cache(
                            all_data, symbol, start_date, end_date
                        )
            
            # Download completo
            return self._download_minute_data(symbol, start_date, end_date)
            
        except Exception as e:
            return self.handle_error(e, f"get_minute_data({symbol})")
    
    def _download_minute_data(self, symbol: str, start_date: str, 
                            end_date: str) -> Dict[str, Any]:
        """
        Download dati minuto da Yahoo Finance
        Gestisce il limite di 7 giorni per richiesta
        """
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Dividi in chunks di max 7 giorni
            all_records = []
            current_start = start_dt
            
            while current_start <= end_dt:
                current_end = min(
                    current_start + timedelta(days=self.max_days_per_request - 1),
                    end_dt
                )
                
                self.log_info(f"Download chunk: {current_start.strftime('%Y-%m-%d')} -> "
                             f"{current_end.strftime('%Y-%m-%d')}")
                
                # Download chunk
                for attempt in range(self.max_retries):
                    try:
                        ticker = yf.Ticker(symbol)
                        
                        # Aggiungi un giorno alla fine per includere l'ultimo giorno
                        chunk_end = current_end + timedelta(days=1)
                        
                        data = ticker.history(
                            start=current_start.strftime('%Y-%m-%d'),
                            end=chunk_end.strftime('%Y-%m-%d'),
                            interval='1m',
                            timeout=self.timeout
                        )
                        
                        if not data.empty:
                            records = self._convert_to_records(data, symbol)
                            all_records.extend(records)
                            break
                        
                    except Exception as e:
                        if attempt < self.max_retries - 1:
                            time.sleep(2)
                            continue
                        raise e
                
                # Prossimo chunk
                current_start = current_end + timedelta(days=1)
                
                # Pausa tra chunks per evitare rate limiting
                if current_start <= end_dt:
                    time.sleep(1)
            
            if not all_records:
                raise ValueError(f"Nessun dato minuto trovato per {symbol}")
            
            # Salva in cache
            self.file_manager.save_data(
                symbol, 'minute', all_records,
                metadata={
                    'source': 'yahoo_finance',
                    'interval': '1m',
                    'download_date': datetime.now().isoformat()
                }
            )
            
            return {
                'success': True,
                'data': {
                    'symbol': symbol,
                    'records': all_records,
                    'count': len(all_records),
                    'first_date': all_records[0]['datetime'] if all_records else None,
                    'last_date': all_records[-1]['datetime'] if all_records else None,
                    'interval': '1m'
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'context': f"_download_minute_data({symbol})"
            }
    
    def _convert_to_records(self, df: pd.DataFrame, symbol: str) -> List[Dict]:
        """Converte DataFrame in lista di record per dati minuto"""
        records = []
        
        for idx, row in df.reset_index().iterrows():
            # Per dati minuto includiamo anche l'orario
            records.append({
                'datetime': row['Date'].strftime('%Y-%m-%d %H:%M:%S'),
                'date': row['Date'].strftime('%Y-%m-%d'),
                'time': row['Date'].strftime('%H:%M:%S'),
                'open': round(float(row['Open']), 2),
                'high': round(float(row['High']), 2),
                'low': round(float(row['Low']), 2),
                'close': round(float(row['Close']), 2),
                'volume': int(row['Volume']),
                'symbol': symbol
            })
        
        return records
    
    def _check_minute_cache(self, symbol: str, start_date: str, 
                          end_date: str) -> Tuple[Optional[pd.DataFrame], List[Tuple[str, str]]]:
        """
        Controlla cache per dati minuto e identifica periodi mancanti
        """
        try:
            cached_df = self.file_manager.load_data(symbol, 'minute')
            
            if cached_df is None or cached_df.empty:
                return None, [(start_date, end_date)]
            
            # Converti colonna datetime se è stringa
            if 'datetime' in cached_df.columns:
                cached_df['datetime'] = pd.to_datetime(cached_df['datetime'])
            
            # Identifica periodi mancanti
            req_start = pd.to_datetime(start_date)
            req_end = pd.to_datetime(end_date)
            
            # Trova date con dati in cache
            cached_dates = set(cached_df['date'].unique())
            
            # Genera tutte le date richieste (escludendo weekend)
            date_range = pd.date_range(start=req_start, end=req_end, freq='B')
            required_dates = set(date_range.strftime('%Y-%m-%d'))
            
            # Trova date mancanti
            missing_dates = required_dates - cached_dates
            
            if not missing_dates:
                return cached_df, []
            
            # Raggruppa date mancanti in periodi continui
            missing_periods = self._group_missing_dates(sorted(missing_dates))
            
            return cached_df, missing_periods
            
        except Exception as e:
            self.log_error("Errore controllo cache minuti", e)
            return None, [(start_date, end_date)]
    
    def _group_missing_dates(self, missing_dates: List[str]) -> List[Tuple[str, str]]:
        """Raggruppa date mancanti in periodi continui"""
        if not missing_dates:
            return []
        
        periods = []
        start = missing_dates[0]
        end = missing_dates[0]
        
        for i in range(1, len(missing_dates)):
            current = datetime.strptime(missing_dates[i], '%Y-%m-%d')
            previous = datetime.strptime(missing_dates[i-1], '%Y-%m-%d')
            
            # Se la differenza è maggiore di 3 giorni (weekend + 1), nuovo periodo
            if (current - previous).days > 3:
                periods.append((start, end))
                start = missing_dates[i]
            
            end = missing_dates[i]
        
        periods.append((start, end))
        return periods
    
    def _prepare_response_from_cache(self, df: pd.DataFrame, symbol: str,
                                   start_date: str, end_date: str) -> Dict[str, Any]:
        """Prepara risposta da dati cached per minuti"""
        try:
            # Filtra per periodo richiesto
            mask = (df['date'] >= start_date) & (df['date'] <= end_date)
            filtered_df = df[mask].copy()
            
            # Ordina per datetime
            if 'datetime' in filtered_df.columns:
                filtered_df.sort_values('datetime', inplace=True)
            
            # Converti in records
            records = filtered_df.to_dict('records')
            
            return {
                'success': True,
                'data': {
                    'symbol': symbol,
                    'records': records,
                    'count': len(records),
                    'first_date': records[0]['datetime'] if records else None,
                    'last_date': records[-1]['datetime'] if records else None,
                    'interval': '1m',
                    'from_cache': True
                }
            }
            
        except Exception as e:
            self.log_error("Errore preparazione risposta cache minuti", e)
            raise
    
    def aggregate_to_timeframe(self, minute_data: List[Dict], 
                             timeframe: str = '5m') -> List[Dict]:
        """
        Aggrega dati minuto in timeframe maggiori (5m, 15m, 30m, 1h)
        """
        try:
            if not minute_data:
                return []
            
            # Converti in DataFrame
            df = pd.DataFrame(minute_data)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            
            # Mappa timeframe a frequenza pandas
            freq_map = {
                '5m': '5T',
                '15m': '15T',
                '30m': '30T',
                '1h': '1H',
                '4h': '4H'
            }
            
            if timeframe not in freq_map:
                raise ValueError(f"Timeframe non supportato: {timeframe}")
            
            # Aggrega OHLCV
            agg_rules = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }
            
            # Resample
            resampled = df.resample(freq_map[timeframe]).agg(agg_rules)
            
            # Rimuovi righe con NaN
            resampled.dropna(inplace=True)
            
            # Converti back in records
            records = []
            for idx, row in resampled.reset_index().iterrows():
                records.append({
                    'datetime': idx.strftime('%Y-%m-%d %H:%M:%S'),
                    'date': idx.strftime('%Y-%m-%d'),
                    'time': idx.strftime('%H:%M:%S'),
                    'open': round(row['open'], 2),
                    'high': round(row['high'], 2),
                    'low': round(row['low'], 2),
                    'close': round(row['close'], 2),
                    'volume': int(row['volume']),
                    'timeframe': timeframe
                })
            
            return records
            
        except Exception as e:
            self.log_error(f"Errore aggregazione a {timeframe}", e)
            raise
    
    def get_market_hours_data(self, symbol: str, date: str) -> Dict[str, Any]:
        """
        Recupera solo dati durante ore di mercato (9:30-16:00 ET)
        """
        try:
            # Recupera tutti i dati del giorno
            result = self.get_minute_data(symbol, date, date)
            
            if not result['success']:
                return result
            
            # Filtra per ore di mercato
            market_records = []
            for record in result['data']['records']:
                time = record['time']
                # Assumendo ore ET, filtra 9:30-16:00
                if '09:30:00' <= time <= '16:00:00':
                    market_records.append(record)
            
            result['data']['records'] = market_records
            result['data']['count'] = len(market_records)
            result['data']['market_hours_only'] = True
            
            return result
            
        except Exception as e:
            return self.handle_error(e, f"get_market_hours_data({symbol})")