/**
 * Componente Tabella Riusabile
 * Principio: Single Responsibility - gestisce solo la visualizzazione tabellare
 */
class ReusableTable {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            sortable: true,
            filterable: true,
            paginated: true,
            pageSize: 10,
            ...options
        };
        this.data = [];
        this.filteredData = [];
        this.currentPage = 1;
        this.sortColumn = null;
        this.sortDirection = 'asc';
        
        this.init();
    }
    
    init() {
        if (!this.container) {
            console.error('Container non trovato');
            return;
        }
        this.container.classList.add('reusable-table-container');
    }
    
    setColumns(columns) {
        // Validazione columns
        if (!Array.isArray(columns)) {
            console.error('Columns deve essere un array');
            return this;
        }
        this.columns = columns;
        return this;
    }
    
    setData(data) {
        // Validazione e normalizzazione dei dati
        if (!data) {
            console.warn('Dati vuoti forniti alla tabella');
            this.data = [];
            this.filteredData = [];
        } else if (!Array.isArray(data)) {
            console.error('I dati devono essere un array, ricevuto:', typeof data, data);
            this.data = [];
            this.filteredData = [];
        } else {
            this.data = data;
            this.filteredData = [...data];
        }
        
        this.currentPage = 1; // Reset alla prima pagina
        this.render();
        return this;
    }
    
    render() {
        if (!this.container) {
            console.error('Container non disponibile per il rendering');
            return;
        }
        
        if (!this.columns || !Array.isArray(this.columns)) {
            this.container.innerHTML = '<div class="table-error">Configurazione colonne mancante</div>';
            return;
        }
        
        this.container.innerHTML = `
            ${this.options.filterable ? this.renderFilter() : ''}
            <div class="table-wrapper">
                <table class="reusable-table">
                    ${this.renderHeader()}
                    ${this.renderBody()}
                </table>
            </div>
            ${this.options.paginated ? this.renderPagination() : ''}
        `;
        this.attachEventListeners();
    }
    
    renderFilter() {
        return `
            <div class="table-filter">
                <input type="text" 
                       class="filter-input" 
                       placeholder="Cerca..."
                       id="${this.container.id}-filter">
            </div>
        `;
    }
    
    renderHeader() {
        const headers = this.columns.map(col => `
            <th class="${this.options.sortable ? 'sortable' : ''}" 
                data-column="${col.key}">
                ${col.label}
                ${this.renderSortIcon(col.key)}
            </th>
        `).join('');
        
        return `<thead><tr>${headers}</tr></thead>`;
    }
    
    renderSortIcon(columnKey) {
        if (!this.options.sortable) return '';
        
        if (this.sortColumn === columnKey) {
            return `<span class="sort-icon">${this.sortDirection === 'asc' ? '▲' : '▼'}</span>`;
        }
        return '<span class="sort-icon">⇅</span>';
    }
    
    renderBody() {
        // Gestisci caso array vuoto
        if (!Array.isArray(this.filteredData) || this.filteredData.length === 0) {
            return `<tbody><tr><td colspan="${this.columns.length}">Nessun dato disponibile</td></tr></tbody>`;
        }
        
        const startIdx = (this.currentPage - 1) * this.options.pageSize;
        const endIdx = startIdx + this.options.pageSize;
        const pageData = this.filteredData.slice(startIdx, endIdx);
        
        const rows = pageData.map(row => {
            const cells = this.columns.map(col => {
                const value = this.getCellValue(row, col);
                return `<td>${value}</td>`;
            }).join('');
            return `<tr>${cells}</tr>`;
        }).join('');
        
        return `<tbody>${rows}</tbody>`;
    }
    
    getCellValue(row, column) {
        let value = row[column.key];
        
        // Applica formatter se presente
        if (column.formatter && typeof column.formatter === 'function') {
            try {
                value = column.formatter(value, row);
            } catch (e) {
                console.error('Errore nel formatter della colonna', column.key, e);
                value = value;
            }
        }
        
        return value ?? '';
    }
    
    renderPagination() {
        const totalPages = Math.ceil(this.filteredData.length / this.options.pageSize);
        
        if (totalPages <= 1) {
            return ''; // Non mostrare paginazione se c'è solo una pagina
        }
        
        return `
            <div class="table-pagination">
                <button class="page-btn" data-page="prev" 
                        ${this.currentPage === 1 ? 'disabled' : ''}>
                    ◄
                </button>
                <span class="page-info">
                    Pagina ${this.currentPage} di ${totalPages}
                </span>
                <button class="page-btn" data-page="next" 
                        ${this.currentPage === totalPages ? 'disabled' : ''}>
                    ►
                </button>
            </div>
        `;
    }
    
    attachEventListeners() {
        // Sorting
        if (this.options.sortable) {
            this.container.querySelectorAll('th.sortable').forEach(th => {
                th.addEventListener('click', () => this.sort(th.dataset.column));
            });
        }
        
        // Filtering
        if (this.options.filterable) {
            const filterInput = this.container.querySelector('.filter-input');
            if (filterInput) {
                filterInput.addEventListener('input', (e) => this.filter(e.target.value));
            }
        }
        
        // Pagination
        if (this.options.paginated) {
            this.container.querySelectorAll('.page-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    const page = btn.dataset.page;
                    if (page === 'prev' && this.currentPage > 1) {
                        this.currentPage--;
                        this.render();
                    } else if (page === 'next') {
                        const totalPages = Math.ceil(this.filteredData.length / this.options.pageSize);
                        if (this.currentPage < totalPages) {
                            this.currentPage++;
                            this.render();
                        }
                    }
                });
            });
        }
    }
    
    sort(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'asc';
        }
        
        this.filteredData.sort((a, b) => {
            const aVal = a[column];
            const bVal = b[column];
            
            if (aVal === bVal) return 0;
            
            const result = aVal > bVal ? 1 : -1;
            return this.sortDirection === 'asc' ? result : -result;
        });
        
        this.currentPage = 1;
        this.render();
    }
    
    filter(searchTerm) {
        const term = searchTerm.toLowerCase();
        
        this.filteredData = this.data.filter(row => {
            return this.columns.some(col => {
                const value = String(row[col.key] || '').toLowerCase();
                return value.includes(term);
            });
        });
        
        this.currentPage = 1;
        this.render();
    }
    
    refresh() {
        this.render();
    }
    
    // Metodi di utilità per debugging
    getData() {
        return this.data;
    }
    
    getFilteredData() {
        return this.filteredData;
    }
}

// Export per uso modulare
window.ReusableTable = ReusableTable;