/* CarScraping Service Worker
 * Progressive Web App offline capabilities and caching
 */

const CACHE_NAME = 'carscraping-v1.0.0';
const STATIC_CACHE_NAME = 'carscraping-static-v1.0.0';
const DATA_CACHE_NAME = 'carscraping-data-v1.0.0';

// Resources to cache for offline functionality
const STATIC_RESOURCES = [
    '/',
    '/static/css/dashboard.css',
    '/static/css/charts.css',
    '/static/css/components.css',
    '/static/css/responsive.css',
    '/static/js/main.js',
    '/static/js/app.js',
    '/static/js/charts/price-trend.js',
    '/static/manifest.json',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.js',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap'
];

// API endpoints that should be cached
const API_CACHE_PATTERNS = [
    /\/api\/cars\/filters\//,
    /\/api\/searches\//,
    /\/api\/analytics\//,
    /\/api\/charts\//
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker: Installing...');
    
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE_NAME).then((cache) => {
                console.log('📦 Service Worker: Caching static resources');
                return cache.addAll(STATIC_RESOURCES);
            }),
            caches.open(DATA_CACHE_NAME).then((cache) => {
                console.log('📊 Service Worker: Data cache initialized');
                return cache;
            })
        ]).then(() => {
            console.log('✅ Service Worker: Installation complete');
            // Force activation of new service worker
            return self.skipWaiting();
        }).catch((error) => {
            console.error('❌ Service Worker: Installation failed', error);
        })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    // Delete old caches
                    if (cacheName !== STATIC_CACHE_NAME && 
                        cacheName !== DATA_CACHE_NAME &&
                        cacheName !== CACHE_NAME) {
                        console.log('🗑️ Service Worker: Deleting old cache', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('✅ Service Worker: Activation complete');
            // Take control of all pages immediately
            return self.clients.claim();
        })
    );
});

// Fetch event - handle network requests
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Only handle GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Handle different types of requests
    if (isStaticResource(url)) {
        event.respondWith(handleStaticResource(request));
    } else if (isAPIRequest(url)) {
        event.respondWith(handleAPIRequest(request));
    } else if (isHTMLRequest(request)) {
        event.respondWith(handleHTMLRequest(request));
    }
});

// Check if request is for a static resource
function isStaticResource(url) {
    return url.pathname.startsWith('/static/') ||
           url.hostname !== self.location.hostname ||
           url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.js') ||
           url.pathname.endsWith('.png') ||
           url.pathname.endsWith('.jpg') ||
           url.pathname.endsWith('.svg') ||
           url.pathname.endsWith('.woff') ||
           url.pathname.endsWith('.woff2');
}

// Check if request is for API data
function isAPIRequest(url) {
    return url.pathname.startsWith('/api/') ||
           API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname));
}

// Check if request is for HTML
function isHTMLRequest(request) {
    return request.headers.get('Accept')?.includes('text/html');
}

// Handle static resource requests (Cache First strategy)
async function handleStaticResource(request) {
    try {
        // Try cache first
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Fallback to network
        const response = await fetch(request);
        
        // Cache successful responses
        if (response.status === 200) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, response.clone());
        }
        
        return response;
        
    } catch (error) {
        console.error('❌ Service Worker: Static resource fetch failed', error);
        
        // Return cached version if available
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline fallback
        return createOfflineResponse();
    }
}

// Handle API requests (Network First with cache fallback)
async function handleAPIRequest(request) {
    try {
        // Try network first for fresh data
        const response = await fetch(request);
        
        if (response.status === 200) {
            // Cache successful API responses
            const cache = await caches.open(DATA_CACHE_NAME);
            cache.put(request, response.clone());
            
            // Notify clients of new data
            notifyClientsOfUpdate(request.url);
        }
        
        return response;
        
    } catch (error) {
        console.log('🔄 Service Worker: Network failed, trying cache for', request.url);
        
        // Fallback to cached data
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            // Add offline indicator header
            const modifiedResponse = new Response(cachedResponse.body, {
                status: cachedResponse.status,
                statusText: cachedResponse.statusText,
                headers: {
                    ...cachedResponse.headers,
                    'X-Served-By': 'service-worker-cache',
                    'X-Cache-Date': cachedResponse.headers.get('date') || new Date().toISOString()
                }
            });
            
            return modifiedResponse;
        }
        
        // Return offline API response
        return createOfflineAPIResponse(request);
    }
}

// Handle HTML requests (Network First with offline fallback)
async function handleHTMLRequest(request) {
    try {
        const response = await fetch(request);
        return response;
        
    } catch (error) {
        console.log('🔄 Service Worker: Serving offline page');
        
        // Return cached main page or offline page
        const cachedResponse = await caches.match('/');
        if (cachedResponse) {
            return cachedResponse;
        }
        
        return createOfflinePage();
    }
}

// Create offline response for static resources
function createOfflineResponse() {
    return new Response('Offline - Resource not available', {
        status: 503,
        statusText: 'Service Unavailable',
        headers: {
            'Content-Type': 'text/plain',
            'X-Served-By': 'service-worker-offline'
        }
    });
}

