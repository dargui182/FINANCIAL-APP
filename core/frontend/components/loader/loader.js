/**
 * Componente Loader riusabile
 * Gestisce indicatori di caricamento
 */
class LoaderManager {
    constructor() {
        this.activeLoaders = new Map();
    }
    
    show(id = 'default', options = {}) {
        const config = {
            text: 'Caricamento...',
            overlay: false,
            size: 'medium',
            ...options
        };
        
        // Se esiste già, rimuovi
        if (this.activeLoaders.has(id)) {
            this.hide(id);
        }
        
        const loader = this.createLoader(config);
        
        if (config.overlay) {
            // Crea overlay
            const overlay = document.createElement('div');
            overlay.className = 'loader-overlay';
            overlay.id = `loader-overlay-${id}`;
            overlay.appendChild(loader);
            document.body.appendChild(overlay);
        } else if (config.container) {
            // Inserisci in container specifico
            const container = document.querySelector(config.container);
            if (container) {
                loader.id = `loader-${id}`;
                container.appendChild(loader);
            }
        }
        
        this.activeLoaders.set(id, { element: loader, config });
    }
    
    createLoader(config) {
        const wrapper = document.createElement('div');
        wrapper.className = `loader-wrapper loader-${config.size}`;
        
        wrapper.innerHTML = `
            <div class="loader-spinner">
                <div class="spinner-ring"></div>
            </div>
            ${config.text ? `<div class="loader-text">${config.text}</div>` : ''}
        `;
        
        return wrapper;
    }
    
    hide(id = 'default') {
        const loader = this.activeLoaders.get(id);
        if (loader) {
            if (loader.config.overlay) {
                const overlay = document.getElementById(`loader-overlay-${id}`);
                if (overlay) {
                    overlay.remove();
                }
            } else {
                loader.element.remove();
            }
            this.activeLoaders.delete(id);
        }
    }
    
    hideAll() {
        this.activeLoaders.forEach((_, id) => this.hide(id));
    }
    
    // Metodi di convenienza
    showOverlay(text = 'Caricamento...') {
        this.show('overlay', {
            text,
            overlay: true,
            size: 'large'
        });
    }
    
    hideOverlay() {
        this.hide('overlay');
    }
    
    // Loader inline per form/pulsanti
    showInline(selector, text = '') {
        const element = document.querySelector(selector);
        if (element) {
            const id = `inline-${Date.now()}`;
            const originalContent = element.innerHTML;
            
            element.disabled = true;
            element.innerHTML = `
                <span class="inline-loader">
                    <span class="spinner-small"></span>
                    ${text || originalContent}
                </span>
            `;
            
            this.activeLoaders.set(id, {
                element,
                originalContent,
                isInline: true
            });
            
            return id;
        }
    }
    
    hideInline(id) {
        const loader = this.activeLoaders.get(id);
        if (loader && loader.isInline) {
            loader.element.innerHTML = loader.originalContent;
            loader.element.disabled = false;
            this.activeLoaders.delete(id);
        }
    }
}

// Crea istanza globale
window.loader = new LoaderManager();