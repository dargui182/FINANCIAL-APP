/**
 * Gestione pagina dati intraday
 */
class MinuteDataManager {
    constructor() {
        this.currentData = null;
        this.currentTimeframe = '1m';
        this.aggregatedData = {};
        this.dataTable = null;
        this.autoRefreshInterval = null;
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.setDefaultDates();
        this.initializeTable();
        this.checkMarketStatus();
        
        // Auto-refresh ogni 5 minuti se mercato aperto
        setInterval(() => this.checkMarketStatus(), 60000); // Check ogni minuto
    }
    
    setupEventListeners() {
        // Form submit
        document.getElementById('minute-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.loadData();
        });
        
        // Quick ranges
        document.querySelectorAll('.quick-range-btn').forEach(btn => {
            btn.addEventListener('click', () => this.setQuickRange(btn.dataset.range));
        });
        
        // Timeframe selector
        document.querySelectorAll('.timeframe-btn').forEach(btn => {
            btn.addEventListener('click', () => this.changeTimeframe(btn.dataset.timeframe));
        });
        
        // Download buttons
        document.getElementById('download-csv').addEventListener('click', () => {
            this.downloadData('csv');
        });
        
        document.getElementById('download-excel').addEventListener('click', () => {
            this.downloadData('excel');
        });
        
        // Clear cache
        document.getElementById('clear-cache').addEventListener('click', () => {
            this.clearCache();
        });
        
