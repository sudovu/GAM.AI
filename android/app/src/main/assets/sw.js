// GAM.AI Offline Service Worker
const CACHE_NAME = 'gam-ai-cache-v3';
self.addEventListener('install', (e) => {
  self.skipWaiting();
});
self.addEventListener('activate', (e) => {
  e.waitUntil(clients.claim());
});
self.addEventListener('fetch', (e) => {
  // Let network handle API, fallback to cache for offline static assets
  if (e.request.url.includes('/api/')) {
    return;
  }
});
