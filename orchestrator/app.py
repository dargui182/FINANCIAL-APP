"""
Applicazione principale - Orchestrator
Gestisce il caricamento dei moduli e l'inizializzazione dell'app
"""
from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
import os
import sys
from pathlib import Path

# Aggiungi path per importare moduli
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.backend.config.settings import (
    ALLOWED_ORIGINS, 
    STATIC_DIR, 
    API_PREFIX,
    ENABLED_MODULES
)
from orchestrator.module_loader import ModuleLoader


class FinancialApp:
    """Classe principale dell'applicazione"""
    
    def __init__(self):
        self.app = Flask(__name__, 
                        static_folder=str(STATIC_DIR),
                        template_folder=str(BASE_DIR / 'templates'))
        self.setup_app()
        self.loader = ModuleLoader(self.app)
        
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
        # Carica moduli
        self.loader.load_enabled_modules()
        
        # Stampa info
        print(f"\n{'='*50}")
        print(f"Financial App - Architettura Modulare")
        print(f"{'='*50}")
        print(f"Moduli caricati: {', '.join(self.loader.loaded_modules)}")
        print(f"API Prefix: {API_PREFIX}")
        print(f"Server: http://{host}:{port}")
        print(f"{'='*50}\n")
        
        # Avvia server
        self.app.run(host=host, port=port, debug=debug)


def create_app():
    """Factory function per creare l'app"""
    financial_app = FinancialApp()
    return financial_app.app


if __name__ == '__main__':
    app = FinancialApp()
    app.run()