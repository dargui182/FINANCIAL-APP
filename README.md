# Financial App - Architettura Modulare

Applicazione web modulare per l'analisi e gestione di dati finanziari, costruita con Flask (backend) e JavaScript vanilla (frontend).

## 🏗️ Architettura

L'applicazione segue un'architettura modulare che permette:
- **Sviluppo indipendente** dei moduli
- **Riusabilità** dei componenti
- **Manutenibilità** del codice
- **Scalabilità** orizzontale

### Struttura Progetto

```
financial-app/
├── core/                    # Componenti condivisi
│   ├── backend/            # Servizi base, config, utils
│   └── frontend/           # Widget riusabili (tabelle, notifiche, etc.)
├── modules/                # Moduli indipendenti
│   └── dataManagement/     # Modulo gestione dati
├── orchestrator/           # Sistema di orchestrazione
├── static/                 # File statici
├── templates/              # Template HTML base
└── requirements.txt        # Dipendenze Python
```

## 🚀 Quick Start

### Prerequisiti

- Python 3.8+
- pip
- virtualenv (consigliato)

### Installazione

1. **Clona il repository**
```bash
git clone <repository-url>
cd financial-app
```

2. **Crea ambiente virtuale**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oppure
venv\Scripts\activate  # Windows
```

3. **Installa dipendenze**
```bash
pip install -r requirements.txt
```

4. **Configura variabili d'ambiente**
```bash
cp .env.example .env
# Modifica .env con le tue configurazioni
```

5. **Avvia l'applicazione**
```bash
python orchestrator/app.py
```

L'app sarà disponibile su `http://localhost:5000`

## 📦 Moduli Disponibili

### Data Management
- Download dati da Yahoo Finance
- Analisi statistiche base
- Export CSV/Excel
- Visualizzazione tabellare

## 🛠️ Componenti Core Riusabili

### Frontend Components

#### ReusableTable
```javascript
const table = new ReusableTable('container-id', {
    sortable: true,
    filterable: true,
    paginated: true
});

table.setColumns([
    { key: 'name', label: 'Nome' },
    { key: 'value', label: 'Valore', formatter: (v) => `€${v}` }
]);

table.setData(data);
```

#### NotificationSystem
```javascript
window.notifications.success('Operazione completata!');
window.notifications.error('Errore nel caricamento');
window.notifications.warning('Attenzione!');
window.notifications.info('Informazione');
```

#### LoaderManager
```javascript
// Loader overlay
window.loader.showOverlay('Caricamento...');
window.loader.hideOverlay();

// Loader inline
const loaderId = window.loader.showInline('#my-button');
window.loader.hideInline(loaderId);
```

#### ApiClient
```javascript
// GET request
const response = await window.apiClient.get('/endpoint', { param: 'value' });

// POST request
const response = await window.apiClient.post('/endpoint', { data: 'value' });

// Download file
await window.apiClient.download('/download', 'filename.csv');
```

### Backend Services

#### BaseService
```python
from core.backend.base.base_service import BaseService

class MyService(BaseService):
    def validate_input(self, data):
        # Implementa validazione
        return True
    
    def my_method(self):
        try:
            # Logica
            self.log_info("Operazione completata")
        except Exception as e:
            return self.handle_error(e, "my_method")
```

## 🔧 Sviluppo

### Aggiungere un Nuovo Modulo

1. **Crea la struttura del modulo**
```bash
mkdir -p modules/myModule/{backend/{api,services,models},frontend/{pages,components,styles}}
```

2. **Implementa il backend**
- Crea servizi in `services/`
- Definisci API routes in `api/routes.py`
- Esporta blueprint con nome `myModule_bp`

3. **Implementa il frontend**
- Crea pagine HTML in `pages/`
- Aggiungi logica JavaScript
- Definisci stili CSS

4. **Registra il modulo**
- Aggiungi a `ENABLED_MODULES` in `settings.py`

### Principi di Design

- **SOLID**: Single Responsibility, Open/Closed, etc.
- **DRY**: Don't Repeat Yourself
- **KISS**: Keep It Simple, Stupid
- **Modularità**: Ogni modulo è indipendente
- **Riusabilità**: Componenti core condivisi

## 📝 API Documentation

### Base URL
```
http://localhost:5000/api/v1
```

### Autenticazione
(Da implementare)

### Rate Limiting
(Da implementare)

## 🧪 Testing

```bash
# Run tutti i test
pytest

# Run con coverage
pytest --cov=.

# Run test specifico modulo
pytest modules/dataManagement/tests/
```

## 🚢 Deployment

### Docker
```bash
docker build -t financial-app .
docker run -p 5000:5000 financial-app
```

### Production
- Usa Gunicorn/uWSGI
- Configura Nginx come reverse proxy
- Imposta variabili d'ambiente sicure
- Abilita HTTPS

## 🤝 Contributing

1. Fork il progetto
2. Crea un branch (`git checkout -b feature/AmazingFeature`)
3. Commit le modifiche (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Apri una Pull Request

## 📄 License

Distribuito sotto licenza MIT. Vedi `LICENSE` per maggiori informazioni.

## 🐛 Known Issues

- Il modulo dataManagement richiede connessione internet per Yahoo Finance
- Limite rate Yahoo Finance: ~2000 richieste/ora

## 📞 Support

Per supporto, apri una issue su GitHub o contatta il team di sviluppo.