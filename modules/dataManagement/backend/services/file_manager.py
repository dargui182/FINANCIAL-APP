"""
Servizio per la gestione del file system e cache dei dati
Principio SOLID: Single Responsibility - gestisce solo file system
"""
import os
import csv
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json

from core.backend.base.base_service import BaseService


class FileManagerService(BaseService):
    """Gestisce il salvataggio e recupero dei dati dal file system"""
    
    def __init__(self):
        super().__init__()
        self.base_path = Path("resources/data/price")
        self._ensure_directories()
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Valida i parametri di input"""
        required_fields = ['symbol', 'data_type']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo richiesto mancante: {field}")
        
        if data['data_type'] not in ['daily', 'dailyAdjusted', 'minute']:
            raise ValueError(f"Tipo dati non valido: {data['data_type']}")
        
        return True
    
    def _ensure_directories(self):
        """Crea le directory necessarie se non esistono"""
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def get_data_path(self, symbol: str, data_type: str) -> Path:
        """Restituisce il path per i dati di un simbolo"""
        return self.base_path / symbol / data_type
    
    def get_data_file(self, symbol: str, data_type: str) -> Path:
        """Restituisce il path del file CSV"""
        data_path = self.get_data_path(symbol, data_type)
        return data_path / f"{symbol}_{data_type}.csv"
    
    def get_metadata_file(self, symbol: str, data_type: str) -> Path:
        """Restituisce il path del file metadata"""
        data_path = self.get_data_path(symbol, data_type)
        return data_path / "metadata.json"
    
    def save_data(self, symbol: str, data_type: str, 
                  records: List[Dict], metadata: Optional[Dict] = None) -> bool:
        """Salva i dati su file CSV"""
        try:
            # Crea directory se non esiste
            data_path = self.get_data_path(symbol, data_type)
            data_path.mkdir(parents=True, exist_ok=True)
            
            # Path del file
            file_path = self.get_data_file(symbol, data_type)
            
            # Converti in DataFrame per gestione più semplice
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df.sort_values('date', inplace=True)
            
            # Salva CSV
            df.to_csv(file_path, index=False, date_format='%Y-%m-%d')
            
            # Salva metadata
            if metadata:
                metadata_path = self.get_metadata_file(symbol, data_type)
                metadata['last_update'] = datetime.now().isoformat()
                metadata['record_count'] = len(records)
                
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            self.log_info(f"Salvati {len(records)} record per {symbol}/{data_type}")
            return True
            
        except Exception as e:
            self.log_error(f"Errore salvataggio dati {symbol}/{data_type}", e)
            raise
    
    def load_data(self, symbol: str, data_type: str) -> Optional[pd.DataFrame]:
        """Carica i dati da file CSV"""
        try:
            file_path = self.get_data_file(symbol, data_type)
            
            if not file_path.exists():
                self.log_info(f"File non trovato: {file_path}")
                return None
            
            # Carica CSV
            df = pd.read_csv(file_path)
            df['date'] = pd.to_datetime(df['date'])
            
            self.log_info(f"Caricati {len(df)} record da {file_path}")
            return df
            
        except Exception as e:
            self.log_error(f"Errore caricamento dati {symbol}/{data_type}", e)
            return None
    
    def load_metadata(self, symbol: str, data_type: str) -> Optional[Dict]:
        """Carica metadata del file"""
        try:
            metadata_path = self.get_metadata_file(symbol, data_type)
            
            if not metadata_path.exists():
                return None
            
            with open(metadata_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.log_error(f"Errore caricamento metadata {symbol}/{data_type}", e)
            return None
    
    def get_last_date(self, symbol: str, data_type: str) -> Optional[str]:
        """Restituisce l'ultima data presente nei dati salvati"""
        try:
            df = self.load_data(symbol, data_type)
            if df is None or df.empty:
                return None
            
            last_date = df['date'].max()
            return last_date.strftime('%Y-%m-%d')
            
        except Exception as e:
            self.log_error(f"Errore recupero ultima data {symbol}/{data_type}", e)
            return None
    
    def append_data(self, symbol: str, data_type: str, 
                    new_records: List[Dict]) -> Tuple[bool, int]:
        """Aggiunge nuovi record ai dati esistenti"""
        try:
            # Carica dati esistenti
            existing_df = self.load_data(symbol, data_type)
            
            # Converti nuovi record in DataFrame
            new_df = pd.DataFrame(new_records)
            new_df['date'] = pd.to_datetime(new_df['date'])
            
            if existing_df is not None:
                # Combina con esistenti, rimuovendo duplicati
                combined_df = pd.concat([existing_df, new_df])
                combined_df.drop_duplicates(subset=['date'], keep='last', inplace=True)
                combined_df.sort_values('date', inplace=True)
                
                new_count = len(combined_df) - len(existing_df)
            else:
                combined_df = new_df
                new_count = len(new_df)
            
            # Salva dati combinati
            records = combined_df.to_dict('records')
            self.save_data(symbol, data_type, records)
            
            self.log_info(f"Aggiunti {new_count} nuovi record per {symbol}/{data_type}")
            return True, new_count
            
        except Exception as e:
            self.log_error(f"Errore append dati {symbol}/{data_type}", e)
            return False, 0
    
    def clear_data(self, symbol: str, data_type: Optional[str] = None) -> bool:
        """Cancella i dati salvati per un simbolo"""
        try:
            if data_type:
                # Cancella solo un tipo specifico
                file_path = self.get_data_file(symbol, data_type)
                metadata_path = self.get_metadata_file(symbol, data_type)
                
                if file_path.exists():
                    file_path.unlink()
                if metadata_path.exists():
                    metadata_path.unlink()
            else:
                # Cancella tutti i dati del simbolo
                symbol_path = self.base_path / symbol
                if symbol_path.exists():
                    import shutil
                    shutil.rmtree(symbol_path)
            
            self.log_info(f"Dati cancellati per {symbol}/{data_type or 'all'}")
            return True
            
        except Exception as e:
            self.log_error(f"Errore cancellazione dati {symbol}", e)
            return False
    
    def list_available_symbols(self) -> List[Dict[str, Any]]:
        """Elenca tutti i simboli con dati salvati"""
        try:
            symbols = []
            
            if not self.base_path.exists():
                return symbols
            
            for symbol_dir in self.base_path.iterdir():
                if symbol_dir.is_dir():
                    symbol_info = {
                        'symbol': symbol_dir.name,
                        'data_types': []
                    }
                    
                    # Controlla quali tipi di dati sono disponibili
                    for data_type in ['daily', 'dailyAdjusted', 'minute']:
                        file_path = self.get_data_file(symbol_dir.name, data_type)
                        if file_path.exists():
                            metadata = self.load_metadata(symbol_dir.name, data_type)
                            symbol_info['data_types'].append({
                                'type': data_type,
                                'last_update': metadata.get('last_update') if metadata else None,
                                'record_count': metadata.get('record_count') if metadata else 0
                            })
                    
                    if symbol_info['data_types']:
                        symbols.append(symbol_info)
            
            return symbols
            
        except Exception as e:
            self.log_error("Errore listing simboli", e)
            return []
    
    def get_data_stats(self, symbol: str, data_type: str) -> Optional[Dict]:
        """Restituisce statistiche sui dati salvati"""
        try:
            df = self.load_data(symbol, data_type)
            if df is None or df.empty:
                return None
            
            return {
                'symbol': symbol,
                'data_type': data_type,
                'record_count': len(df),
                'first_date': df['date'].min().strftime('%Y-%m-%d'),
                'last_date': df['date'].max().strftime('%Y-%m-%d'),
                'missing_dates': self._find_missing_dates(df),
                'file_size_kb': self.get_data_file(symbol, data_type).stat().st_size / 1024
            }
            
        except Exception as e:
            self.log_error(f"Errore calcolo statistiche {symbol}/{data_type}", e)
            return None
    
    def _find_missing_dates(self, df: pd.DataFrame) -> int:
        """Trova il numero di date mancanti nel dataset"""
        if df.empty:
            return 0
        
        # Crea range completo di date (escludendo weekend)
        date_range = pd.date_range(
            start=df['date'].min(),
            end=df['date'].max(),
            freq='B'  # Business days
        )
        
        # Conta date mancanti
        existing_dates = set(df['date'].dt.date)
        expected_dates = set(date_range.date)
        
        return len(expected_dates - existing_dates)