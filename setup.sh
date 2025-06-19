#!/bin/bash
# Setup script per Financial App

echo "==================================="
echo "Financial App - Setup Iniziale"
echo "==================================="

# Colori per output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Funzione per stampare successo
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Funzione per stampare errore
error() {
    echo -e "${RED}✗ $1${NC}"
    exit 1
}

# Verifica Python
echo "Verifico Python..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    success "Python3 trovato"
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    success "Python trovato"
else
    error "Python non trovato. Installa Python 3.8+"
fi

# Verifica versione Python
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "Versione Python: $PYTHON_VERSION"

# Crea virtual environment
echo "Creo ambiente virtuale..."
$PYTHON_CMD -m venv venv || error "Impossibile creare virtual environment"
success "Ambiente virtuale creato"

# Attiva virtual environment
echo "Attivo ambiente virtuale..."
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate || error "Impossibile attivare venv"
else
    # Unix-like
    source venv/bin/activate || error "Impossibile attivare venv"
fi
success "Ambiente virtuale attivato"

# Aggiorna pip
echo "Aggiorno pip..."
pip install --upgrade pip || error "Impossibile aggiornare pip"
success "pip aggiornato"

# Installa dipendenze
echo "Installo dipendenze..."
pip install -r requirements.txt || error "Impossibile installare dipendenze"
success "Dipendenze installate"

# Crea file .env se non esiste
if [ ! -f .env ]; then
    echo "Creo file .env..."
    cp .env.example .env || error "Impossibile creare .env"
    success "File .env creato"
else
    success "File .env già esistente"
fi

# Crea directory necessarie
echo "Creo directory necessarie..."
mkdir -p static/core/{css,js}
mkdir -p logs
success "Directory create"

# Rendi eseguibile run.py
chmod +x run.py
success "run.py reso eseguibile"

echo ""
echo "==================================="
echo "Setup completato con successo!"
echo "==================================="
echo ""
echo "Per avviare l'applicazione:"
echo "  1. Attiva l'ambiente virtuale:"
echo "     source venv/bin/activate (Linux/Mac)"
echo "     venv\\Scripts\\activate (Windows)"
echo ""
echo "  2. Avvia l'app:"
echo "     python run.py"
echo ""
echo "L'app sarà disponibile su http://localhost:5000"
echo ""