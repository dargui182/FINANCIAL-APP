"""
API Routes per il modulo Data Management
"""
from flask import Blueprint, request, jsonify
import pandas as pd
from io import BytesIO
import json

from ..services.yahoo_service import YahooFinanceService
from ..services.data_processor import DataProcessor

# Crea blueprint per il modulo - NOME CORRETTO per module_loader
dataManagement_bp = Blueprint('dataManagement', __name__)

# Inizializza servizi
yahoo_service = YahooFinanceService()
data_processor = DataProcessor()


@dataManagement_bp.route('/stock/data', methods=['POST'])
def get_stock_data():
    """Endpoint per recuperare dati di un singolo titolo"""
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
    """Endpoint per scaricare dati in formato CSV/Excel"""
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
            import pandas as pd
            
            # Converte i record in DataFrame
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
            import pandas as pd
            
            # Converte i record in DataFrame
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


@dataManagement_bp.route('/debug/symbol/<symbol>', methods=['GET'])
def debug_symbol(symbol):
    """Endpoint di debug per verificare un simbolo"""
    try:
        # Test info simbolo
        info_result = yahoo_service.get_stock_info(symbol)
        
        # Test dati recenti (2024)
        data_result = yahoo_service.get_stock_data(
            symbol=symbol,
            start_date='2024-12-01',
            end_date='2024-12-31'
        )
        
        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'info_available': info_result['success'],
                'info_error': info_result.get('error') if not info_result['success'] else None,
                'data_available': data_result['success'],
                'data_error': data_result.get('error') if not data_result['success'] else None,
                'recent_data_count': len(data_result.get('data', {}).get('records', [])) if data_result['success'] else 0
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dataManagement_bp.route('/test/quick/<symbol>', methods=['GET'])
def quick_test_symbol(symbol):
    """Test veloce per un simbolo con periodo fisso"""
    try:
        result = yahoo_service.get_stock_data(
            symbol=symbol,
            start_date='2024-01-01',
            end_date='2024-12-31'
        )
        
        if result['success']:
            data = result['data']
            return jsonify({
                'success': True,
                'data': {
                    'symbol': data['symbol'],
                    'records_count': data['count'],
                    'period': f"{data['first_date']} to {data['last_date']}",
                    'sample_prices': {
                        'first': data['records'][0] if data['records'] else None,
                        'last': data['records'][-1] if data['records'] else None
                    }
                }
            })
        else:
            return jsonify(result), 400
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@dataManagement_bp.route('/test/raw/<symbol>', methods=['GET'])
def raw_test_symbol(symbol):
    """Test RAW diretto con yfinance - bypass dei nostri servizi"""
    try:
        import yfinance as yf
        from datetime import datetime
        
        # Test molto basilare
        ticker = yf.Ticker(symbol)
        
        # Test 1: Info
        try:
            info = ticker.info
            info_success = bool(info and len(info) > 3)
            info_keys = list(info.keys())[:10] if info else []
        except Exception as e:
            info_success = False
            info_keys = []
            info_error = str(e)
        
        # Test 2: History con periodo molto piccolo
        try:
            # Prova con un periodo molto recente e piccolo
            hist_1d = ticker.history(period="1d")
            hist_1d_success = not hist_1d.empty
            hist_1d_len = len(hist_1d)
        except Exception as e:
            hist_1d_success = False
            hist_1d_len = 0
            hist_1d_error = str(e)
        
        # Test 3: History con date specifiche
        try:
            hist_range = ticker.history(start="2024-12-01", end="2024-12-31")
            hist_range_success = not hist_range.empty
            hist_range_len = len(hist_range)
        except Exception as e:
            hist_range_success = False
            hist_range_len = 0
            hist_range_error = str(e)
        
        # Test 4: History con periodo predefinito
        try:
            hist_1mo = ticker.history(period="1mo")
            hist_1mo_success = not hist_1mo.empty
            hist_1mo_len = len(hist_1mo)
        except Exception as e:
            hist_1mo_success = False
            hist_1mo_len = 0
            hist_1mo_error = str(e)
        
        return jsonify({
            'success': True,
            'data': {
                'symbol': symbol,
                'yfinance_version': yf.__version__,
                'tests': {
                    'info': {
                        'success': info_success,
                        'keys_sample': info_keys,
                        'error': locals().get('info_error')
                    },
                    'history_1d': {
                        'success': hist_1d_success,
                        'records': hist_1d_len,
                        'error': locals().get('hist_1d_error')
                    },
                    'history_range': {
                        'success': hist_range_success,
                        'records': hist_range_len,
                        'error': locals().get('hist_range_error')
                    },
                    'history_1mo': {
                        'success': hist_1mo_success,
                        'records': hist_1mo_len,
                        'error': locals().get('hist_1mo_error')
                    }
                }
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f"Test RAW fallito: {str(e)}"
        }), 500