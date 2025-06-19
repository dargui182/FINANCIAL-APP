# Data Management Module

Modulo per il download e la gestione dei dati finanziari da Yahoo Finance.

## Funzionalità

- **Download dati storici** per singoli titoli
- **Ricerca simboli** con autocompletamento
- **Analisi base** dei dati scaricati
- **Export** in formato CSV ed Excel
- **Visualizzazione tabellare** con ordinamento e filtri

## Struttura

```
dataManagement/
├── backend/
│   ├── api/          # Endpoints REST
│   ├── services/     # Logica business
│   └── models/       # Modelli dati
├── frontend/
│   ├── pages/        # Pagine HTML
│   ├── components/   # Componenti specifici
│   └── styles/       # CSS del modulo
└── README.md
```

## API Endpoints

### `POST /api/v1/data-management/stock/data`
Recupera dati storici di un titolo.

**Request:**
```json
{
    "symbol": "AAPL",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "interval": "1d"  // opzionale
}
```

### `GET /api/v1/data-management/stock/info/{symbol}`
Ottieni informazioni dettagliate su un titolo.

### `POST /api/v1/data-management/stock/download`
Scarica dati in formato CSV o Excel.

### `POST /api/v1/data-management/stock/analysis`
Esegue analisi statistiche sui dati.

## Componenti Frontend

### Stock Selector
- Autocompletamento simboli
- Validazione input
- Suggerimenti real-time

### Data Table
- Visualizzazione dati con paginazione
- Ordinamento colonne
- Filtro ricerca
- Export dati

## Servizi Backend

### YahooFinanceService
- Gestione API Yahoo Finance
- Retry automatico
- Gestione errori
- Cache temporanea

### DataProcessor
- Calcolo statistiche
- Preparazione export
- Analisi trend
- Formattazione dati

## Utilizzo

1. Accedi alla pagina del modulo
2. Inserisci il simbolo del titolo
3. Seleziona il periodo
4. Clicca "Carica Dati"
5. Visualizza e scarica i risultati

## Configurazione

Le impostazioni del modulo si trovano in `core/backend/config/settings.py`:

- `YAHOO_API_TIMEOUT`: Timeout richieste (default: 20s)
- `YAHOO_MAX_RETRIES`: Tentativi massimi (default: 3)

## Estensioni Future

- [ ] Supporto per multipli titoli simultanei
- [ ] Grafici interattivi
- [ ] Indicatori tecnici
- [ ] Salvataggio dati in database
- [ ] Scheduling download automatici