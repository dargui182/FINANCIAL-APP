/**
 * Logica per la pagina di download dati
 */
class DataDownloadManager {
    constructor() {
        this.currentData = null;
        this.dataTable = null;
        this.apiBasePath = '/api/v1/data-management'; // Path corretto in kebab-case
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setDefaultDates();
        this.initializeTable();
    }
    
    setupEventListeners() {
        // Form submit
        document.getElementById('download-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.loadData();
        });
        
        // Quick range buttons
        document.querySelectorAll('.quick-range-btn').forEach(btn => {
            btn.addEventListener('click', () => this.setQuickRange(btn.dataset.range));
        });
        
        // Download buttons
        document.getElementById('download-csv').addEventListener('click', () => {
            this.downloadData('csv');
        });
        
        document.getElementById('download-excel').addEventListener('click', () => {
            this.downloadData('excel');
        });
        
        // Symbol search
        const symbolInput = document.getElementById('symbol');
        let searchTimeout;
        
        symbolInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value;
            
            if (query.length >= 1) {
                searchTimeout = setTimeout(() => this.searchSymbols(query), 300);
            } else {
                this.hideSuggestions();
            }
        });
        
        // Click outside to close suggestions
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.symbol-input-wrapper')) {
                this.hideSuggestions();
            }
        });
    }
    
    setDefaultDates() {
        // Usa date del 2024 per sicurezza (evita problemi con date future)
        const endDate = new Date('2024-12-31');
        const startDate = new Date('2024-01-01');
        
        document.getElementById('end-date').value = endDate.toISOString().split('T')[0];
        document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
        
        console.log('Date di default impostate:', {
            start: startDate.toISOString().split('T')[0],
            end: endDate.toISOString().split('T')[0]
        });
    }
    
    setQuickRange(range) {
        // Usa date del 2024 per evitare problemi con date future
        const endDate = new Date('2024-12-31');
        let startDate = new Date('2024-12-31');
        
        switch (range) {
            case '1M':
                startDate = new Date('2024-11-01');
                break;
            case '3M':
                startDate = new Date('2024-09-01');
                break;
            case '6M':
                startDate = new Date('2024-06-01');
                break;
            case '1Y':
                startDate = new Date('2024-01-01');
                break;
            case 'YTD':
                startDate = new Date('2024-01-01');
                break;
        }
        
        document.getElementById('end-date').value = endDate.toISOString().split('T')[0];
        document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
        
        console.log('Quick range impostato:', {
            range,
            start: startDate.toISOString().split('T')[0],
            end: endDate.toISOString().split('T')[0]
        });
        
        // Evidenzia bottone attivo
        document.querySelectorAll('.quick-range-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.range === range);
        });
    }
    
    async searchSymbols(query) {
        try {
            console.log('Ricerca simboli per:', query);
            
            // Usa l'endpoint corretto
            const response = await this.makeApiCall('GET', `/symbols/search?q=${encodeURIComponent(query)}`);
            
            if (response.success && response.data && Array.isArray(response.data)) {
                this.showSuggestions(response.data);
            } else {
                console.log('Nessun dato valido ricevuto:', response);
                this.hideSuggestions();
            }
        } catch (error) {
            console.error('Errore ricerca simboli:', error);
            this.hideSuggestions();
        }
    }
    
    showSuggestions(symbols) {
        const container = document.getElementById('symbol-suggestions');
        container.innerHTML = symbols.map(s => `
            <div class="suggestion-item" data-symbol="${s.symbol}">
                <strong>${s.symbol}</strong> - ${s.name}
            </div>
        `).join('');
        
        container.style.display = 'block';
        
        // Click su suggerimento
        container.querySelectorAll('.suggestion-item').forEach(item => {
            item.addEventListener('click', () => {
                document.getElementById('symbol').value = item.dataset.symbol;
                this.hideSuggestions();
            });
        });
    }
    
    hideSuggestions() {
        document.getElementById('symbol-suggestions').style.display = 'none';
    }
    
    initializeTable() {
        this.dataTable = new ReusableTable('data-table', {
            sortable: true,
            filterable: true,
            paginated: true,
            pageSize: 20
        });
        
        // Definisci colonne
        this.dataTable.setColumns([
            { key: 'date', label: 'Data' },
            { 
                key: 'open', 
                label: 'Apertura',
                formatter: (value) => value ? `$${value.toFixed(2)}` : '-'
            },
            { 
                key: 'high', 
                label: 'Massimo',
                formatter: (value) => value ? `$${value.toFixed(2)}` : '-'
            },
            { 
                key: 'low', 
                label: 'Minimo',
                formatter: (value) => value ? `$${value.toFixed(2)}` : '-'
            },
            { 
                key: 'close', 
                label: 'Chiusura',
                formatter: (value) => value ? `$${value.toFixed(2)}` : '-'
            },
            { 
                key: 'volume', 
                label: 'Volume',
                formatter: (value) => value ? value.toLocaleString() : '-'
            }
        ]);
    }
    
    async makeApiCall(method, endpoint, data = null) {
        const url = `${this.apiBasePath}${endpoint}`;
        console.log(`${method} ${url}`);
        
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }
        
        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            // Controlla se la risposta è JSON
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const result = await response.json();
                return result;
            } else {
                // Per download di file
                return response;
            }
        } catch (error) {
            console.error(`Errore API ${method} ${url}:`, error);
            throw error;
        }
    }
    
    async loadData() {
        // Mostra loading
        this.showLoading();
        
        const formData = {
            symbol: document.getElementById('symbol').value.toUpperCase(),
            start_date: document.getElementById('start-date').value,
            end_date: document.getElementById('end-date').value
        };
        
        try {
            console.log('Caricamento dati per:', formData);
            
            // Carica dati principali
            const response = await this.makeApiCall('POST', '/stock/data', formData);
            
            console.log('Risposta API:', response);
            
            if (response.success && response.data) {
                this.currentData = response.data;
                this.displayData(response.data);
                
                // Carica analisi
                this.loadAnalysis(formData);
                
                // Abilita download
                document.getElementById('download-csv').disabled = false;
                document.getElementById('download-excel').disabled = false;
                
                window.notifications.success('Dati caricati con successo!');
            } else {
                const errorMsg = response.error || 'Risposta API non valida';
                window.notifications.error(`Errore: ${errorMsg}`);
                this.hideLoading();
            }
        } catch (error) {
            console.error('Errore caricamento dati:', error);
            window.notifications.error(`Errore di rete: ${error.message}`);
            this.hideLoading();
        }
    }
    
    async loadAnalysis(params) {
        try {
            const response = await this.makeApiCall('POST', '/stock/analysis', params);
            
            if (response.success && response.data) {
                this.displayAnalysis(response.data);
            }
        } catch (error) {
            console.error('Errore caricamento analisi:', error);
        }
    }
    
    displayData(data) {
        console.log('Display data chiamato con:', data);
        
        // Validazione dati
        if (!data || typeof data !== 'object') {
            console.error('Dati non validi:', data);
            window.notifications.error('Dati ricevuti non validi');
            this.hideLoading();
            return;
        }
        
        // Nascondi empty state
        document.getElementById('empty-state').style.display = 'none';
        
        // Mostra info
        document.getElementById('data-info').style.display = 'block';
        document.getElementById('info-content').innerHTML = `
            <p><strong>Simbolo:</strong> ${data.symbol || 'N/A'}</p>
            <p><strong>Periodo:</strong> ${data.first_date || 'N/A'} - ${data.last_date || 'N/A'}</p>
            <p><strong>Record totali:</strong> ${data.count || 0}</p>
        `;
        
        // Mostra tabella
        document.getElementById('data-table-container').style.display = 'block';
        
        // Verifica che records sia un array
        const records = data.records || [];
        if (!Array.isArray(records)) {
            console.error('Records non è un array:', records);
            window.notifications.error('Formato dati non valido');
            this.dataTable.setData([]);
        } else {
            console.log('Settando dati tabella:', records);
            this.dataTable.setData(records);
        }
        
        this.hideLoading();
    }
    
    displayAnalysis(analysis) {
        // Mostra summary
        document.getElementById('stats-summary').style.display = 'grid';
        
        // Protezione contro dati mancanti
        const priceStats = analysis.price_stats || {};
        const returns = analysis.returns || {};
        const volatility = analysis.volatility || {};
        const volumeStats = analysis.volume_stats || {};
        
        // Aggiorna valori
        document.getElementById('current-price').textContent = 
            priceStats.current ? `$${priceStats.current.toFixed(2)}` : 'N/A';
        
        const totalReturn = returns.total || 0;
        const changeClass = totalReturn >= 0 ? 'positive' : 'negative';
        document.getElementById('total-change').innerHTML = 
            `<span class="${changeClass}">${totalReturn >= 0 ? '+' : ''}${totalReturn.toFixed(2)}%</span>`;
        
        document.getElementById('volatility').textContent = 
            volatility.daily ? `${volatility.daily.toFixed(2)}%` : 'N/A';
        
        document.getElementById('avg-volume').textContent = 
            volumeStats.daily_avg ? this.formatVolume(volumeStats.daily_avg) : 'N/A';
    }
    
    formatVolume(volume) {
        if (volume >= 1000000000) {
            return (volume / 1000000000).toFixed(1) + 'B';
        } else if (volume >= 1000000) {
            return (volume / 1000000).toFixed(1) + 'M';
        } else if (volume >= 1000) {
            return (volume / 1000).toFixed(1) + 'K';
        }
        return volume.toString();
    }
    
    async downloadData(format) {
        if (!this.currentData) {
            window.notifications.warning('Nessun dato da scaricare');
            return;
        }
        
        // Prepara i parametri per il download
        const params = {
            symbol: this.currentData.symbol,
            start_date: document.getElementById('start-date').value,
            end_date: document.getElementById('end-date').value,
            format: format
        };
        
        window.notifications.info(`Preparazione download ${format.toUpperCase()}...`);
        
        try {
            // Usa il metodo API centralizzato
            const response = await this.makeApiCall('POST', '/stock/download', params);
            
            // Se arriviamo qui, response è un oggetto Response per il file
            if (response instanceof Response) {
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                
                // Nome file con timestamp per evitare cache
                const timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, '-');
                const filename = `${params.symbol}_data_${timestamp}.${format}`;
                
                // Crea link per download
                const link = document.createElement('a');
                link.href = downloadUrl;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // Cleanup
                window.URL.revokeObjectURL(downloadUrl);
                
                window.notifications.success(`Download ${format.toUpperCase()} completato: ${filename}`);
            } else {
                // Errore
                throw new Error(response.error || 'Download failed');
            }
            
        } catch (error) {
            console.error('Errore download completo:', error);
            window.notifications.error(`Errore download: ${error.message}`);
        }
    }
    
    showLoading() {
        document.getElementById('empty-state').innerHTML = `
            <div class="loader"></div>
            <p>Caricamento dati in corso...</p>
        `;
        document.getElementById('empty-state').style.display = 'block';
    }
    
    hideLoading() {
        // Loader verrà nascosto quando si mostra il contenuto
    }
}

// Inizializza quando DOM è pronto
document.addEventListener('DOMContentLoaded', () => {
    new DataDownloadManager();
});