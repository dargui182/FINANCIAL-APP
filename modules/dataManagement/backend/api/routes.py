"""
API Routes per il modulo Data Management - Enhanced Version
"""
from flask import Blueprint, request, jsonify
import pandas as pd
from io import BytesIO
import json

from ..services.yahoo_service import YahooFinanceService
from ..services.data_processor import DataProcessor
from ..services.file_manager import FileManagerService

# Crea blueprint per il modulo - NOME CORRETTO per module_loader
dataManagement_bp = Blueprint('dataManagement', __name__)

# Inizializza servizi
yahoo_service = YahooFinanceService()
data_processor = DataProcessor()
file_manager = FileManagerService()


@dataManagement_bp.route('/stock/data', methods=['POST'])
def get_stock_data():
    """Endpoint per recuperare dati di un singolo titolo (legacy)"""
    try:
        data = request.get_json()
        
        # Valida input
        yahoo_service.validate_input(data)
        
        # Recupera dati
        result = yahoo_service.get_stock_data(
            symbol=data['symbol'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            interval=data.get('interval', '1d')
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Errore interno del server'
        }), 500


@dataManagement_bp.route('/stock/data/v2', methods=['POST'])
def get_stock_data_v2():
    """
    Endpoint enhanced per recuperare dati con supporto cache e adjusted
    """
    try:
        data = request.get_json()
        
        # Parametri enhanced
        use_cache = data.get('use_cache', True)
        adjusted = data.get('adjusted', True)
        interval = data.get('interval', '1d')
        
        # Valida input base
        yahoo_service.validate_input(data)
        
        # Recupera dati con nuove opzioni
        result = yahoo_service.get_stock_data(
            symbol=data['symbol'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            interval=interval,
            use_cache=use_cache,
            adjusted=adjusted
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Errore interno del server'
        }), 500


@dataManagement_bp.route('/stock/history/full', methods=['POST'])
def get_full_history():
    """
    Endpoint per scaricare lo storico completo di un titolo
    """
    try:
        data = request.get_json()
        
        if 'symbol' not in data:
            raise ValueError("Simbolo richiesto")
        
        adjusted = data.get('adjusted', True)
        
        result = yahoo_service.get_full_history(
            symbol=data['symbol'],
            adjusted=adjusted
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Errore interno del server'
        }), 500


@dataManagement_bp.route('/stock/multiple', methods=['POST'])
def get_multiple_stocks():
    """Endpoint per recuperare dati di multipli titoli"""
    try:
        data = request.get_json()
        
        if 'symbols' not in data or not isinstance(data['symbols'], list):
            raise ValueError("Lista simboli richiesta")
        
        result = yahoo_service.get_multiple_stocks(
            symbols=data['symbols'],
            start_date=data['start_date'],
            end_date=data['end_date']
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Errore interno del server'
        }), 500


@dataManagement_bp.route('/stock/info/<symbol>', methods=['GET'])
def get_stock_info(symbol):
    """Endpoint per informazioni su un titolo"""
    try:
        result = yahoo_service.get_stock_info(symbol)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Errore nel recupero informazioni'
        }), 500


@dataManagement_bp.route('/stock/download', methods=['POST'])
def download_stock_data():
    """Endpoint per scaricare dati in formato CSV/Excel (legacy)"""
    try:
        data = request.get_json()
        
        # Validazione parametri
        required_fields = ['symbol', 'start_date', 'end_date', 'format']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'error': f"Campo richiesto mancante: {field}"
                }), 400
        
        format_type = data.get('format', 'csv').lower()
        if format_type not in ['csv', 'excel']:
            return jsonify({
                'success': False,
                'error': "Formato non supportato. Usa 'csv' o 'excel'"
            }), 400
        
        # Recupera dati
        stock_result = yahoo_service.get_stock_data(
            symbol=data['symbol'],
            start_date=data['start_date'],
            end_date=data['end_date']
        )
        
        if not stock_result['success']:
            return jsonify(stock_result), 400
        
        # Processa per download
        from flask import make_response
        import io
        
        if format_type == 'csv':
            # Genera CSV
            records = stock_result['data']['records']
            df = pd.DataFrame(records)
            
            # Crea CSV in memoria
            output = io.StringIO()
            df.to_csv(output, index=False)
            csv_data = output.getvalue()
            
            # Crea risposta
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = f'attachment; filename="{data["symbol"]}_data.csv"'
            
            return response
            
        elif format_type == 'excel':
            # Genera Excel
            records = stock_result['data']['records']
            df = pd.DataFrame(records)
            
            # Crea Excel in memoria
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Stock Data', index=False)
            
            excel_data = output.getvalue()
            
            # Crea risposta
            response = make_response(excel_data)
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Disposition'] = f'attachment; filename="{data["symbol"]}_data.xlsx"'
            
            return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Errore interno: {str(e)}"
        }), 500


