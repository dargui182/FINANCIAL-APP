"""
Test per YahooFinanceService
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from modules.dataManagement.backend.services.yahoo_service import YahooFinanceService


class TestYahooFinanceService:
    """Test suite per YahooFinanceService"""
    
    @pytest.fixture
    def service(self):
        """Fixture per creare istanza del servizio"""
        return YahooFinanceService()
    
    @pytest.fixture
    def valid_params(self):
        """Parametri validi di test"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        return {
            'symbol': 'AAPL',
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        }
    
    def test_validate_input_valid(self, service, valid_params):
        """Test validazione con parametri validi"""
        assert service.validate_input(valid_params) is True
    
    def test_validate_input_missing_field(self, service):
        """Test validazione con campo mancante"""
        params = {'symbol': 'AAPL', 'start_date': '2024-01-01'}
        
        with pytest.raises(ValueError) as exc_info:
            service.validate_input(params)
        
        assert "Campo richiesto mancante: end_date" in str(exc_info.value)
    
    def test_validate_input_invalid_date_format(self, service):
        """Test validazione con formato data non valido"""
        params = {
            'symbol': 'AAPL',
            'start_date': '01/01/2024',  # Formato errato
            'end_date': '2024-12-31'
        }
        
        with pytest.raises(ValueError) as exc_info:
            service.validate_input(params)
        
        assert "Formato data non valido" in str(exc_info.value)
    
    def test_validate_input_future_date(self, service):
        """Test validazione con data futura"""
        future_date = datetime.now() + timedelta(days=30)
        params = {
            'symbol': 'AAPL',
            'start_date': '2024-01-01',
            'end_date': future_date.strftime('%Y-%m-%d')
        }
        
        with pytest.raises(ValueError) as exc_info:
            service.validate_input(params)
        
        assert "La data di fine non può essere nel futuro" in str(exc_info.value)
    
    @patch('yfinance.Ticker')
    def test_get_stock_data_success(self, mock_ticker, service, valid_params):
        """Test recupero dati con successo"""
        # Mock response
        mock_data = Mock()
        mock_data.empty = False
        mock_data.reset_index.return_value.iterrows.return_value = [
            (0, {
                'Date': datetime(2024, 1, 1),
                'Open': 100.0,
                'High': 105.0,
                'Low': 99.0,
                'Close': 103.0,
                'Volume': 1000000
            })
        ]
        
        mock_ticker.return_value.history.return_value = mock_data
        
        result = service.get_stock_data(**valid_params)
        
        assert result['success'] is True
        assert result['data']['symbol'] == 'AAPL'
        assert len(result['data']['records']) == 1
        assert result['data']['records'][0]['close'] == 103.0
    
    @patch('yfinance.Ticker')
    def test_get_stock_data_empty_response(self, mock_ticker, service, valid_params):
        """Test con risposta vuota da Yahoo"""
        mock_data = Mock()
        mock_data.empty = True
        mock_ticker.return_value.history.return_value = mock_data
        
        result = service.get_stock_data(**valid_params)
        
        assert result['success'] is False
        assert "Nessun dato trovato" in result['error']
    
    def test_get_multiple_stocks(self, service):
        """Test recupero multipli titoli"""
        # Per un test reale, questo dovrebbe essere mockato
        # Qui testiamo solo la struttura della risposta
        with patch.object(service, 'get_stock_data') as mock_get:
            mock_get.return_value = {
                'success': True,
                'data': {'symbol': 'TEST', 'records': []}
            }
            
            result = service.get_multiple_stocks(
                ['AAPL', 'GOOGL'],
                '2024-01-01',
                '2024-01-31'
            )
            
            assert result['success'] is True
            assert 'data' in result
            assert 'errors' in result
            assert mock_get.call_count == 2


if __name__ == '__main__':
    pytest.main([__file__])