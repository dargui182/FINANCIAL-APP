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
            self.logger.info(f"=== INIZIO CARICAMENTO MODULO: {module_name} ===")
            
            # Verifica esistenza modulo
            module_path = Path(MODULES_DIR) / module_name
            if not module_path.exists():
                raise ValueError(f"Modulo {module_name} non trovato in {module_path}")
            
            self.logger.info(f"Path modulo verificato: {module_path}")
            
            # Verifica esistenza file routes.py
            routes_file = module_path / "backend" / "api" / "routes.py"
            self.logger.info(f"Verifico file routes: {routes_file}")
            self.logger.info(f"File routes esiste: {routes_file.exists()}")
            
            # Carica blueprint API se esiste
            blueprint_loaded = False
            try:
                # Import dinamico del modulo
                module_import_path = f'modules.{module_name}.backend.api.routes'
                self.logger.info(f"=== TENTATIVO IMPORT: {module_import_path} ===")
                
                api_module = importlib.import_module(module_import_path)
                self.logger.info(f"✓ Import modulo riuscito")
                
                # Lista tutti gli attributi del modulo
                all_attrs = [attr for attr in dir(api_module) if not attr.startswith('__')]
                self.logger.info(f"Attributi modulo: {all_attrs}")
                
                # Cerca il blueprint
                blueprint_name = f'{module_name}_bp'
                self.logger.info(f"=== CERCANDO BLUEPRINT: {blueprint_name} ===")
                
                if hasattr(api_module, blueprint_name):
                    blueprint = getattr(api_module, blueprint_name)
                    self.logger.info(f"✓ Blueprint trovato: {type(blueprint)}")
                    
                    # Verifica che sia effettivamente un Blueprint
                    from flask import Blueprint
                    if isinstance(blueprint, Blueprint):
                        self.logger.info(f"✓ Tipo Blueprint confermato")
                        self.logger.info(f"✓ Nome blueprint: {blueprint.name}")
                        
                        # Registra blueprint con prefix
                        url_prefix = f"{API_PREFIX}/{self.camel_to_kebab(module_name)}"
                        self.logger.info(f"=== REGISTRAZIONE BLUEPRINT ===")
                        self.logger.info(f"URL prefix: {url_prefix}")
                        
                        # Prima di registrare, conta le route dell'app
                        routes_before = len(list(self.app.url_map.iter_rules()))
                        self.logger.info(f"Route app prima della registrazione: {routes_before}")
                        
                        # Registra il blueprint
                        self.app.register_blueprint(blueprint, url_prefix=url_prefix)
                        blueprint_loaded = True
                        
                        # Dopo la registrazione, conta di nuovo
                        routes_after = len(list(self.app.url_map.iter_rules()))
                        new_routes = routes_after - routes_before
                        self.logger.info(f"Route app dopo la registrazione: {routes_after}")
                        self.logger.info(f"Nuove route aggiunte: {new_routes}")
                        
                        self.logger.info(f"✓ ✓ ✓ BLUEPRINT REGISTRATO: {module_name} su {url_prefix}")
                        
                        # Verifica registrazione controllando le route dell'app
                        app_routes_with_prefix = []
                        for rule in self.app.url_map.iter_rules():
                            if url_prefix in str(rule):
                                app_routes_with_prefix.append({
                                    'rule': str(rule),
                                    'endpoint': rule.endpoint,
                                    'methods': list(rule.methods)
                                })
                        self.logger.info(f"Route registrate con prefix {url_prefix}: {app_routes_with_prefix}")
                        
                    else:
                        self.logger.error(f"✗ {blueprint_name} non è un Blueprint Flask: {type(blueprint)}")
                    
                else:
                    available_blueprints = [attr for attr in all_attrs if attr.endswith('_bp')]
                    self.logger.error(f"✗ Blueprint {blueprint_name} NON TROVATO")
                    self.logger.error(f"Blueprint disponibili: {available_blueprints}")
                    self.logger.error(f"Tutti gli attributi: {all_attrs}")
                
            except ImportError as e:
                self.logger.error(f"✗ ERRORE IMPORT: {e}")
                import traceback
                self.logger.error(f"Traceback completo:\n{traceback.format_exc()}")
            except Exception as e:
                self.logger.error(f"✗ ERRORE GENERICO nel caricamento blueprint: {e}")
                import traceback
                self.logger.error(f"Traceback completo:\n{traceback.format_exc()}")
                raise
            
            # Carica informazioni modulo
            self.load_module_info(module_name, module_path)
            
            # Aggiungi a moduli caricati
            self.loaded_modules.append(module_name)
            
            if blueprint_loaded:
                self.logger.info(f"✓ ✓ ✓ MODULO {module_name} CARICATO COMPLETAMENTE CON BLUEPRINT")
            else:
                self.logger.warning(f"⚠ MODULO {module_name} CARICATO SENZA BLUEPRINT")
            
            self.logger.info(f"=== FINE CARICAMENTO MODULO: {module_name} ===\n")
        
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