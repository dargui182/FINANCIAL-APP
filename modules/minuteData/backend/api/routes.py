"""
API Routes per il modulo Minute Data
"""
from flask import Blueprint, request, jsonify
import pandas as pd
from datetime import datetime, timedelta

from ..services.minute_data_service import MinuteDataService
from modules.dataManagement.backend.services.file_manager import FileManagerService

# Crea blueprint per il modulo
minuteData_bp = Blueprint('minuteData', __name__)

# Inizializza servizi
minute_service = MinuteDataService()
file_manager = FileManagerService()


@minuteData_bp.route('/data/1m', methods=['POST'])
def get_minute_data():
    """Endpoint per recuperare dati a 1 minuto"""
    try:
        data = request.get_json()
        
        # Parametri
        use_cache = data.get('use_cache', True)
        
        # Recupera dati
        result = minute_service.get_minute_data(
            symbol=data['symbol'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            use_cache=use_cache
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
            'error': 'Errore interno del server',
            'details': str(e)
        }), 500


@minuteData_bp.route('/data/aggregate', methods=['POST'])
def aggregate_minute_data():
    """Endpoint per aggregare dati minuto in timeframe maggiori"""
    try:
        data = request.get_json()
        
        # Validazione
        if 'records' not in data or 'timeframe' not in data:
            raise ValueError("Records e timeframe richiesti")
        
        # Aggrega
        aggregated = minute_service.aggregate_to_timeframe(
            data['records'],
            data['timeframe']
        )
        
        return jsonify({
            'success': True,
            'data': {
                'records': aggregated,
                'count': len(aggregated),
                'timeframe': data['timeframe'],
                'original_count': len(data['records'])
            }
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


@minuteData_bp.route('/data/market-hours', methods=['POST'])
def get_market_hours_data():
    """Endpoint per dati solo durante ore di mercato"""
    try:
        data = request.get_json()
        
        if 'symbol' not in data or 'date' not in data:
            raise ValueError("Symbol e date richiesti")
        
        result = minute_service.get_market_hours_data(
            data['symbol'],
            data['date']
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
            'error': str(e)
        }), 500


@minuteData_bp.route('/data/today/<symbol>', methods=['GET'])
def get_today_data(symbol):
    """Endpoint per dati di oggi"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        
        result = minute_service.get_minute_data(
            symbol=symbol,
            start_date=today,
            end_date=today,
            use_cache=True
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@minuteData_bp.route('/data/last-week/<symbol>', methods=['GET'])
def get_last_week_data(symbol):
    """Endpoint per dati ultima settimana"""
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        result = minute_service.get_minute_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            use_cache=True
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@minuteData_bp.route('/download', methods=['POST'])
def download_minute_data():
    """Endpoint per scaricare dati minuto"""
    try:
        data = request.get_json()
        
        # Validazione
        required = ['symbol', 'start_date', 'end_date', 'format']
        for field in required:
            if field not in data:
                raise ValueError(f"Campo richiesto: {field}")
        
        format_type = data['format'].lower()
        timeframe = data.get('timeframe', '1m')
        
        # Recupera dati
        result = minute_service.get_minute_data(
            symbol=data['symbol'],
            start_date=data['start_date'],
            end_date=data['end_date'],
            use_cache=True
        )
        
        if not result['success']:
            return jsonify(result), 400
        
        records = result['data']['records']
        
        # Se richiesto timeframe diverso, aggrega
        if timeframe != '1m':
            records = minute_service.aggregate_to_timeframe(records, timeframe)
        
        # Prepara download
        from flask import make_response
        import io
        
        df = pd.DataFrame(records)
        
        if format_type == 'csv':
            output = io.StringIO()
            df.to_csv(output, index=False)
            csv_data = output.getvalue()
            
            response = make_response(csv_data)
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = (
                f'attachment; filename="{data["symbol"]}_'
                f'{timeframe}_minute_data.csv"'
            )
            
            return response
            
        elif format_type == 'excel':
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Dati principali
                df.to_excel(writer, sheet_name=f'{timeframe} Data', index=False)
                
                # Info
                info_data = {
                    'Metric': ['Symbol', 'Timeframe', 'Records', 'Period'],
                    'Value': [
                        data['symbol'],
                        timeframe,
                        len(records),
                        f"{data['start_date']} to {data['end_date']}"
                    ]
                }
                info_df = pd.DataFrame(info_data)
                info_df.to_excel(writer, sheet_name='Info', index=False)
            
            excel_data = output.getvalue()
            
            response = make_response(excel_data)
            response.headers['Content-Type'] = (
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response.headers['Content-Disposition'] = (
                f'attachment; filename="{data["symbol"]}_'
                f'{timeframe}_minute_data.xlsx"'
            )
            
            return response
        
        else:
            raise ValueError(f"Formato non supportato: {format_type}")
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@minuteData_bp.route('/stats/<symbol>', methods=['GET'])
def get_minute_stats(symbol):
    """Statistiche sui dati minuto cached"""
    try:
        stats = file_manager.get_data_stats(symbol, 'minute')
        
        if stats:
            # Aggiungi info specifiche per dati minuto
            df = file_manager.load_data(symbol, 'minute')
            if df is not None and not df.empty:
                # Conta giorni unici
                unique_dates = df['date'].nunique()
                stats['unique_trading_days'] = unique_dates
                
                # Media record per giorno
                stats['avg_records_per_day'] = len(df) // unique_dates if unique_dates > 0 else 0
            
            return jsonify({
                'success': True,
                'data': stats
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Nessun dato minuto trovato'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@minuteData_bp.route('/cache/clear/<symbol>', methods=['DELETE'])
def clear_minute_cache(symbol):
    """Cancella cache dati minuto"""
    try:
        success = file_manager.clear_data(symbol, 'minute')
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Cache minuti cancellata per {symbol}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Errore cancellazione cache'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500