        // Refresh button
        document.getElementById('refresh-btn').addEventListener('click', () => {
            this.loadData();
        });
    }
    
    setDefaultDates() {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        
        document.getElementById('end-date').value = today.toISOString().split('T')[0];
        document.getElementById('start-date').value = yesterday.toISOString().split('T')[0];
    }
    
    setQuickRange(range) {
        const endDate = new Date();
        let startDate = new Date();
        
        switch (range) {
            case 'TODAY':
                startDate = new Date();
                break;
            case 'YESTERDAY':
                startDate.setDate(startDate.getDate() - 1);
                endDate.setDate(endDate.getDate() - 1);
                break;
            case '3D':
                startDate.setDate(startDate.getDate() - 3);
                break;
            case '1W':
                startDate.setDate(startDate.getDate() - 7);
                break;
            case '2W':
                startDate.setDate(startDate.getDate() - 14);
                break;
            case 'MAX':
                startDate.setDate(startDate.getDate() - 30);
                break;
        }
        
        document.getElementById('start-date').value = startDate.toISOString().split('T')[0];
        document.getElementById('end-date').value = endDate.toISOString().split('T')[0];
        
        // Evidenzia bottone attivo
        document.querySelectorAll('.quick-range-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.range === range);
        });
    }
    
    checkMarketStatus() {
        const now = new Date();
        const hours = now.getHours();
        const minutes = now.getMinutes();
        const day = now.getDay();
        
        // Mercato US: 9:30-16:00 ET, Lun-Ven
        // Assumendo fuso orario locale (da adattare per ET)
        const isWeekday = day >= 1 && day <= 5;
        const marketHours = (hours === 9 && minutes >= 30) || (hours > 9 && hours < 16);
        const isMarketOpen = isWeekday && marketHours;
        
        const statusEl = document.getElementById('market-status');
        const textEl = document.getElementById('market-text');
        const refreshBtn = document.getElementById('refresh-btn');
        
        if (isMarketOpen) {
            statusEl.className = 'market-status open';
            textEl.textContent = 'Mercato Aperto';
            refreshBtn.style.display = 'block';
            
            // Se abbiamo dati di oggi, abilita auto-refresh
            if (this.currentData && this.isToday()) {
                this.startAutoRefresh();
            }
        } else {
            statusEl.className = 'market-status closed';
            textEl.textContent = 'Mercato Chiuso';
            refreshBtn.style.display = 'none';
            this.stopAutoRefresh();
        }
    }
    
    isToday() {
        if (!this.currentData || !this.currentData.records || this.currentData.records.length === 0) {
            return false;
        }
        
        const lastRecord = this.currentData.records[this.currentData.records.length - 1];
        const recordDate = new Date(lastRecord.date);
        const today = new Date();
        
        return recordDate.toDateString() === today.toDateString();
    }
    
    startAutoRefresh() {
        if (this.autoRefreshInterval) return;
        
        // Refresh ogni 5 minuti
        this.autoRefreshInterval = setInterval(() => {
            window.notifications.info('Aggiornamento automatico dati...');
            this.loadData();
        }, 5 * 60 * 1000);
    }
    
    stopAutoRefresh() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
            this.autoRefreshInterval = null;
        }
    }
    
    initializeTable() {
        this.dataTable = new ReusableTable('data-table', {
            sortable: true,
            filterable: true,
            paginated: true,
            pageSize: 50 // Più record per dati minuto
        });
        
        // Colonne per dati minuto
        this.updateTableColumns('1m');
    }
    
    updateTableColumns(timeframe) {
        const columns = [
            { 
                key: 'datetime', 
                label: 'Data/Ora',
                formatter: (value) => {
                    const dt = new Date(value);
                    return dt.toLocaleString('it-IT', {
                        day: '2-digit',
                        month: '2-digit',
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit'
                    });
                }
            },
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
        ];
        
        // Aggiungi colonna timeframe se aggregato
        if (timeframe !== '1m') {
            columns.push({
                key: 'timeframe',
                label: 'Timeframe'
            });
        }
        
        this.dataTable.setColumns(columns);
    }
    
    async loadData() {
        window.loader.showOverlay('Caricamento dati intraday...');
        
        const params = {
            symbol: document.getElementById('symbol').value.toUpperCase(),
            start_date: document.getElementById('start-date').value,
            end_date: document.getElementById('end-date').value,
            use_cache: document.getElementById('use-cache').checked
        };
        
        try {
            const response = await window.apiClient.post('/minuteData/data/1m', params);
            
            if (response.success && response.data && response.data.data) {
                this.currentData = response.data.data;
                this.aggregatedData = { '1m': this.currentData.records };
                
                // Applica filtro ore di mercato se richiesto
                if (document.getElementById('market-hours-only').checked) {
                    this.filterMarketHours();
                }
                
                this.displayData(this.currentData);
                
                // Check cache status
                await this.checkCacheStatus(params.symbol);
                
                const fromCache = response.data.data.from_cache ? ' (da cache)' : '';
                window.notifications.success(`Caricati ${this.currentData.count} record${fromCache}`);
                
                // Check auto-refresh
                this.checkMarketStatus();
            } else {
                window.notifications.error(`Errore: ${response.error || 'Caricamento fallito'}`);
            }
        } catch (error) {
            console.error('Errore:', error);
            window.notifications.error(`Errore: ${error.message}`);
        } finally {
            window.loader.hideOverlay();
        }
    }
    
    filterMarketHours() {
        if (!this.currentData || !this.currentData.records) return;
        
        const filtered = this.currentData.records.filter(record => {
            const time = record.time;
            return time >= '09:30:00' && time <= '16:00:00';
        });
        
        this.currentData.records = filtered;
        this.currentData.count = filtered.length;
        this.aggregatedData['1m'] = filtered;
    }
    
    displayData(data) {
        // Nascondi empty state
        document.getElementById('empty-state').style.display = 'none';
        
        // Mostra controlli
        document.getElementById('timeframe-selector').style.display = 'flex';
        document.getElementById('data-summary').style.display = 'grid';
        document.getElementById('download-options').style.display = 'block';
        document.getElementById('data-table-container').style.display = 'block';
        
        // Aggiorna summary
        this.updateSummary(data);
        
        // Mostra tabella
        const records = this.aggregatedData[this.currentTimeframe] || data.records;
        this.dataTable.setData(records);
    }
    
    updateSummary(data) {
        document.getElementById('total-records').textContent = data.count || 0;
        
        // Calcola giorni unici
        const uniqueDates = new Set(data.records.map(r => r.date));
        document.getElementById('trading-days').textContent = uniqueDates.size;
        
        // Prima e ultima data
        if (data.records && data.records.length > 0) {
            const firstDt = new Date(data.records[0].datetime);
            const lastDt = new Date(data.records[data.records.length - 1].datetime);
            
            document.getElementById('first-record').textContent = 
                firstDt.toLocaleString('it-IT', {
                    day: '2-digit',
                    month: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            
            document.getElementById('last-record').textContent = 
                lastDt.toLocaleString('it-IT', {
                    day: '2-digit',
                    month: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit'
                });
        }
    }
    
    async changeTimeframe(timeframe) {
        if (!this.currentData || timeframe === this.currentTimeframe) return;
        
        // Evidenzia bottone attivo
        document.querySelectorAll('.timeframe-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.timeframe === timeframe);
        });
        
        // Se già aggregato, usa cache
        if (this.aggregatedData[timeframe]) {
            this.currentTimeframe = timeframe;
            this.updateTableColumns(timeframe);
            this.dataTable.setData(this.aggregatedData[timeframe]);
            return;
        }
        
        // Altrimenti aggrega
        window.loader.showInline('#timeframe-selector', 'Aggregazione...');
        
        try {
            const response = await window.apiClient.post('/minuteData/data/aggregate', {
                records: this.currentData.records,
                timeframe: timeframe
            });
            
            if (response.success && response.data && response.data.data) {
                this.aggregatedData[timeframe] = response.data.data.records;
                this.currentTimeframe = timeframe;
                this.updateTableColumns(timeframe);
                this.dataTable.setData(response.data.data.records);
                
                window.notifications.success(
                    `Aggregati ${response.data.data.original_count} record in ${response.data.data.count} barre ${timeframe}`
                );
            }
        } catch (error) {
            console.error('Errore aggregazione:', error);
            window.notifications.error(`Errore: ${error.message}`);
        } finally {
            window.loader.hideInline('#timeframe-selector');
        }
    }
    
    async downloadData(format) {
        if (!this.currentData) {
            window.notifications.warning('Nessun dato da scaricare');
            return;
        }
        
        const params = {
            symbol: document.getElementById('symbol').value.toUpperCase(),
            start_date: document.getElementById('start-date').value,
            end_date: document.getElementById('end-date').value,
            format: format,
            timeframe: this.currentTimeframe
        };
        
        window.notifications.info(`Preparazione download ${format.toUpperCase()}...`);
        
        try {
            const response = await fetch('/api/v1/minute-data/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(params)
            });
            
            if (!response.ok) {
                throw new Error(`Download failed: ${response.status}`);
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${params.symbol}_${params.timeframe}_minute_data.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            window.notifications.success('Download completato');
        } catch (error) {
            console.error('Errore download:', error);
            window.notifications.error(`Errore: ${error.message}`);
        }
    }
    
    async checkCacheStatus(symbol) {
        try {
            const response = await window.apiClient.get(`/minuteData/stats/${symbol}`);
            
            if (response.success && response.data && response.data.data) {
                const stats = response.data.data;
                document.getElementById('cache-info').style.display = 'block';
                document.getElementById('cache-content').innerHTML = `
                    <p><strong>Record salvati:</strong> ${stats.record_count}</p>
                    <p><strong>Giorni unici:</strong> ${stats.unique_trading_days || 0}</p>
                    <p><strong>Periodo:</strong> ${stats.first_date} - ${stats.last_date}</p>
                    <p><strong>Dimensione:</strong> ${stats.file_size_kb.toFixed(2)} KB</p>
                `;
                
                document.getElementById('clear-cache').style.display = 'inline-block';
            } else {
                document.getElementById('cache-info').style.display = 'none';
                document.getElementById('clear-cache').style.display = 'none';
            }
        } catch (error) {
            console.error('Errore check cache:', error);
        }
    }
    
    async clearCache() {
        const symbol = document.getElementById('symbol').value.toUpperCase();
        
        if (!symbol) {
            window.notifications.warning('Inserisci un simbolo prima');
            return;
        }
        
        if (!confirm(`Cancellare la cache dei dati minuto per ${symbol}?`)) {
            return;
        }
        
        try {
            const response = await window.apiClient.delete(`/minuteData/cache/clear/${symbol}`);
            
            if (response.success) {
                window.notifications.success('Cache cancellata');
                document.getElementById('cache-info').style.display = 'none';
                document.getElementById('clear-cache').style.display = 'none';
            } else {
                window.notifications.error(`Errore: ${response.error}`);
            }
        } catch (error) {
            console.error('Errore clear cache:', error);
            window.notifications.error(`Errore: ${error.message}`);
        }
    }
}

// Inizializza quando DOM è pronto
document.addEventListener('DOMContentLoaded', () => {
    new MinuteDataManager();
});