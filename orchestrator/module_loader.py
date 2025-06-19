"""
Module Loader - Carica dinamicamente i moduli
"""
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Any

from core.backend.config.settings import ENABLED_MODULES, API_PREFIX, MODULES_DIR


class ModuleLoader:
    """Gestisce il caricamento dinamico dei moduli"""
    
    def __init__(self, app):
        self.app = app
        self.loaded_modules = []
        self.module_info = {}
        self.logger = logging.getLogger(__name__)
        
    def load_enabled_modules(self):
        """Carica tutti i moduli abilitati"""
        for module_name in ENABLED_MODULES:
            try:
                self.load_module(module_name)
            except Exception as e:
                self.logger.error(f"Errore caricamento modulo {module_name}: {e}")
    
    def load_module(self, module_name: str):
        """Carica un singolo modulo"""
        self.logger.info(f"Caricamento modulo: {module_name}")
        
        # Verifica esistenza modulo
        module_path = Path(MODULES_DIR) / module_name
        if not module_path.exists():
            raise ValueError(f"Modulo {module_name} non trovato in {module_path}")
        
        # Carica blueprint API se esiste
        try:
            # Import dinamico del modulo
            api_module = importlib.import_module(f'modules.{module_name}.backend.api.routes')
            
            # Cerca il blueprint
            blueprint_name = f'{module_name}_bp'
            if hasattr(api_module, blueprint_name):
                blueprint = getattr(api_module, blueprint_name)
                
                # Registra blueprint con prefix
                url_prefix = f"{API_PREFIX}/{self.camel_to_kebab(module_name)}"
                self.app.register_blueprint(blueprint, url_prefix=url_prefix)
                
                self.logger.info(f"Registrato blueprint {module_name} su {url_prefix}")
            
        except ImportError as e:
            self.logger.warning(f"Nessun blueprint API per {module_name}: {e}")
        
        # Carica informazioni modulo
        self.load_module_info(module_name, module_path)
        
        # Aggiungi a moduli caricati
        self.loaded_modules.append(module_name)
        
    def load_module_info(self, module_name: str, module_path: Path):
        """Carica informazioni del modulo dal README o metadata"""
        info = {
            'name': module_name,
            'display_name': self.format_module_name(module_name),
            'path': str(module_path),
            'has_frontend': (module_path / 'frontend').exists(),
            'has_backend': (module_path / 'backend').exists(),
            'endpoints': []
        }
        
        # Leggi README se esiste
        readme_path = module_path / 'README.md'
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                info['description'] = f.read().split('\n')[0].replace('#', '').strip()
        else:
            info['description'] = f"Modulo {info['display_name']}"
        
        # Cerca pagine frontend
        if info['has_frontend']:
            pages_path = module_path / 'frontend' / 'pages'
            if pages_path.exists():
                info['pages'] = [p.stem for p in pages_path.glob('*.html')]
        
        self.module_info[module_name] = info
    
    def get_loaded_modules(self) -> List[Dict[str, Any]]:
        """Restituisce informazioni sui moduli caricati"""
        return [self.module_info[name] for name in self.loaded_modules]
    
    def is_module_loaded(self, module_name: str) -> bool:
        """Verifica se un modulo è caricato"""
        return module_name in self.loaded_modules
    
    @staticmethod
    def camel_to_kebab(name: str) -> str:
        """Converte camelCase in kebab-case"""
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append('-')
            result.append(char.lower())
        return ''.join(result)
    
    @staticmethod
    def format_module_name(name: str) -> str:
        """Formatta il nome del modulo per display"""
        # Separa camelCase
        result = []
        for i, char in enumerate(name):
            if char.isupper() and i > 0:
                result.append(' ')
            result.append(char)
        return ''.join(result).title()