// Create offline API response
function createOfflineAPIResponse(request) {
    const url = new URL(request.url);
    
    // Return appropriate offline data structure
    let offlineData = {};
    
    if (url.pathname.includes('/analytics')) {
        offlineData = {
            total_cars: 0,
            price_stats: { avg_price: 0, min_price: 0, max_price: 0 },
            mileage_stats: {
                range_0_50k: { avg_price: 0, count: 0 },
                range_50_100k: { avg_price: 0, count: 0 },
                range_100k_plus: { avg_price: 0, count: 0 }
            },
            offline: true
        };
    } else if (url.pathname.includes('/charts')) {
        offlineData = {
            dates: [],
            overall: [],
            by_mileage: { low: [], medium: [], high: [] },
            statistics: { average: 0, change_percentage: 0, volatility: 0 },
            offline: true
        };
    } else if (url.pathname.includes('/cars')) {
        offlineData = [];
    } else {
        offlineData = { offline: true, message: 'Data not available offline' };
    }
    
    return new Response(JSON.stringify(offlineData), {
        status: 200,
        headers: {
            'Content-Type': 'application/json',
            'X-Served-By': 'service-worker-offline'
        }
    });
}

// Create offline HTML page
function createOfflinePage() {
    const offlineHTML = `
        <!DOCTYPE html>
        <html lang="it">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>CarScraping - Offline</title>
            <style>
                body {
                    font-family: 'Inter', sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #1e3a8a, #3b82f6);
                    color: white;
                    text-align: center;
                }
                .offline-container {
                    max-width: 400px;
                    padding: 2rem;
                }
                .offline-icon {
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }
                .offline-title {
                    font-size: 1.5rem;
                    margin-bottom: 1rem;
                    font-weight: 600;
                }
                .offline-message {
                    font-size: 1rem;
                    margin-bottom: 2rem;
                    opacity: 0.9;
                }
                .retry-button {
                    background: rgba(255, 255, 255, 0.2);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    color: white;
                    padding: 0.75rem 1.5rem;
                    border-radius: 0.5rem;
                    cursor: pointer;
                    font-size: 1rem;
                    transition: background 0.3s;
                }
                .retry-button:hover {
                    background: rgba(255, 255, 255, 0.3);
                }
            </style>
        </head>
        <body>
            <div class="offline-container">
                <div class="offline-icon">🚗</div>
                <div class="offline-title">CarScraping</div>
                <div class="offline-message">
                    Sei attualmente offline. Alcuni dati potrebbero non essere aggiornati.
                </div>
                <button class="retry-button" onclick="window.location.reload()">
                    Riprova
                </button>
            </div>
        </body>
        </html>
    `;
    
    return new Response(offlineHTML, {
        status: 200,
        headers: {
            'Content-Type': 'text/html',
            'X-Served-By': 'service-worker-offline'
        }
    });
}

// Notify clients of data updates
function notifyClientsOfUpdate(url) {
    self.clients.matchAll().then((clients) => {
        clients.forEach((client) => {
            client.postMessage({
                type: 'DATA_UPDATE',
                url: url,
                timestamp: Date.now()
            });
        });
    });
}

// Handle background sync for data updates
self.addEventListener('sync', (event) => {
    if (event.tag === 'background-sync-cars') {
        event.waitUntil(backgroundSyncCars());
    }
});

// Background sync for car data
async function backgroundSyncCars() {
    try {
        console.log('🔄 Service Worker: Background sync for car data');
        
        const response = await fetch('/api/analytics/');
        if (response.ok) {
            const cache = await caches.open(DATA_CACHE_NAME);
            cache.put('/api/analytics/', response.clone());
            
            notifyClientsOfUpdate('/api/analytics/');
        }
        
    } catch (error) {
        console.error('❌ Service Worker: Background sync failed', error);
    }
}

// Handle push notifications
self.addEventListener('push', (event) => {
    if (!event.data) return;
    
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/images/icons/icon-192x192.png',
        badge: '/static/images/icons/icon-72x72.png',
        data: data.data,
        actions: [
            {
                action: 'view',
                title: 'Visualizza',
                icon: '/static/images/icons/action-view.png'
            },
            {
                action: 'dismiss',
                title: 'Ignora',
                icon: '/static/images/icons/action-dismiss.png'
            }
        ],
        requireInteraction: true,
        tag: data.tag || 'default'
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    if (event.action === 'view') {
        const urlToOpen = event.notification.data?.url || '/';
        
        event.waitUntil(
            self.clients.matchAll({ type: 'window' }).then((clients) => {
                // Check if there's already a window open
                for (let client of clients) {
                    if (client.url === urlToOpen && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Open new window
                if (self.clients.openWindow) {
                    return self.clients.openWindow(urlToOpen);
                }
            })
        );
    }
});

// Handle messages from clients
self.addEventListener('message', (event) => {
    const { type, data } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'GET_VERSION':
            event.ports[0].postMessage({
                version: CACHE_NAME,
                timestamp: Date.now()
            });
            break;
            
        case 'CLEAR_CACHE':
            clearAllCaches().then(() => {
                event.ports[0].postMessage({ success: true });
            });
            break;
            
        default:
            console.log('Unknown message type:', type);
    }
});

// Clear all caches
async function clearAllCaches() {
    const cacheNames = await caches.keys();
    await Promise.all(
        cacheNames.map(cacheName => caches.delete(cacheName))
    );
    console.log('🗑️ Service Worker: All caches cleared');
}