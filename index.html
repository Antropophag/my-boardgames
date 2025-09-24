const CACHE_NAME = "antropophag-cache-v1";

// Что кэшируем сразу (иконки, стили, скрипты)
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
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
});

// Удаляем старые кэши при обновлении
self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.map(key => key !== CACHE_NAME && caches.delete(key)))
    )
  );
});

// Стратегия: Cache First с обновлением из сети
self.addEventListener("fetch", event => {
  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      const fetchPromise = fetch(event.request).then(networkResponse => {
        if (networkResponse.ok) {
          caches.open(CACHE_NAME).then(cache =>
            cache.put(event.request, networkResponse.clone())
          );
        }
        return networkResponse;
      }).catch(() => cachedResponse);

      return cachedResponse || fetchPromise;
    })
  );
});
