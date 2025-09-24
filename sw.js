const CACHE_NAME = "antropophag-cache-v2";
const STATIC_ASSETS = [
  "/",
  "/index.html",
  "/favicon-16x16.png",
  "/favicon-32x32.png",
  "/favicon-512x512.png",
  "/fonts/foundation-icons.css",
  "/dice.gif"
];

self.addEventListener("install", event => {
  console.log("[SW] Установка сервис-воркера...");
  event.waitUntil(
    caches.open(CACHE_NAME).then(async cache => {
      for (const url of STATIC_ASSETS) {
        try { 
          await cache.add(url); 
          console.log("[SW] Закеширован:", url);
        } catch(e){ 
          console.warn("[SW] Не удалось закешировать", url); 
        }
      }
      self.skipWaiting();
    })
  );
});

self.addEventListener("activate", event => {
  console.log("[SW] Активация сервис-воркера...");
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => key !== CACHE_NAME ? caches.delete(key) : null)
      ).then(() => self.clients.claim())
    )
  );
});

// Cache First только для статики, JSON грузим напрямую
self.addEventListener("fetch", event => {
  if (event.request.url.includes('/data/games.json')) return; // игнорируем JSON
  event.respondWith(
    caches.match(event.request).then(cached => {
      return cached || fetch(event.request).then(resp => {
        if(resp.ok){
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, resp.clone()));
        }
        return resp;
      }).catch(() => cached);
    })
  );
});
