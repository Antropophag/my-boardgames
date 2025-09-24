const CACHE_NAME = "antropophag-cache-v1";

const STATIC_ASSETS = [
  "/",
  "/index.html",
  "/favicon-16x16.png",
  "/favicon-32x32.png",
  "/favicon-512x512.png",
  "/fonts/foundation-icons.css",
  "/dice.gif"
];

// Установка сервис-воркера и кеширование файлов с логированием
self.addEventListener("install", event => {
  console.log("[SW] Установка сервис-воркера...");
  event.waitUntil(
    caches.open(CACHE_NAME).then(async cache => {
      let cachedCount = 0;
      for (const url of STATIC_ASSETS) {
        try {
          await cache.add(url);
          cachedCount++;
          console.log(`[SW] Закеширован (${cachedCount}/${STATIC_ASSETS.length}):`, url);
        } catch (err) {
          console.warn("[SW] Не удалось закешировать:", url, err);
        }
      }
      console.log("[SW] Установка завершена.");
      self.skipWaiting(); // активируем новый SW сразу
    })
  );
});

// Активация сервис-воркера и удаление старых кэшей
self.addEventListener("activate", event => {
  console.log("[SW] Активация сервис-воркера...");
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.map(key => {
          if (key !== CACHE_NAME) {
            console.log("[SW] Удаляем старый кэш:", key);
            return caches.delete(key);
          }
        })
      ).then(() => {
        console.log("[SW] Активация завершена.");
        return self.clients.claim(); // контролируем все вкладки сразу
      })
    )
  );
});

// Стратегия Cache First с обновлением сети
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
