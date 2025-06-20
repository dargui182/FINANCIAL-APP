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
        
        // Clear cache button
        document.getElementById('clear-cache').addEventListener('click', () => {
            this.clearCache();
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
            case 'ALL':
                // Per storico completo useremo un endpoint specifico
                this.loadFullHistory();
                return;
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
            const response = await window.apiClient.get('/dataManagement/symbols/search', { q: query });
            
            if (response.success && response.data && response.data.data && Array.isArray(response.data.data)) {
                this.showSuggestions(response.data.data);
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
    
    async loadData() {
        // Mostra loading
        window.loader.showOverlay('Caricamento dati...');
        
        const formData = {
            symbol: document.getElementById('symbol').value.toUpperCase(),
            start_date: document.getElementById('start-date').value,
            end_date: document.getElementById('end-date').value,
            use_cache: document.getElementById('use-cache').checked,
            adjusted: document.getElementById('use-adjusted').checked
        };
        
        try {
            // Usa nuovo endpoint v2
            const response = await window.apiClient.post('/dataManagement/stock/data/v2', formData);
            
            console.log('Risposta API v2:', response); // Debug
            
            if (response.success && response.data && response.data.data) {
                this.currentData = response.data.data;
                this.displayData(response.data.data);
                
                // Carica analisi
                this.loadAnalysis(formData);
                
                // Mostra stato cache
                this.checkCacheStatus(formData.symbol);
                
                // Abilita download
                document.getElementById('download-csv').disabled = false;
                document.getElementById('download-excel').disabled = false;
                
                const cacheMsg = response.data.data.from_cache ? ' (da cache)' : '';
                window.notifications.success(`Dati caricati con successo${cacheMsg}!`);
            } else {
                const errorMsg = response.error || response.data?.error || 'Risposta API non valida';
                window.notifications.error(`Errore: ${errorMsg}`);
            }
        } catch (error) {
            console.error('Errore caricamento dati:', error);
            window.notifications.error(`Errore di rete: ${error.message}`);
        } finally {
            window.loader.hideOverlay();
        }
    }
    
    async loadFullHistory() {
        const symbol = document.getElementById('symbol').value.toUpperCase();
        
        if (!symbol) {
            window.notifications.warning('Inserisci un simbolo prima di caricare lo storico completo');
            return;
        }
        
        window.loader.showOverlay('Caricamento storico completo...');
        
        try {
            const response = await window.apiClient.post('/dataManagement/stock/history/full', {
                symbol: symbol,
                adjusted: document.getElementById('use-adjusted').checked
            });
            
            if (response.success && response.data && response.data.data) {
                this.currentData = response.data.data;
                this.displayData(response.data.data);
                
                // Aggiorna date nei campi
                if (response.data.data.first_date && response.data.data.last_date) {
                    document.getElementById('start-date').value = response.data.data.first_date;
                    document.getElementById('end-date').value = response.data.data.last_date;
                }
                
                // Carica analisi
                this.loadAnalysis({
                    symbol: symbol,
                    start_date: response.data.data.first_date,
                    end_date: response.data.data.last_date
                });
                
                // Evidenzia bottone ALL
                document.querySelectorAll('.quick-range-btn').forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.range === 'ALL');
                });
                
                // Abilita download
                document.getElementById('download-csv').disabled = false;
                document.getElementById('download-excel').disabled = false;
                
                window.notifications.success(`Storico completo caricato: ${response.data.data.count} record`);
            } else {
                window.notifications.error(`Errore: ${response.error || 'Caricamento fallito'}`);
            }
        } catch (error) {
            console.error('Errore caricamento storico:', error);
            window.notifications.error(`Errore: ${error.message}`);
        } finally {
            window.loader.hideOverlay();
        }
    }
    
    async loadAnalysis(params) {
        try {
            const response = await window.apiClient.post('/dataManagement/stock/analysis', params);
            
            if (response.success && response.data && response.data.data) {
                this.displayAnalysis(response.data.data);
            }
        } catch (error) {
            console.error('Errore caricamento analisi:', error);
        }
    }
    
    async checkCacheStatus(symbol) {
        try {
            const dataType = document.getElementById('use-adjusted').checked ? 'dailyAdjusted' : 'daily';
            const response = await window.apiClient.get(`/dataManagement/cache/stats/${symbol}`, {
                data_type: dataType
            });
            
            if (response.success && response.data && response.data.data) {
                const stats = response.data.data;
                document.getElementById('cache-status').style.display = 'block';
                document.getElementById('cache-content').innerHTML = `
                    <p><strong>Tipo dati:</strong> ${stats.data_type}</p>
                    <p><strong>Record salvati:</strong> ${stats.record_count}</p>
                    <p><strong>Periodo:</strong> ${stats.first_date} - ${stats.last_date}</p>
                    <p><strong>Date mancanti:</strong> ${stats.missing_dates}</p>
                    <p><strong>Dimensione file:</strong> ${stats.file_size_kb.toFixed(2)} KB</p>
                `;
                
                // Aggiungi listener per clear cache
                document.getElementById('clear-cache').onclick = () => this.clearCache(symbol, dataType);
            } else {
                document.getElementById('cache-status').style.display = 'none';
            }
        } catch (error) {
            console.error('Errore verifica cache:', error);
            document.getElementById('cache-status').style.display = 'none';
        }
    }
    
    async clearCache(symbol, dataType) {
        if (!symbol) {
            symbol = document.getElementById('symbol').value.toUpperCase();
            dataType = document.getElementById('use-adjusted').checked ? 'dailyAdjusted' : 'daily';
        }
        
        if (!symbol) {
            window.notifications.warning('Inserisci un simbolo');
            return;
        }
        
        if (!confirm(`Cancellare la cache per ${symbol} (${dataType})?`)) {
            return;
        }
        
        try {
            const response = await window.apiClient.delete(`/dataManagement/cache/clear/${symbol}?data_type=${dataType}`);
            
            if (response.success) {
                window.notifications.success('Cache cancellata con successo');
                document.getElementById('cache-status').style.display = 'none';
            } else {
                window.notifications.error(`Errore: ${response.error || response.data?.message || 'Errore sconosciuto'}`);
            }
        } catch (error) {
            console.error('Errore cancellazione cache:', error);
            window.notifications.error(`Errore: ${error.message}`);
        }
    }
    
    displayData(data) {
        console.log('Display data chiamato con:', data); // Debug
        
        // Validazione dati
        if (!data || typeof data !== 'object') {
            console.error('Dati non validi:', data);
            window.notifications.error('Dati ricevuti non validi');
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
            ${data.from_cache ? '<p><strong>Fonte:</strong> Cache locale</p>' : ''}
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
            console.log('Settando dati tabella:', records.length, 'record'); // Debug
            
            // Se abbiamo dati adjusted, mostra colonne appropriate
            if (records.length > 0 && records[0].adj_close !== undefined) {
                this.dataTable.setColumns([
                    { key: 'date', label: 'Data' },
                    { 
                        key: 'open', 
                        label: 'Apertura',
                        formatter: (value) => value ? `$${value.toFixed(2)}` : '-'
                    },
                    { 
                        key: 'close', 
                        label: 'Chiusura',
                        formatter: (value) => value ? `$${value.toFixed(2)}` : '-'
                    },
                    { 
                        key: 'adj_close', 
                        label: 'Chiusura Adj.',
                        formatter: (value) => value ? `$${value.toFixed(2)}` : '-'
                    },
                    { 
                        key: 'volume', 
                        label: 'Volume',
                        formatter: (value) => value ? value.toLocaleString() : '-'
                    }
                ]);
            }
            
            this.dataTable.setData(records);
        }
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
            format: format,
            adjusted: document.getElementById('use-adjusted').checked,
            include_analysis: document.getElementById('include-analysis').checked
        };
        
        window.notifications.info(`Preparazione download ${format.toUpperCase()}...`);
        
        try {
            // Usa endpoint v2
            const response = await fetch('/api/v1/data-management/stock/download/v2', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });
            
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Download failed: ${response.status} - ${errorText}`);
            }
            
            // Controlla content-type
            const contentType = response.headers.get('content-type');
            console.log('Content-Type:', contentType);
            
            if (contentType && contentType.includes('application/json')) {
                // Risposta JSON (errore)
                const result = await response.json();
                throw new Error(result.error || 'Download failed');
            }
            
            // È un file - procedi con il download
            const blob = await response.blob();
            const downloadUrl = window.URL.createObjectURL(blob);
            
            // Nome file con timestamp e tipo
            const timestamp = new Date().toISOString().slice(0, 19).replace(/[:]/g, '-');
            const adjustedLabel = params.adjusted ? 'adjusted' : 'regular';
            const filename = `${params.symbol}_${adjustedLabel}_${timestamp}.${format}`;
            
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
            
        } catch (error) {
            console.error('Errore download completo:', error);
            window.notifications.error(`Errore download: ${error.message}`);
        }
    }
}

// Inizializza quando DOM è pronto
document.addEventListener('DOMContentLoaded', () => {
    new DataDownloadManager();
});