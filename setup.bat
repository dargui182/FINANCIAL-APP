@echo off
REM Setup script per Financial App - Windows

echo ===================================
echo Financial App - Setup Iniziale
echo ===================================

REM Verifica Python
echo Verifico Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRORE] Python non trovato. Installa Python 3.8+
    pause
    exit /b 1
)
echo [OK] Python trovato

REM Mostra versione Python
python --version

REM Crea virtual environment
echo Creo ambiente virtuale...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERRORE] Impossibile creare virtual environment
    pause
    exit /b 1
)
echo [OK] Ambiente virtuale creato

REM Attiva virtual environment
echo Attivo ambiente virtuale...
call venv\Scripts\activate.bat
echo [OK] Ambiente virtuale attivato

REM Aggiorna pip
echo Aggiorno pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [ERRORE] Impossibile aggiornare pip
    pause
    exit /b 1
)
echo [OK] pip aggiornato

REM Installa dipendenze
echo Installo dipendenze...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERRORE] Impossibile installare dipendenze
    pause
    exit /b 1
)
echo [OK] Dipendenze installate

REM Crea file .env se non esiste
if not exist .env (
    echo Creo file .env...
    copy .env.example .env
    echo [OK] File .env creato
) else (
    echo [OK] File .env gia esistente
)

REM Crea directory necessarie
echo Creo directory necessarie...
if not exist "static\core\css" mkdir "static\core\css"
if not exist "static\core\js" mkdir "static\core\js"
if not exist "logs" mkdir "logs"
echo [OK] Directory create

echo.
echo ===================================
echo Setup completato con successo!
echo ===================================
echo.
echo Per avviare l'applicazione:
echo   1. Attiva l'ambiente virtuale:
echo      venv\Scripts\activate
echo.
echo   2. Avvia l'app:
echo      python run.py
echo.
echo L'app sara disponibile su http://localhost:5000
echo.
pause