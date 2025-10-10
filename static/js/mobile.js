// Mobile App Main JavaScript

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/service-worker.js')
            .then(registration => {
                console.log('ServiceWorker registered:', registration);
            })
            .catch(err => {
                console.log('ServiceWorker registration failed:', err);
            });
    });
}

// PWA Install Prompt
let deferredPrompt;

window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    showInstallPromotion();
});

function showInstallPromotion() {
    const installPrompt = document.getElementById('installPrompt');
    if (installPrompt) {
        installPrompt.style.display = 'block';
    }
}

function installApp() {
    const installPrompt = document.getElementById('installPrompt');
    if (installPrompt) {
        installPrompt.style.display = 'none';
    }
    
    if (deferredPrompt) {
        deferredPrompt.prompt();
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install prompt');
            }
            deferredPrompt = null;
        });
    }
}

// Online/Offline Status
window.addEventListener('online', () => {
    hideOfflineIndicator();
    syncOfflineData();
});

window.addEventListener('offline', () => {
    showOfflineIndicator();
});

function showOfflineIndicator() {
    let indicator = document.getElementById('offlineIndicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'offlineIndicator';
        indicator.className = 'offline-indicator';
        indicator.textContent = '⚠️ You are offline';
        document.body.insertBefore(indicator, document.body.firstChild);
    }
}

function hideOfflineIndicator() {
    const indicator = document.getElementById('offlineIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// Sync offline data when back online
async function syncOfflineData() {
    const offlineQueue = JSON.parse(localStorage.getItem('offlineQueue') || '[]');
    
    for (const request of offlineQueue) {
        try {
            await fetch(request.url, {
                method: request.method,
                headers: request.headers,
                body: request.body
            });
        } catch (error) {
            console.error('Failed to sync request:', error);
        }
    }
    
    localStorage.setItem('offlineQueue', '[]');
}

// Check initial online status
if (!navigator.onLine) {
    showOfflineIndicator();
}

// Utility Functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const content = document.querySelector('.mobile-content');
    content.insertBefore(alertDiv, content.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

// API Helper
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        if (!navigator.onLine) {
            // Queue for later if offline
            const offlineQueue = JSON.parse(localStorage.getItem('offlineQueue') || '[]');
            offlineQueue.push({ url, ...options });
            localStorage.setItem('offlineQueue', JSON.stringify(offlineQueue));
            throw new Error('You are offline. Request will be sent when connection is restored.');
        }
        throw error;
    }
}