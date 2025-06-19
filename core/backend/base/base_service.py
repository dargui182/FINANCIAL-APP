"""
Base Service Class - Principio SOLID: Single Responsibility
Ogni servizio eredita da questa classe base
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging


class BaseService(ABC):
    """Classe base per tutti i servizi"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def validate_input(self, data: Dict[str, Any]) -> bool:
        """Valida i dati di input"""
        pass
    
    def log_info(self, message: str) -> None:
        """Log informativo"""
        self.logger.info(message)
    
    def log_error(self, message: str, error: Optional[Exception] = None) -> None:
        """Log errori"""
        if error:
            self.logger.error(f"{message}: {str(error)}")
        else:
            self.logger.error(message)
    
    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """Gestione standard degli errori"""
        self.log_error(f"Errore in {context}", error)
        return {
            "success": False,
            "error": str(error),
            "context": context
        }