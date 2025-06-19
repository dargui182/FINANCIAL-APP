"""
Servizio per processare e analizzare i dati
Principio SOLID: Single Responsibility - gestisce solo elaborazione dati
"""
import pandas as pd
import numpy as np
from flask import send_file
from io import BytesIO
from typing import Dict, Any, List
from datetime import datetime

from core.backend.base.base_service import BaseService


class DataProcessor(BaseService):
    """Processa e analizza i dati finanziari"""
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Valida i dati di input per il processing"""
        if 'records' not in data or not data['records']:
            raise ValueError("Nessun dato da processare")
        return True
    
    def basic_analysis(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue analisi statistiche di base sui dati"""
        try:
            records = stock_data['records']
            df = pd.DataFrame(records)
            
            # Converte date
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Calcola statistiche
            stats = {
                'symbol': stock_data['symbol'],
                'period': {
                    'start': stock_data['first_date'],
                    'end': stock_data['last_date'],
                    'days': len(records)
                },
                'price_stats': {
                    'min': float(df['close'].min()),
                    'max': float(df['close'].max()),
                    'mean': float(df['close'].mean()),
                    'std': float(df['close'].std()),
                    'current': float(df['close'].iloc[-1])
                },
                'volume_stats': {
                    'total': int(df['volume'].sum()),
                    'daily_avg': int(df['volume'].mean())
                },
                'returns': self._calculate_returns(df),
                'volatility': self._calculate_volatility(df),
                'trends': self._identify_trends(df)
            }
            
            return stats
            
        except Exception as e:
            self.log_error("Errore nell'analisi", e)
            raise
    
    def prepare_download(self, stock_data: Dict[str, Any], 
                        format_type: str = 'csv') -> Any:
        """Prepara i dati per il download"""
        try:
            records = stock_data['records']
            df = pd.DataFrame(records)
            
            # Aggiungi metadati
            df['symbol'] = stock_data['symbol']
            
            if format_type == 'csv':
                return self._prepare_csv(df, stock_data['symbol'])
            elif format_type == 'excel':
                return self._prepare_excel(df, stock_data['symbol'])
            else:
                raise ValueError(f"Formato non supportato: {format_type}")
                
        except Exception as e:
            self.log_error("Errore nella preparazione download", e)
            raise
    
    def _calculate_returns(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calcola i rendimenti"""
        df['daily_return'] = df['close'].pct_change()
        
        return {
            'daily_avg': float(df['daily_return'].mean() * 100),
            'total': float(((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100),
            'best_day': float(df['daily_return'].max() * 100),
            'worst_day': float(df['daily_return'].min() * 100)
        }
    
    def _calculate_volatility(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calcola la volatilità"""
        daily_returns = df['close'].pct_change()
        
        return {
            'daily': float(daily_returns.std() * 100),
            'annualized': float(daily_returns.std() * np.sqrt(252) * 100)
        }
    
    def _identify_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identifica trend di base"""
        # Media mobile semplice
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        current_price = df['close'].iloc[-1]
        
        trend = {
            'short_term': 'N/A',
            'medium_term': 'N/A'
        }
        
        # Trend breve termine
        if len(df) >= 20 and not pd.isna(df['sma_20'].iloc[-1]):
            if current_price > df['sma_20'].iloc[-1]:
                trend['short_term'] = 'Rialzista'
            else:
                trend['short_term'] = 'Ribassista'
        
        # Trend medio termine
        if len(df) >= 50 and not pd.isna(df['sma_50'].iloc[-1]):
            if current_price > df['sma_50'].iloc[-1]:
                trend['medium_term'] = 'Rialzista'
            else:
                trend['medium_term'] = 'Ribassista'
        
        return trend
    
    def _prepare_csv(self, df: pd.DataFrame, symbol: str) -> Any:
        """Prepara file CSV per download"""
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8')
        output.seek(0)
        
        filename = f"{symbol}_data_{datetime.now().strftime('%Y%m%d')}.csv"
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    
    def _prepare_excel(self, df: pd.DataFrame, symbol: str) -> Any:
        """Prepara file Excel per download"""
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Dati principali
            df.to_excel(writer, sheet_name='Dati', index=False)
            
            # Aggiungi foglio con statistiche
            stats_df = pd.DataFrame([
                ['Simbolo', symbol],
                ['Record totali', len(df)],
                ['Data inizio', df['date'].min()],
                ['Data fine', df['date'].max()],
                ['Prezzo minimo', df['close'].min()],
                ['Prezzo massimo', df['close'].max()],
                ['Prezzo medio', df['close'].mean()]
            ], columns=['Metrica', 'Valore'])
            
            stats_df.to_excel(writer, sheet_name='Statistiche', index=False)
        
        output.seek(0)
        filename = f"{symbol}_data_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )