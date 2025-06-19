/**
 * Utility di formattazione riusabili
 * Principio DRY - Don't Repeat Yourself
 */

const Formatters = {
    /**
     * Formatta numeri con separatori migliaia
     */
    number(value, decimals = 0) {
        if (value === null || value === undefined) return '-';
        return Number(value).toLocaleString('it-IT', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        });
    },
    
    /**
     * Formatta valuta
     */
    currency(value, currency = 'USD') {
        if (value === null || value === undefined) return '-';
        return new Intl.NumberFormat('it-IT', {
            style: 'currency',
            currency: currency
        }).format(value);
    },
    
    /**
     * Formatta percentuale
     */
    percentage(value, decimals = 2, showSign = true) {
        if (value === null || value === undefined) return '-';
        
        const formatted = Number(value).toFixed(decimals);
        const sign = showSign && value > 0 ? '+' : '';
        return `${sign}${formatted}%`;
    },
    
    /**
     * Formatta date
     */
    date(value, format = 'short') {
        if (!value) return '-';
        
        const date = new Date(value);
        
        switch (format) {
            case 'short':
                return date.toLocaleDateString('it-IT');
            case 'long':
                return date.toLocaleDateString('it-IT', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                });
            case 'iso':
                return date.toISOString().split('T')[0];
            case 'time':
                return date.toLocaleTimeString('it-IT');
            case 'datetime':
                return date.toLocaleString('it-IT');
            default:
                return date.toLocaleDateString('it-IT');
        }
    },
    
    /**
     * Formatta volumi (K, M, B)
     */
    volume(value) {
        if (value === null || value === undefined) return '-';
        
        const num = Number(value);
        
        if (num >= 1e9) {
            return (num / 1e9).toFixed(1) + 'B';
        } else if (num >= 1e6) {
            return (num / 1e6).toFixed(1) + 'M';
        } else if (num >= 1e3) {
            return (num / 1e3).toFixed(1) + 'K';
        }
        
        return num.toString();
    },
    
    /**
     * Formatta bytes (KB, MB, GB)
     */
    bytes(value) {
        if (value === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(value) / Math.log(k));
        
        return parseFloat((value / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    /**
     * Formatta durata (secondi in formato leggibile)
     */
    duration(seconds) {
        if (!seconds) return '0s';
        
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        const parts = [];
        if (hours > 0) parts.push(`${hours}h`);
        if (minutes > 0) parts.push(`${minutes}m`);
        if (secs > 0 || parts.length === 0) parts.push(`${secs}s`);
        
        return parts.join(' ');
    },
    
    /**
     * Tronca testo
     */
    truncate(text, length = 50, suffix = '...') {
        if (!text) return '';
        if (text.length <= length) return text;
        return text.substring(0, length) + suffix;
    },
    
    /**
     * Capitalizza prima lettera
     */
    capitalize(text) {
        if (!text) return '';
        return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase();
    },
    
    /**
     * Formatta range di date
     */
    dateRange(startDate, endDate) {
        const start = this.date(startDate);
        const end = this.date(endDate);
        return `${start} - ${end}`;
    },
    
    /**
     * Calcola e formatta variazione percentuale
     */
    priceChange(oldPrice, newPrice) {
        if (!oldPrice || !newPrice) return '-';
        
        const change = ((newPrice - oldPrice) / oldPrice) * 100;
        const formatted = this.percentage(change, 2, true);
        
        const className = change > 0 ? 'positive' : change < 0 ? 'negative' : 'neutral';
        
        return `<span class="${className}">${formatted}</span>`;
    }
};

// Rendi disponibile globalmente
window.formatters = Formatters;