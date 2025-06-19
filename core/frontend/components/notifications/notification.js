/**
 * Sistema di notifiche riusabile
 * Principio: Single Responsibility - gestisce solo le notifiche
 */
class NotificationSystem {
    constructor() {
        this.container = null;
        this.notifications = [];
        this.init();
    }
    
    init() {
        // Crea container se non esiste
        if (!document.getElementById('notification-container')) {
            this.container = document.createElement('div');
            this.container.id = 'notification-container';
            this.container.className = 'notification-container';
            document.body.appendChild(this.container);
        } else {
            this.container = document.getElementById('notification-container');
        }
    }
    
    show(message, type = 'info', duration = 5000) {
        const id = Date.now();
        const notification = {
            id,
            message,
            type,
            duration
        };
        
        this.notifications.push(notification);
        this.render(notification);
        
        if (duration > 0) {
            setTimeout(() => this.remove(id), duration);
        }
        
        return id;
    }
    
    render(notification) {
        const notifElement = document.createElement('div');
        notifElement.className = `notification notification-${notification.type}`;
        notifElement.id = `notification-${notification.id}`;
        notifElement.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">${this.getIcon(notification.type)}</span>
                <span class="notification-message">${notification.message}</span>
            </div>
            <button class="notification-close" onclick="window.notifications.remove(${notification.id})">
                ×
            </button>
        `;
        
        this.container.appendChild(notifElement);
        
        // Trigger animation
        setTimeout(() => {
            notifElement.classList.add('notification-show');
        }, 10);
    }
    
    getIcon(type) {
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };
        return icons[type] || icons.info;
    }
    
    remove(id) {
        const notifElement = document.getElementById(`notification-${id}`);
        if (notifElement) {
            notifElement.classList.remove('notification-show');
            setTimeout(() => {
                notifElement.remove();
                this.notifications = this.notifications.filter(n => n.id !== id);
            }, 300);
        }
    }
    
    // Metodi di convenienza
    success(message, duration) {
        return this.show(message, 'success', duration);
    }
    
    error(message, duration) {
        return this.show(message, 'error', duration);
    }
    
    warning(message, duration) {
        return this.show(message, 'warning', duration);
    }
    
    info(message, duration) {
        return this.show(message, 'info', duration);
    }
    
    clear() {
        this.notifications.forEach(notif => this.remove(notif.id));
    }
}

// Inizializza sistema notifiche globale
window.notifications = new NotificationSystem();