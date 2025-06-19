"""
API Routes per il modulo Data Management
"""
from flask import Blueprint, request, jsonify
import pandas as pd
from io import BytesIO
import json

from ..services.yahoo_service import YahooFinanceService
from ..services.data_processor import DataProcessor

# Crea blueprint per il modulo
data_management_bp = Blueprint('data_management', __name__)

# Inizializza servizi
yahoo_service = YahooFinanceService()
data_processor = DataProcessor()


@data_management_bp.route('/stock/data', methods=['POST'])
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


@data_management_bp.route('/stock/multiple', methods=['POST'])
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


@data_management_bp.route('/stock/info/<symbol>', methods=['GET'])
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


@data_management_bp.route('/stock/download', methods=['POST'])
def download_stock_data():
    """Endpoint per scaricare dati in formato CSV/Excel"""
    try:
        data = request.get_json()
        format_type = data.get('format', 'csv')
        
        # Recupera dati
        stock_result = yahoo_service.get_stock_data(
            symbol=data['symbol'],
            start_date=data['start_date'],
            end_date=data['end_date']
        )
        
        if not stock_result['success']:
            return jsonify(stock_result), 400
        
        # Processa per download
        file_data = data_processor.prepare_download(
            stock_result['data'],
            format_type
        )
        
        return file_data
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@data_management_bp.route('/stock/analysis', methods=['POST'])
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


@data_management_bp.route('/symbols/search', methods=['GET'])
def search_symbols():
    """Endpoint per cercare simboli (mock per ora)"""
    query = request.args.get('q', '')
    
    # Lista mock di simboli comuni
    symbols = [
        {'symbol': 'AAPL', 'name': 'Apple Inc.'},
        {'symbol': 'GOOGL', 'name': 'Alphabet Inc.'},
        {'symbol': 'MSFT', 'name': 'Microsoft Corporation'},
        {'symbol': 'AMZN', 'name': 'Amazon.com Inc.'},
        {'symbol': 'TSLA', 'name': 'Tesla, Inc.'},
        {'symbol': 'META', 'name': 'Meta Platforms Inc.'},
        {'symbol': 'NVDA', 'name': 'NVIDIA Corporation'},
        {'symbol': 'JPM', 'name': 'JPMorgan Chase & Co.'},
        {'symbol': 'V', 'name': 'Visa Inc.'},
        {'symbol': 'WMT', 'name': 'Walmart Inc.'}
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