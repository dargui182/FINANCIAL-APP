"""
Applicazione principale - Orchestrator
Gestisce il caricamento dei moduli e l'inizializzazione dell'app
"""
from flask import Flask, render_template, send_from_directory, jsonify
from flask_cors import CORS
import os
import sys
import logging
from pathlib import Path

# Aggiungi path per importare moduli
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.backend.config.settings import (
    ALLOWED_ORIGINS, 
    STATIC_DIR, 
    API_PREFIX,
    ENABLED_MODULES,
    LOG_LEVEL,
    LOG_FORMAT
)
from orchestrator.module_loader import ModuleLoader


class FinancialApp:
    """Classe principale dell'applicazione"""
    
    def __init__(self):
        self.setup_logging()
        self.app = Flask(__name__, 
                        static_folder=str(STATIC_DIR),
                        template_folder=str(BASE_DIR / 'templates'))
        self.setup_app()
        self.loader = ModuleLoader(self.app)
        self.logger = logging.getLogger(__name__)
        
    def setup_logging(self):
        """Configura il logging dell'applicazione"""
        logging.basicConfig(
            level=getattr(logging, LOG_LEVEL),
            format=LOG_FORMAT,
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(BASE_DIR / 'logs' / 'app.log')
            ]
        )
        
    def setup_app(self):
        """Configura l'applicazione Flask"""
        # CORS
        CORS(self.app, origins=ALLOWED_ORIGINS)
        
        # Configurazioni
        self.app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
        
        # Routes base
        self.setup_base_routes()
    
    def setup_base_routes(self):
        """Configura le route base dell'applicazione"""
        
        @self.app.route('/')
        def index():
            """Home page con lista moduli"""
            modules = self.loader.get_loaded_modules()
            return render_template('index.html', modules=modules)
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return {'status': 'healthy', 'modules': len(self.loader.loaded_modules)}
        
        @self.app.route('/debug/routes')
        def debug_routes():
            """Debug endpoint per vedere tutte le routes"""
            routes = self.loader.get_all_routes()
            
            # Separa per tipo
            api_routes = [r for r in routes if API_PREFIX in r['rule']]
            other_routes = [r for r in routes if API_PREFIX not in r['rule']]
            
            return jsonify({
                'success': True,
                'data': {
                    'total_routes': len(routes),
                    'api_routes_count': len(api_routes),
                    'other_routes_count': len(other_routes),
                    'api_routes': api_routes,
                    'other_routes': other_routes,
                    'loaded_modules': self.loader.loaded_modules,
                    'api_prefix': API_PREFIX
                }
            })
        
        @self.app.route('/debug/module/<module_name>')
        def debug_module(module_name):
            """Debug specifico per un modulo"""
            if not self.loader.is_module_loaded(module_name):
                return jsonify({
                    'success': False,
                    'error': f'Modulo {module_name} non caricato'
                }), 404
            
            # Trova route del modulo
            kebab_name = ModuleLoader.camel_to_kebab(module_name)
            module_prefix = f"{API_PREFIX}/{kebab_name}"
            
            all_routes = self.loader.get_all_routes()
            module_routes = [r for r in all_routes if module_prefix in r['rule']]
            
            return jsonify({
                'success': True,
                'data': {
                    'module_name': module_name,
                    'kebab_name': kebab_name,
                    'expected_prefix': module_prefix,
                    'routes_found': len(module_routes),
                    'routes': module_routes,
                    'module_info': self.loader.module_info.get(module_name, {})
                }
            })
        
        # Serve static files per i moduli
        @self.app.route('/modules/<module>/<path:filename>')
        def serve_module_static(module, filename):
            """Serve file statici dei moduli"""
            module_path = BASE_DIR / 'modules' / module / 'frontend'
            return send_from_directory(str(module_path), filename)
        
        # Serve core static files
        @self.app.route('/static/core/<path:filename>')
        def serve_core_static(filename):
            """Serve file statici del core"""
            core_path = BASE_DIR / 'core' / 'frontend'
            return send_from_directory(str(core_path), filename)
    
    def run(self, host='0.0.0.0', port=5000, debug=True):
        """Avvia l'applicazione"""
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"Financial App - Architettura Modulare")
        self.logger.info(f"{'='*60}")
        
        # Carica moduli
        self.logger.info("Caricamento moduli...")
        self.loader.load_enabled_modules()
        
        # Debug route info
        self.loader.debug_route_info()
        
        # Stampa info
        self.logger.info(f"Moduli caricati: {', '.join(self.loader.loaded_modules)}")
        self.logger.info(f"API Prefix: {API_PREFIX}")
        self.logger.info(f"Server: http://{host}:{port}")
        self.logger.info(f"Debug routes: http://{host}:{port}/debug/routes")
        self.logger.info(f"Debug dataManagement: http://{host}:{port}/debug/module/dataManagement")
        self.logger.info(f"{'='*60}\n")
        
        # Avvia server
        self.app.run(host=host, port=port, debug=debug)


def create_app():
    """Factory function per creare l'app"""
    financial_app = FinancialApp()
    return financial_app.app


if __name__ == '__main__':
    app = FinancialApp()
    app.run()