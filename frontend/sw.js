const CACHE_NAME = 'slopeguard-v4';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/manifest.json',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png',
];

// Install event: cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.allSettled(
        ASSETS_TO_CACHE.map((url) => cache.add(url).catch((err) => console.warn('Cache failed for:', url, err)))
      );
    })
  );
  self.skipWaiting();
});

// Activate event: clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch event: network first, fallback to cache (same-origin only)
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;
  
  const url = new URL(event.request.url);
  // Do not intercept external map tiles (CartoDB, Esri, Mapzen) or external APIs
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request);
    })
  );
});

// Push event: receive Web Push and show notification
self.addEventListener('push', (event) => {
  let data = {
    title: '🚨 SLOPEGUARD EMERGENCY ALERT',
    body: 'Critical landslide risk detected in NE India. Evacuation protocols initiated.',
    url: '/'
  };
  
  if (event.data) {
    try {
      const parsed = event.data.json();
      if (parsed) data = Object.assign(data, parsed);
    } catch (e) {
      const txt = event.data.text();
      if (txt) data.body = txt;
    }
  }

  const title = data.title || '🚨 SLOPEGUARD EMERGENCY ALERT';
  const baseUrl = self.registration ? self.registration.scope : self.location.origin;
  const iconUrl = new URL('icons/icon-192x192.png', baseUrl).href;

  const options = {
    body: data.body || 'Critical landslide risk detected in NE India. Evacuation protocols initiated.',
    icon: iconUrl,
    badge: iconUrl,
    vibrate: [300, 100, 300, 100, 300],
    data: {
      url: data.url || '/'
    },
    tag: 'slopeguard-emergency-alert',
    renotify: true,
    requireInteraction: true
  };

  event.waitUntil(
    self.registration.showNotification(title, options).catch((err) => {
      console.error('showNotification failed in sw:', err);
    })
  );
});

// Notification click event: open the URL
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const urlToOpen = event.notification.data.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (let i = 0; i < windowClients.length; i++) {
        const client = windowClients[i];
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});
