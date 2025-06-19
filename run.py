#!/usr/bin/env python
"""
Script di avvio dell'applicazione Financial App
"""
import os
import sys
from pathlib import Path

# Aggiungi il percorso root al Python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from orchestrator.app import FinancialApp
from dotenv import load_dotenv


def main():
    """Funzione principale"""
    # Carica variabili d'ambiente
    load_dotenv()
    
    # Crea e avvia l'applicazione
    app = FinancialApp()
    
    # Ottieni configurazioni da env
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    # Avvia
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()