"""
Configurazione centrale dell'applicazione
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Carica variabili d'ambiente
load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
MODULES_DIR = BASE_DIR / "modules"
STATIC_DIR = BASE_DIR / "static"

# API Configuration
API_PREFIX = "/api/v1"
API_TIMEOUT = 30  # secondi

# CORS
ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5000",
]

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Yahoo Finance
YAHOO_API_TIMEOUT = 20
YAHOO_MAX_RETRIES = 3

# Database (future use)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///financial_app.db")

# Module Registry
ENABLED_MODULES = [
    "dataManagement",
    # Aggiungi qui altri moduli quando li crei
]