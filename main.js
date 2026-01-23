document.addEventListener("DOMContentLoaded", () => {
  let isRussia = false;
  let countryDetectionComplete = false;

  async function detectCountry() {
    try {
      const response = await fetch("https://ipinfo.io/json");
      const data = await response.json();

      isRussia = data.country === "RU";
      console.log(
        "Страна пользователя:",
        data.country,
        isRussia ? "(Россия)" : "(Не Россия)",
      );
    } catch (error) {
      console.log(
        "Не удалось определить страну через ipinfo.io. Используем weserv.nl по умолчанию.",
        error,
      );
      isRussia = false;
    } finally {
      countryDetectionComplete = true;
    }
  }

  function getRatingColor(avg) {
    if (avg > 7.9) return "#186b40";
    if (avg > 6.9) return "#1978b3";
    if (avg > 4.9) return "#5369a2";
    return "#666e75";
  }

  function getColumnCount() {
    if (window.innerWidth < 600) return 2;
    if (window.innerWidth < 900) return 3;
    if (window.innerWidth < 2000) return 4;
    return 5;
  }

  const fullImageObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;

        const img = entry.target;
        if (img.dataset.fullLoaded) return;

        const fullImg = new Image();
        fullImg.decoding = "async";
        fullImg.src = img.dataset.full;

        fullImg.onload = () => {
          img.src = img.dataset.full;
          img.dataset.fullLoaded = "1";
        };

        fullImageObserver.unobserve(img);
      });
    },
    { rootMargin: "200px" },
  );

  function createGameDiv(game, container) {
    const div = document.createElement("div");
    div.className = "game";

    const ratingColor = getRatingColor(game.average);

    let weightColor = "#5bda98";
    if (game.averageweight > 4) weightColor = "#df4751";
    else if (game.averageweight > 3) weightColor = "#ff6b26";

    const rank = game.overallrank ?? "—";

    const dpr = window.devicePixelRatio || 1;
    const colWidth = Math.ceil(
      (container.clientWidth / getColumnCount()) * dpr,
    );

    const thumbSource = game.thumbnail || game.image;
    const thumbWidth = Math.min(colWidth, 320);

    if (!isRussia) {
      domain = "images.weserv.nl";
    } else {
      domain = "img.alchemmist.xyz";
    }

    let thumbUrl, fullUrl;
    thumbUrl = `https://${domain}/?url=${encodeURIComponent(thumbSource)}&w=${thumbWidth}&q=80&output=webp`;
    fullUrl = `https://${domain}/?url=${encodeURIComponent(game.image)}&w=${colWidth}&q=90&output=webp`;

    div.innerHTML = `
            <img
              src="${thumbUrl}"
              data-full="${fullUrl}"
              loading="lazy"
              decoding="async"
              alt="${game.name}"
            >
            <div class="overlay">
              <div class="overlay-content">
                <div class="rating-hex" style="background-color:${ratingColor}">
                  ${game.average.toFixed(1)}
                </div>
                <div class="title-rank">
                  <div class="title">
                    <a href="${game.url}" target="_blank">${game.name}</a>
                  </div>
                  <div class="rank"><i class="fi-crown"></i> ${rank}</div>
                </div>
              </div>
              <div class="info">
                <p><i class="fi-torso"></i> ${game.minplayers}–${game.maxplayers}</p>
                <p><i class="fi-clock"></i> ${game.playingtime} min</p>
                <p>
                  <i class="fi-puzzle"></i>
                  <span style="color:${weightColor}">
                    ${game.averageweight !== null ? game.averageweight.toFixed(2) : "N/A"}
                  </span> / 5
                </p>
              </div>
              <div class="info-column">
                <p>Players: ${game.minplayers}–${game.maxplayers}</p>
                <p>Playing time: ${game.playingtime} min</p>
                <p>
                  Complexity:
                  <span style="color:${weightColor}">
                    ${game.averageweight !== null ? game.averageweight.toFixed(2) : "N/A"}
                  </span> / 5
                </p>
              </div>
            </div>
          `;

    const img = div.querySelector("img");

    fullImageObserver.observe(img);

    return div;
  }

  function layoutMasonry(container) {
    const colCount = getColumnCount();
    const colWidth = container.clientWidth / colCount;

    container.querySelectorAll(".game").forEach((el) => {
      el.style.width = colWidth + "px";
    });

    return new Masonry(container, {
      itemSelector: ".game",
      columnWidth: colWidth,
      gutter: 0,
      transitionDuration: "0.4s",
    });
  }

  async function loadGames(file, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;

    try {
      const response = await fetch(file);
      const data = await response.json();

      const games =
        data[
          containerId === "ownMosaic"
            ? "own"
            : containerId === "preMosaic"
              ? "preordered"
              : "wishlist"
        ];

      games.forEach((game) => {
        container.appendChild(createGameDiv(game, container));
      });

      return new Promise((resolve) => {
        imagesLoaded(container, () => {
          const msnry = layoutMasonry(container);

          container.querySelectorAll(".game").forEach((el, i) => {
            setTimeout(() => el.classList.add("show"), 80 * i);
          });

          resolve(msnry);
        });
      });
    } catch (error) {
      console.error("Ошибка загрузки игр:", error);
      return null;
    }
  }

  async function loadAll() {
    document.getElementById("loadingIndicator").style.display = "block";

    await detectCountry();

    try {
      const [ownMsnry, preMsnry, wishMsnry] = await Promise.all([
        loadGames("data/games.json", "ownMosaic"),
        loadGames("data/games.json", "preMosaic"),
        loadGames("data/games.json", "wishMosaic"),
      ]);

      document.getElementById("loader")?.remove();
      document.getElementById("loadingIndicator").style.display = "none";

      function handleResize() {
        const containers = [
          {
            msnry: ownMsnry,
            container: document.getElementById("ownMosaic"),
          },
          {
            msnry: preMsnry,
            container: document.getElementById("preMosaic"),
          },
          {
            msnry: wishMsnry,
            container: document.getElementById("wishMosaic"),
          },
        ];

        containers.forEach(({ msnry, container }) => {
          if (msnry && container) {
            const newColWidth = container.clientWidth / getColumnCount();
            container.querySelectorAll(".game").forEach((el) => {
              el.style.width = newColWidth + "px";
            });
            msnry.options.columnWidth = newColWidth;
            msnry.layout();
          }
        });
      }

      let resizeTimeout;
      window.addEventListener("resize", () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(handleResize, 250);
      });
    } catch (error) {
      console.error("Ошибка при загрузке всех данных:", error);
      document.getElementById("loader")?.remove();
      document.getElementById("loadingIndicator").style.display = "none";
    }
  }

  loadAll();
});
