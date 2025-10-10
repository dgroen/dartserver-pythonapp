// Service Worker for PWA Offline Support

const CACHE_NAME = 'darts-mobile-v1';
const urlsToCache = [
    '/mobile',
    '/mobile/gameplay',
    '/mobile/gamemaster',
    '/mobile/dartboard-setup',
    '/mobile/results',
    '/mobile/account',
    '/mobile/hotspot',
    '/static/css/mobile.css',
    '/static/js/mobile.js',
    '/static/js/mobile_account.js',
    '/static/js/mobile_hotspot.js',
    '/static/js/mobile_dartboard_setup.js',
    '/static/js/mobile_gameplay.js',
    '/static/js/mobile_gamemaster.js',
    '/static/js/mobile_results.js',
    '/static/manifest.json'
];

// Install event - cache resources
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Opened cache');
                return cache.addAll(urlsToCache);
            })
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Cache hit - return response
                if (response) {
                    return response;
                }

                return fetch(event.request).then(
                    (response) => {
                        // Check if valid response
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }

                        // Clone the response
                        const responseToCache = response.clone();

                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(event.request, responseToCache);
                            });

                        return response;
                    }
                );
            })
            .catch(() => {
                // Return offline page if available
                return caches.match('/mobile');
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Background sync for offline requests
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-scores') {
        event.waitUntil(syncOfflineScores());
    }
});

async function syncOfflineScores() {
    // Get offline queue from IndexedDB or similar
    // Send queued requests to server
    console.log('Syncing offline scores...');
}

// Push notifications (for future use)
self.addEventListener('push', (event) => {
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        vibrate: [200, 100, 200]
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow('/mobile')
    );
});