@dataManagement_bp.route('/stock/download/v2', methods=['POST'])
def download_stock_data_v2():
    """
    Endpoint enhanced per download con opzioni adjusted/non-adjusted
    """
    try:
        data = request.get_json()
        
        # Validazione parametri
        required_fields = ['symbol', 'start_date', 'end_date', 'format']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f"Campo richiesto mancante: {field}"
                }), 400
        
        format_type = data.get('format', 'csv').lower()
        adjusted = data.get('adjusted', True)
        use_cache = data.get('use_cache', True)
        
        # Recupera dati
        stock_result = yahoo_service.get_stock_data(
            symbol=data['symbol'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            use_cache=use_cache,
            adjusted=adjusted
        )
        
        if not stock_result['success']:
            return jsonify(stock_result), 400
        
        # Prepara per download
        from flask import make_response
        import io
        
        records = stock_result['data']['records']
        df = pd.DataFrame(records)
        
        # Aggiungi metadati
        df['symbol'] = stock_result['data']['symbol']
        df['data_source'] = 'yahoo_finance'
        df['adjusted'] = adjusted
        
        if format_type == 'csv':
            # CSV
            output = io.StringIO()
            df.to_csv(output, index=False)
            csv_data = output.getvalue()
            
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = (
                f'attachment; filename="{data["symbol"]}_'
                f'{"adjusted" if adjusted else "regular"}_data.csv"'
            )
            
            return response
            
        elif format_type == 'excel':
            # Excel con più fogli
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Dati principali
                df.to_excel(writer, sheet_name='Price Data', index=False)
                
                # Statistiche
                stats_data = {
                    'Metric': ['Symbol', 'Records', 'Start Date', 'End Date',
                               'Data Type', 'From Cache'],
                    'Value': [
                        stock_result['data']['symbol'],
                        stock_result['data']['count'],
                        stock_result['data']['first_date'],
                        stock_result['data']['last_date'],
                        'Adjusted' if adjusted else 'Regular',
                        stock_result['data'].get('from_cache', False)
                    ]
                }
                stats_df = pd.DataFrame(stats_data)
                stats_df.to_excel(writer, sheet_name='Info', index=False)
                
                # Analisi se richiesta
                if data.get('include_analysis', False):
                    analysis = data_processor.basic_analysis(stock_result['data'])
                    
                    # Converti analisi in DataFrame
                    analysis_rows = []
                    for category, values in analysis.items():
                        if isinstance(values, dict):
                            for key, value in values.items():
                                analysis_rows.append({
                                    'Category': category,
                                    'Metric': key,
                                    'Value': value
                                })
                    
                    if analysis_rows:
                        analysis_df = pd.DataFrame(analysis_rows)
                        analysis_df.to_excel(writer, sheet_name='Analysis', index=False)
            
            excel_data = output.getvalue()
            
            response = make_response(excel_data)
            response.headers['Content-Type'] = (
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response.headers['Content-Disposition'] = (
                f'attachment; filename="{data["symbol"]}_'
                f'{"adjusted" if adjusted else "regular"}_data.xlsx"'
            )
            
            return response
            
        else:
            return jsonify({
                'success': False,
                'error': f"Formato non supportato: {format_type}"
            }), 400
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Errore interno: {str(e)}"
        }), 500


