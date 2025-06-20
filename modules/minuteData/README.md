# Minute Data Module

Modulo specializzato per il download e gestione di dati intraday a 1 minuto da Yahoo Finance.

## Caratteristiche

- **Download dati a 1 minuto** per analisi intraday
- **Cache intelligente** con download incrementale
- **Aggregazione timeframe** (5m, 15m, 30m, 1h)
- **Filtro ore di mercato** (9:30-16:00 ET)
- **Auto-refresh** durante ore di trading
- **Export CSV/Excel** con timeframe multipli

## Limitazioni

- Dati disponibili solo per gli **ultimi 30 giorni**
- Download in chunks di massimo **7 giorni** per volta
- Richiede connessione stabile per grandi volumi

## Struttura

```
minuteData/
├── backend/
│   ├── api/          # Routes API
│   ├── services/     # Servizio dati minuto
│   └── __init__.py
├── frontend/
│   └── pages/        # UI per dati intraday
└── README.md
```

## API Endpoints

### `POST /api/v1/minute-data/data/1m`
Recupera dati a 1 minuto con cache.

**Request:**
```json
{
    "symbol": "AAPL",
    "start_date": "2024-12-20",
    "end_date": "2024-12-27",
    "use_cache": true
}
```

### `POST /api/v1/minute-data/data/aggregate`
Aggrega dati minuto in timeframe maggiori.

**Request:**
```json
{
    "records": [...],  // Array dati 1m
    "timeframe": "5m"  // 5m, 15m, 30m, 1h
}
```

### `POST /api/v1/minute-data/data/market-hours`
Filtra solo dati durante ore di mercato.

### `GET /api/v1/minute-data/data/today/{symbol}`
Dati di oggi per un simbolo.

### `GET /api/v1/minute-data/data/last-week/{symbol}`
Dati ultima settimana.

### `POST /api/v1/minute-data/download`
Download dati in CSV/Excel con timeframe custom.

## Utilizzo Frontend

1. **Selezione periodo**: Max 30 giorni nel passato
2. **Quick ranges**: Oggi, Ieri, 3D, 1W, 2W, MAX
3. **Aggregazione live**: Cambia timeframe senza ricarica
4. **Auto-refresh**: Ogni 5 min durante mercato aperto

## Cache Management

I dati vengono salvati in:
```
resources/data/price/{symbol}/minute/
```

### Struttura file:
- `{symbol}_minute.csv`: Dati raw 1 minuto
- `metadata.json`: Info su ultimo aggiornamento

### Download incrementale:
- Controlla dati esistenti
- Scarica solo giorni mancanti
- Merge automatico dei dataset

## Timeframe Aggregation

Supporta aggregazione OHLCV corretta:
- **Open**: Primo valore del periodo
- **High**: Massimo del periodo
- **Low**: Minimo del periodo
- **Close**: Ultimo valore del periodo
- **Volume**: Somma dei volumi

## Best Practices

1. **Usa cache** per ridurre chiamate API
2. **Scarica di notte/weekend** per evitare traffico
3. **Aggrega localmente** invece di ri-scaricare
4. **Monitora limiti** Yahoo Finance

## Esempi di Codice

### Python - Uso del servizio
```python
from modules.minuteData.backend.services import MinuteDataService

service = MinuteDataService()

# Download con cache
result = service.get_minute_data(
    symbol='AAPL',
    start_date='2024-12-20',
    end_date='2024-12-27',
    use_cache=True
)

# Aggrega a 5 minuti
if result['success']:
    aggregated = service.aggregate_to_timeframe(
        result['data']['records'],
        timeframe='5m'
    )
```

### JavaScript - Frontend
```javascript
// Carica dati
const response = await apiClient.post('/minute-data/data/1m', {
    symbol: 'AAPL',
    start_date: '2024-12-20',
    end_date: '2024-12-27',
    use_cache: true
});

// Aggrega a 15 minuti
const aggregated = await apiClient.post('/minute-data/data/aggregate', {
    records: response.data.data.records,
    timeframe: '15m'
});
```

## Performance

- **1 giorno**: ~390 record (6.5h * 60min)
- **1 settimana**: ~1,950 record
- **30 giorni**: ~11,700 record
- **File size**: ~0.5-3 MB per simbolo

## Future Enhancements

- [ ] Supporto pre/post market
- [ ] Streaming real-time
- [ ] Indicatori tecnici su dati minuto
- [ ] Compressione dati storici
- [ ] Multi-symbol download parallelo