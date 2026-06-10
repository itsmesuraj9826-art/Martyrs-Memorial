/* ============================================================
   service-worker.js — Martyrs' Memorial +2 PWA
   Strategy: Cache-first for assets, Network-first for pages
   ============================================================ */

const CACHE_NAME    = 'mm-plus2-v1';
const OFFLINE_PAGE  = '/offline';

// Assets to pre-cache on install (shell)
const PRECACHE = [
  '/',
  '/about',
  '/academics',
  '/see-result',
  '/contact',
  '/static/css/main.css',
  '/static/css/public.css',
  '/static/js/main.js',
  '/static/img/logo.svg',
  '/static/img/favicon-32.png',
];

// ── Install: pre-cache shell ──────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())
  );
});

// ── Activate: clean old caches ────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    ).then(() => self.clients.claim())
  );
});

// ── Fetch: serve from cache, fall back to network ─────────
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET, admin, auth, cross-origin
  if (request.method !== 'GET') return;
  if (url.pathname.startsWith('/admin')) return;
  if (url.pathname.startsWith('/auth')) return;
  if (url.origin !== self.location.origin) return;

  // CSS/JS/images → cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached =>
        cached || fetch(request).then(response => {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(c => c.put(request, clone));
          return response;
        })
      )
    );
    return;
  }

  // HTML pages → network-first, fall back to cache, then offline page
  event.respondWith(
    fetch(request)
      .then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(c => c.put(request, clone));
        return response;
      })
      .catch(() =>
        caches.match(request).then(cached =>
          cached || caches.match(OFFLINE_PAGE) || new Response(
            '<h1>You are offline</h1><p>Please check your connection.</p>',
            { headers: { 'Content-Type': 'text/html' } }
          )
        )
      )
  );
});