@dataManagement_bp.route('/stock/analysis', methods=['POST'])
def analyze_stock_data():
    """Endpoint per analisi base dei dati"""
    try:
        data = request.get_json()
        
        # Recupera dati
        stock_result = yahoo_service.get_stock_data(
            symbol=data['symbol'],
            start_date=data['start_date'],
            end_date=data['end_date']
        )
        
        if not stock_result['success']:
            return jsonify(stock_result), 400
        
        # Esegui analisi
        analysis = data_processor.basic_analysis(stock_result['data'])
        
        return jsonify({
            'success': True,
            'data': analysis
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dataManagement_bp.route('/cache/list', methods=['GET'])
def list_cached_symbols():
    """
    Endpoint per elencare tutti i simboli con dati in cache
    """
    try:
        symbols = file_manager.list_available_symbols()
        
        return jsonify({
            'success': True,
            'data': symbols,
            'count': len(symbols)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dataManagement_bp.route('/cache/stats/<symbol>', methods=['GET'])
def get_cache_stats(symbol):
    """
    Endpoint per ottenere statistiche sui dati cached di un simbolo
    """
    try:
        data_type = request.args.get('data_type', 'dailyAdjusted')
        
        stats = file_manager.get_data_stats(symbol, data_type)
        
        if stats:
            return jsonify({
                'success': True,
                'data': stats
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Nessun dato trovato in cache'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dataManagement_bp.route('/cache/clear/<symbol>', methods=['DELETE'])
def clear_symbol_cache(symbol):
    """
    Endpoint per cancellare la cache di un simbolo
    """
    try:
        data_type = request.args.get('data_type')  # Opzionale
        
        result = yahoo_service.clear_cache(symbol, data_type)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dataManagement_bp.route('/stock/validate/adjusted', methods=['POST'])
def validate_adjusted_data():
    """
    Endpoint per validare la qualità dei dati adjusted
    """
    try:
        data = request.get_json()
        
        if 'records' not in data:
            # Se non ci sono records, prova a caricare da un simbolo
            if 'symbol' in data and 'data_type' in data:
                df = file_manager.load_data(data['symbol'], data['data_type'])
                if df is not None:
                    records = df.to_dict('records')
                else:
                    raise ValueError("Nessun dato trovato")
            else:
                raise ValueError("Records o simbolo richiesti")
        else:
            records = data['records']
        
        from ..services.adjusted_data import AdjustedDataService
        adj_service = AdjustedDataService()
        
        validation = adj_service.validate_adjusted_data(records)
        
        return jsonify({
            'success': True,
            'data': validation
        })
        
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dataManagement_bp.route('/symbols/search', methods=['GET'])
def search_symbols():
    """Endpoint per cercare simboli (mock per ora)"""
    query = request.args.get('q', '')
    
    # Lista di simboli testati e affidabili
    symbols = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc. Class A'},
        {'symbol': 'GOOG', 'name': 'Alphabet Inc. Class C'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
        {'symbol': 'TSLA', 'name': 'Tesla, Inc.'},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.'},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corporation'},
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'},
        {'symbol': 'V', 'name': 'Visa Inc.'},
        {'symbol': 'JNJ', 'name': 'Johnson & Johnson'},
        {'symbol': 'WMT', 'name': 'Walmart Inc.'},
        {'symbol': 'PG', 'name': 'Procter & Gamble'},
        {'symbol': 'UNH', 'name': 'UnitedHealth Group'},
        {'symbol': 'HD', 'name': 'Home Depot'},
    ]
    
    # Filtra per query
    if query:
        filtered = [s for s in symbols 
                   if query.upper() in s['symbol'] or 
                   query.lower() in s['name'].lower()]
    else:
        filtered = symbols
    
    return jsonify({
        'success': True,
        'data': filtered[:10]  # Limita a 10 risultati
    })


@dataManagement_bp.route('/test/connection', methods=['GET'])
def test_connection():
    """Endpoint per testare la connessione a Yahoo Finance"""
    try:
        result = yahoo_service.test_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500