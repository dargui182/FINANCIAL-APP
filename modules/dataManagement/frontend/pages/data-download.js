/**
 * Logica per la pagina di download dati
 */
class DataDownloadManager {
    constructor() {
        this.currentData = null;
        this.dataTable = null;
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
        const endDate = new Date();
        const startDate = new Date();
        startDate.setMonth(startDate.getMonth() - 3); // Default 3 mesi
        
        document.getElementById('end-date').value = endDate.toISOString().split('T')[0];
        document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
    }
    
    setQuickRange(range) {
        const endDate = new Date();
        let startDate = new Date();
        
        switch (range) {
            case '1M':
                startDate.setMonth(startDate.getMonth() - 1);
                break;
            case '3M':
                startDate.setMonth(startDate.getMonth() - 3);
                break;
            case '6M':
                startDate.setMonth(startDate.getMonth() - 6);
                break;
            case '1Y':
                startDate.setFullYear(startDate.getFullYear() - 1);
                break;
            case 'YTD':
                startDate = new Date(endDate.getFullYear(), 0, 1);
                break;
        }
        
        document.getElementById('end-date').value = endDate.toISOString().split('T')[0];
        document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
        
        // Evidenzia bottone attivo
        document.querySelectorAll('.quick-range-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.range === range);
        });
    }
    
    async searchSymbols(query) {
        const response = await window.apiClient.get('/data-management/symbols/search', { q: query });
        
        if (response.success && response.data.length > 0) {
            this.showSuggestions(response.data);
        } else {
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
                formatter: (value) => `$${value.toFixed(2)}`
            },
            { 
                key: 'high', 
                label: 'Massimo',
                formatter: (value) => `$${value.toFixed(2)}`
            },
            { 
                key: 'low', 
                label: 'Minimo',
                formatter: (value) => `$${value.toFixed(2)}`
            },
            { 
                key: 'close', 
                label: 'Chiusura',
                formatter: (value) => `$${value.toFixed(2)}`
            },
            { 
                key: 'volume', 
                label: 'Volume',
                formatter: (value) => value.toLocaleString()
            }
        ]);
    }
    
    async loadData() {
        // Mostra loading
        this.showLoading();
        
        const formData = {
            symbol: document.getElementById('symbol').value.toUpperCase(),
            start_date: document.getElementById('start-date').value,
            end_date: document.getElementById('end-date').value
        };
        
        // Carica dati principali
        const response = await window.apiClient.post('/data-management/stock/data', formData);
        
        if (response.success) {
            this.currentData = response.data;
            this.displayData(response.data);
            
            // Carica analisi
            this.loadAnalysis(formData);
            
            // Abilita download
            document.getElementById('download-csv').disabled = false;
            document.getElementById('download-excel').disabled = false;
            
            window.notifications.success('Dati caricati con successo!');
        } else {
            window.notifications.error(`Errore: ${response.error}`);
            this.hideLoading();
        }
    }
    
    async loadAnalysis(params) {
        const response = await window.apiClient.post('/data-management/stock/analysis', params);
        
        if (response.success) {
            this.displayAnalysis(response.data);
        }
    }
    
    displayData(data) {
        // Nascondi empty state
        document.getElementById('empty-state').style.display = 'none';
        
        // Mostra info
        document.getElementById('data-info').style.display = 'block';
        document.getElementById('info-content').innerHTML = `
            <p><strong>Simbolo:</strong> ${data.symbol}</p>
            <p><strong>Periodo:</strong> ${data.first_date} - ${data.last_date}</p>
            <p><strong>Record totali:</strong> ${data.count}</p>
        `;
        
        // Mostra tabella
        document.getElementById('data-table-container').style.display = 'block';
        this.dataTable.setData(data.records);
        
        this.hideLoading();
    }
    
    displayAnalysis(analysis) {
        // Mostra summary
        document.getElementById('stats-summary').style.display = 'grid';
        
        // Aggiorna valori
        document.getElementById('current-price').textContent = 
            `$${analysis.price_stats.current.toFixed(2)}`;
        
        const changeClass = analysis.returns.total >= 0 ? 'positive' : 'negative';
        document.getElementById('total-change').innerHTML = 
            `<span class="${changeClass}">${analysis.returns.total >= 0 ? '+' : ''}${analysis.returns.total.toFixed(2)}%</span>`;
        
        document.getElementById('volatility').textContent = 
            `${analysis.volatility.daily.toFixed(2)}%`;
        
        document.getElementById('avg-volume').textContent = 
            this.formatVolume(analysis.volume_stats.daily_avg);
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
        if (!this.currentData) return;
        
        const params = {
            symbol: this.currentData.symbol,
            start_date: document.getElementById('start-date').value,
            end_date: document.getElementById('end-date').value,
            format: format
        };
        
        window.notifications.info(`Preparazione download ${format.toUpperCase()}...`);
        
        const filename = `${params.symbol}_data.${format}`;
        await window.apiClient.download('/data-management/stock/download', filename);
    }
    
    showLoading() {
        document.getElementById('empty-state').innerHTML = `
            <div class="loader"></div>
            <p>Caricamento dati in corso...</p>
        `;
    }
    
    hideLoading() {
        // Loader verrà nascosto quando si mostra il contenuto
    }
}

// Inizializza quando DOM è pronto
document.addEventListener('DOMContentLoaded', () => {
    new DataDownloadManager();
});