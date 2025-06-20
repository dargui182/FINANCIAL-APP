"""
Servizio per il calcolo dei prezzi adjusted
Principio SOLID: Single Responsibility - gestisce solo calcoli adjusted
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime

from core.backend.base.base_service import BaseService


class AdjustedDataService(BaseService):
    """Gestisce il calcolo dei prezzi adjusted per coerenza OHLC"""
    
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Valida i parametri di input"""
        required_fields = ['records', 'has_adjusted']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Campo richiesto mancante: {field}")
        return True
    
    def calculate_adjusted_prices(self, records: List[Dict], 
                                has_adjusted: bool = True) -> List[Dict]:
        """
        Calcola i prezzi adjusted per tutti i campi OHLC
        Se has_adjusted è True, usa l'Adj Close esistente
        Se è False, copia Close in Adj Close
        """
        try:
            if not records:
                return records
            
            # Converti in DataFrame per calcoli più efficienti
            df = pd.DataFrame(records)
            
            # Se non ci sono dati adjusted, usa Close come Adj Close
            if not has_adjusted or 'adj_close' not in df.columns:
                df['adj_close'] = df['close']
                self.log_info("Nessun dato adjusted disponibile, uso Close come Adj Close")
            
            # Calcola il fattore di aggiustamento
            df = self._calculate_adjustment_factor(df)
            
            # Applica l'aggiustamento a tutti i prezzi
            df = self._apply_adjustment(df)
            
            # Converti back in lista di dizionari
            adjusted_records = df.to_dict('records')
            
            self.log_info(f"Calcolati prezzi adjusted per {len(adjusted_records)} record")
            return adjusted_records
            
        except Exception as e:
            self.log_error("Errore nel calcolo prezzi adjusted", e)
            raise
    
    def _calculate_adjustment_factor(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcola il fattore di aggiustamento per ogni giorno
        Fattore = Adj Close / Close
        """
        try:
            # Evita divisione per zero
            df['adjustment_factor'] = np.where(
                df['close'] != 0,
                df['adj_close'] / df['close'],
                1.0
            )
            
            # Gestisci valori NaN o infiniti
            df['adjustment_factor'].fillna(1.0, inplace=True)
            df['adjustment_factor'] = df['adjustment_factor'].replace([np.inf, -np.inf], 1.0)
            
            return df
            
        except Exception as e:
            self.log_error("Errore calcolo fattore aggiustamento", e)
            raise
    
    def _apply_adjustment(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applica il fattore di aggiustamento a Open, High, Low
        per mantenere la coerenza con Adj Close
        """
        try:
            # Applica aggiustamento
            df['adj_open'] = df['open'] * df['adjustment_factor']
            df['adj_high'] = df['high'] * df['adjustment_factor']
            df['adj_low'] = df['low'] * df['adjustment_factor']
            
            # Verifica coerenza: high >= low, high >= open, high >= close
            df = self._ensure_price_consistency(df)
            
            # Rimuovi colonna temporanea
            df.drop('adjustment_factor', axis=1, inplace=True)
            
            return df
            
        except Exception as e:
            self.log_error("Errore applicazione aggiustamento", e)
            raise
    
    def _ensure_price_consistency(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assicura che i prezzi adjusted siano coerenti:
        - High deve essere il massimo tra Open, High, Low, Close
        - Low deve essere il minimo tra Open, High, Low, Close
        """
        try:
            # Calcola min e max per ogni riga
            price_cols = ['adj_open', 'adj_high', 'adj_low', 'adj_close']
            
            # Correggi high e low se necessario
            df['adj_high'] = df[price_cols].max(axis=1)
            df['adj_low'] = df[price_cols].min(axis=1)
            
            # Log eventuali correzioni significative
            corrections = ((df['adj_high'] != df['high'] * df['adjustment_factor']) | 
                         (df['adj_low'] != df['low'] * df['adjustment_factor'])).sum()
            
            if corrections > 0:
                self.log_info(f"Applicate {corrections} correzioni per coerenza prezzi")
            
            return df
            
        except Exception as e:
            self.log_error("Errore verifica coerenza prezzi", e)
            raise
    
    def validate_adjusted_data(self, records: List[Dict]) -> Dict[str, Any]:
        """
        Valida la qualità dei dati adjusted
        """
        try:
            df = pd.DataFrame(records)
            
            validation_results = {
                'is_valid': True,
                'issues': [],
                'statistics': {}
            }
            
            # Controlla presenza colonne necessarie
            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            adjusted_cols = ['adj_open', 'adj_high', 'adj_low', 'adj_close']
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                validation_results['is_valid'] = False
                validation_results['issues'].append(f"Colonne mancanti: {missing_cols}")
            
            # Controlla coerenza prezzi
            if all(col in df.columns for col in adjusted_cols):
                # High deve essere >= di tutti gli altri prezzi
                invalid_high = df[
                    (df['adj_high'] < df['adj_open']) |
                    (df['adj_high'] < df['adj_close']) |
                    (df['adj_high'] < df['adj_low'])
                ]
                
                if not invalid_high.empty:
                    validation_results['is_valid'] = False
                    validation_results['issues'].append(
                        f"High non valido in {len(invalid_high)} record"
                    )
                
                # Low deve essere <= di tutti gli altri prezzi
                invalid_low = df[
                    (df['adj_low'] > df['adj_open']) |
                    (df['adj_low'] > df['adj_close']) |
                    (df['adj_low'] > df['adj_high'])
                ]
                
                if not invalid_low.empty:
                    validation_results['is_valid'] = False
                    validation_results['issues'].append(
                        f"Low non valido in {len(invalid_low)} record"
                    )
            
            # Calcola statistiche
            if 'adj_close' in df.columns and 'close' in df.columns:
                adjustment_factors = df['adj_close'] / df['close']
                validation_results['statistics'] = {
                    'min_adjustment': float(adjustment_factors.min()),
                    'max_adjustment': float(adjustment_factors.max()),
                    'mean_adjustment': float(adjustment_factors.mean()),
                    'records_with_adjustment': int((adjustment_factors != 1.0).sum())
                }
            
            return validation_results
            
        except Exception as e:
            self.log_error("Errore validazione dati adjusted", e)
            return {
                'is_valid': False,
                'issues': [str(e)],
                'statistics': {}
            }
    
    def compare_adjusted_vs_regular(self, records: List[Dict]) -> Dict[str, Any]:
        """
        Confronta prezzi regular vs adjusted per analisi
        """
        try:
            df = pd.DataFrame(records)
            
            comparison = {
                'has_adjustments': False,
                'adjustment_dates': [],
                'max_adjustment_pct': 0.0,
                'total_return_regular': 0.0,
                'total_return_adjusted': 0.0
            }
            
            if 'adj_close' not in df.columns or 'close' not in df.columns:
                return comparison
            
            # Identifica date con aggiustamenti
            df['has_adjustment'] = (df['adj_close'] != df['close'])
            adjustment_dates = df[df['has_adjustment']]['date'].tolist()
            
            if adjustment_dates:
                comparison['has_adjustments'] = True
                comparison['adjustment_dates'] = adjustment_dates
                
                # Calcola massimo aggiustamento percentuale
                df['adjustment_pct'] = abs(
                    (df['adj_close'] - df['close']) / df['close']
                ) * 100
                comparison['max_adjustment_pct'] = float(df['adjustment_pct'].max())
                
                # Calcola return totale con e senza aggiustamenti
                if len(df) > 1:
                    comparison['total_return_regular'] = float(
                        ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
                    )
                    comparison['total_return_adjusted'] = float(
                        ((df['adj_close'].iloc[-1] / df['adj_close'].iloc[0]) - 1) * 100
                    )
            
            return comparison
            
        except Exception as e:
            self.log_error("Errore confronto adjusted vs regular", e)
            raise