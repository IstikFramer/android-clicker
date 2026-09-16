const series = [
  {
    id: "neon-afterglow",
    title: "Neon Afterglow",
    author: "Rin Aoki",
    genre: "sci-fi",
    image: "assets/cover-neon-afterglow.png",
    rating: "4.9",
    chapters: 36,
    year: 2026,
    description: { ru: "Город после дождя всё ещё светится.", en: "The city still glows after the rain." },
  },
  {
    id: "glass-orchard",
    title: "Glass Orchard",
    author: "Mika Vale",
    genre: "fantasy",
    image: "assets/cover-glass-orchard.png",
    rating: "4.8",
    chapters: 18,
    year: 2026,
    description: { ru: "Тишина тоже умеет расти.", en: "Silence knows how to grow." },
  },
  {
    id: "signal-zero",
    title: "Signal / Zero",
    author: "K. Nara",
    genre: "sci-fi",
    image: "assets/cover-signal-zero.png",
    rating: "4.9",
    chapters: 36,
    year: 2025,
    description: { ru: "Последний поезд слышит их сигнал.", en: "The last train hears their signal." },
  },
  {
    id: "paper-moon",
    title: "Paper Moon",
    author: "Yui Sato",
    genre: "slice",
    image: "assets/cover-paper-moon.png",
    rating: "4.7",
    chapters: 12,
    year: 2026,
    description: { ru: "Маленькая комната. Большая ночь.", en: "A small room. A very big night." },
  },
  {
    id: "dusk-protocol",
    title: "Dusk Protocol",
    author: "Mori / 404",
    genre: "action",
    image: "assets/cover-dusk-protocol.png",
    rating: "4.6",
    chapters: 24,
    year: 2024,
    description: { ru: "У каждого сбоя есть причина.", en: "Every glitch has a reason." },
  },
];

const copy = {
  ru: {
    nav: { catalog: "Каталог", trending: "В тренде", library: "Моя полка", about: "О проекте" },
    auth: { login: "Войти", title: "Вернись к своим историям.", description: "Сохрани прогресс и собери личную полку без лишних шагов.", email: "Email", password: "Пароль", submit: "Войти в демо", disclaimer: "Демо-форма — аккаунт не создаётся." },
    search: { kicker: "БЫСТРЫЙ ПОИСК", placeholder: "Название, автор или тег" },
    hero: { eyebrow: "LIVE DISCOVERY / 02", titleOne: "Читай за", titleAccent: "полшага", titleTwo: "впереди.", description: "MangaLive собирает истории, которые хочется открыть прямо сейчас — от тихой slice of life до вселенных, где всё вот-вот взорвётся.", primary: "Открыть каталог", surprise: "Удиви меня", note: "Без бесконечного скролла. Только хорошие совпадения.", pulse: "Пульс читателей", quote: "Включила первую главу — и пропала на три часа." },
    metrics: { label: "СЕЙЧАС НА MANGALIVE", description: "Лента, которая знает, где ты остановился — и что открыть дальше.", readers: "активных читателей", series: "серий в каталоге", finish: "заканчивают начатое" },
    trending: { title: "В тренде у своих", signal: "Два курьера. Один последний поезд. И сигнал, который не должен был дойти.", orchard: "Тишина тоже умеет расти.", paper: "Маленькая комната. Большая ночь." },
    common: { seeAll: "Смотреть всё", read: "Читать", chapters: "глав" },
    catalog: { title: "Найди свою следующую obsession", sortLabel: "Сортировка", sortPopular: "По популярности", sortNew: "Сначала новые", sortRating: "По рейтингу", filter: "Фильтр", genre: "Жанр", reset: "Сбросить", emptyTitle: "Ничего не потерялось — просто ищем иначе.", emptyText: "Попробуй другой запрос или сбрось фильтры." },
    genres: { all: "Все", action: "Экшен", fantasy: "Фэнтези", slice: "Повседневность", scifi: "Sci-fi" },
    library: { titleOne: "Твоя полка.", titleTwo: "Твои правила.", description: "Сохрани историю, которую хочется дочитать. MangaLive запомнит страницу, настроение и тот самый «ещё одну главу».", cta: "Открыть мою полку" },
    about: { titleOne: "Не просто ридер.", titleTwo: "Место для открытия.", description: "Мы собираем каталог как зин: немного хаоса, много характера и ноль безликих рекомендаций. Каждый экран MangaLive помогает выбрать историю быстрее и остаться в ней дольше." },
    footer: { note: "Сделано для тех, кто говорит «последняя глава» и не имеет это в виду." },
    reader: { tip: "Демо-режим: страницы переключаются, а твой прогресс сохраняется в браузере.", previous: "Назад", next: "Следующая", finish: "Закончить", chapter: "Глава" },
    toast: { saved: "Добавлено на полку", removed: "Убрано с полки", login: "Добро пожаловать в демо MangaLive", reset: "Фильтры сброшены", surprise: "Случайный выбор готов" },
    result: { showing: "Показаны", stories: "историй", library: "В полке", noLibrary: "Полка пока пуста" },
  },
  en: {
    nav: { catalog: "Catalog", trending: "Trending", library: "My shelf", about: "The idea" },
    auth: { login: "Sign in", title: "Come back to your stories.", description: "Save your progress and build a personal shelf without the extra steps.", email: "Email", password: "Password", submit: "Enter demo", disclaimer: "Demo form — no account is created." },
    search: { kicker: "QUICK SEARCH", placeholder: "Title, author or tag" },
    hero: { eyebrow: "LIVE DISCOVERY / 02", titleOne: "Read half a", titleAccent: "step", titleTwo: "ahead.", description: "MangaLive collects stories you want to open right now — from quiet slice of life to universes one spark away from blowing up.", primary: "Open catalog", surprise: "Surprise me", note: "No endless scrolling. Only good coincidences.", pulse: "Reader pulse", quote: "I opened chapter one — and vanished for three hours." },
    metrics: { label: "RIGHT NOW ON MANGALIVE", description: "A feed that knows where you stopped — and what to open next.", readers: "active readers", series: "series in catalog", finish: "finish what they start" },
    trending: { title: "Trending with the in-crowd", signal: "Two couriers. One last train. And a signal that should never have arrived.", orchard: "Silence knows how to grow.", paper: "A small room. A very big night." },
    common: { seeAll: "See all", read: "Read", chapters: "chapters" },
    catalog: { title: "Find your next obsession", sortLabel: "Sort", sortPopular: "Most popular", sortNew: "Newest first", sortRating: "Top rated", filter: "Filter", genre: "Genre", reset: "Reset", emptyTitle: "Nothing is lost — we are just looking differently.", emptyText: "Try another query or reset your filters." },
    genres: { all: "All", action: "Action", fantasy: "Fantasy", slice: "Slice of life", scifi: "Sci-fi" },
    library: { titleOne: "Your shelf.", titleTwo: "Your rules.", description: "Save the story you want to finish. MangaLive remembers your page, your mood, and that classic ‘one more chapter’ moment.", cta: "Open my shelf" },
    about: { titleOne: "Not just a reader.", titleTwo: "A place to discover.", description: "We curate the catalog like a zine: a little chaos, lots of character and zero bland recommendations. Every MangaLive screen helps you choose faster and stay longer." },
    footer: { note: "Made for people who say ‘last chapter’ and never mean it." },
    reader: { tip: "Demo mode: pages switch here, and your progress is saved in the browser.", previous: "Previous", next: "Next", finish: "Finish", chapter: "Chapter" },
    toast: { saved: "Added to your shelf", removed: "Removed from your shelf", login: "Welcome to the MangaLive demo", reset: "Filters reset", surprise: "A random pick is ready" },
    result: { showing: "Showing", stories: "stories", library: "In shelf", noLibrary: "Your shelf is empty" },
  },
};

const state = {
  language: "ru",
  genre: "all",
  search: "",
  sort: "popular",
  view: "grid",
  libraryOnly: false,
  favorites: loadFavorites(),
};

const $ = (selector, scope = document) => scope.querySelector(selector);
const $$ = (selector, scope = document) => [...scope.querySelectorAll(selector)];
const t = (key) => key.split(".").reduce((value, part) => value?.[part], copy[state.language]);

function loadFavorites() {
  try {
    const saved = JSON.parse(localStorage.getItem("mangalive-favorites") || "[]");
    return Array.isArray(saved) ? saved : [];
  } catch {
    return [];
  }
}

function persistFavorites() {
  try { localStorage.setItem("mangalive-favorites", JSON.stringify(state.favorites)); } catch { /* private mode */ }
}

function applyLanguage(language) {
  state.language = language;
  document.documentElement.lang = language;
  $$('[data-language]').forEach((button) => button.classList.toggle("is-active", button.dataset.language === language));
  $$('[data-i18n]').forEach((element) => {
    const value = t(element.dataset.i18n);
    if (value !== undefined) element.textContent = value;
  });
  $$('[data-i18n-placeholder]').forEach((element) => {
    const value = t(element.dataset.i18nPlaceholder);
    if (value !== undefined) element.placeholder = value;
  });
  renderCatalog();
  renderReader();
}

function getGenreLabel(genre) {
  const key = { all: "genres.all", action: "genres.action", fantasy: "genres.fantasy", slice: "genres.slice", "sci-fi": "genres.scifi" }[genre];
  return t(key) || genre;
}

function getVisibleSeries() {
  const query = state.search.trim().toLowerCase();
  let visible = series.filter((item) => {
    const matchesGenre = state.genre === "all" || item.genre === state.genre;
    const matchesLibrary = !state.libraryOnly || state.favorites.includes(item.id);
    const searchPool = `${item.title} ${item.author} ${item.genre} ${getGenreLabel(item.genre)} ${item.description.ru} ${item.description.en}`.toLowerCase();
    return matchesGenre && matchesLibrary && (!query || searchPool.includes(query));
  });

  if (state.sort === "new") visible.sort((a, b) => b.year - a.year);
  if (state.sort === "rating") visible.sort((a, b) => Number(b.rating) - Number(a.rating));
  if (state.sort === "popular") visible.sort((a, b) => Number(b.rating) - Number(a.rating) || b.chapters - a.chapters);
  return visible;
}

function bookmarkSvg() {
  return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.5 4.5A1.5 1.5 0 0 1 8 3h8a1.5 1.5 0 0 1 1.5 1.5V21l-5.5-3.4L6.5 21V4.5Z"></path></svg>';
}

function renderCatalog() {
  const grid = $("#catalogGrid");
  const empty = $("#emptyState");
  if (!grid || !empty) return;
  const visible = getVisibleSeries();
  grid.classList.toggle("is-list", state.view === "list");
  grid.innerHTML = visible.map((item, index) => {
    const isSaved = state.favorites.includes(item.id);
    const indexLabel = String(index + 1).padStart(2, "0");
    return `
      <article class="manga-card" data-series-card="${item.id}">
        <div class="manga-art">
          <img src="${item.image}" alt="${item.title} cover" loading="lazy" />
          <span class="art-index">${indexLabel} / 05</span>
          <button class="save-btn ${isSaved ? "is-saved" : ""}" type="button" data-save="${item.id}" aria-label="${isSaved ? "Remove" : "Save"} ${item.title}" aria-pressed="${isSaved}">${bookmarkSvg()}</button>
        </div>
        <div class="manga-info">
          <div class="card-top"><span>${getGenreLabel(item.genre)}</span><span class="rating">★ ${item.rating}</span></div>
          <h3 title="${item.title}">${item.title}</h3>
          <p>${item.description[state.language]}</p>
          <div class="card-footer"><span class="card-chapters">${item.chapters} ${t("common.chapters")}</span><button class="card-read" type="button" data-read="${item.id}">${t("common.read")} ↗</button></div>
        </div>
      </article>`;
  }).join("");
  empty.hidden = visible.length !== 0;

  const result = $("#catalogResultText");
  if (result) {
    if (state.libraryOnly && state.favorites.length === 0) result.textContent = t("result.noLibrary");
    else result.textContent = `${state.libraryOnly ? t("result.library") : t("result.showing")} ${visible.length} ${t("result.stories")}`;
  }
  const activeFilters = (state.genre !== "all" ? 1 : 0) + (state.libraryOnly ? 1 : 0);
  const filterCount = $("#filterCount");
  if (filterCount) {
    filterCount.textContent = activeFilters;
    filterCount.classList.toggle("is-visible", activeFilters > 0);
  }
}

function showToast(message) {
  const toast = $("#toast");
  const text = $("#toastText");
  if (!toast || !text) return;
  text.textContent = message;
  toast.classList.add("is-visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove("is-visible"), 2600);
}

function toggleFavorite(id) {
  const existing = state.favorites.includes(id);
  state.favorites = existing ? state.favorites.filter((item) => item !== id) : [...state.favorites, id];
  persistFavorites();
  renderCatalog();
  showToast(t(existing ? "toast.removed" : "toast.saved"));
  if (readerState.id === id) updateReaderSaveState();
}

const readerState = { id: "neon-afterglow", page: 0 };
const readerPages = (item) => [
  { src: item.image, caption: "THE CITY NEVER SLEEPS", position: "center" },
  { src: "assets/hero-bg.png", caption: "KEEP WALKING / KEEP LOOKING", position: "center" },
  { src: "assets/noise-texture-bg.png", caption: "TO BE CONTINUED", position: "center" },
];

function renderReader() {
  const item = series.find((entry) => entry.id === readerState.id) || series[0];
  const pages = readerPages(item);
  const page = pages[readerState.page] || pages[0];
  const title = $("#readerTitle");
  const meta = $("#readerMeta");
  const seriesName = $("#readerSeries");
  const number = $("#readerPageNumber");
  const image = $("#readerPageImage");
  const caption = $("#readerPageCaption");
  const progress = $("#readerProgress");
  const prev = $("#readerPrev");
  const next = $("#readerNext");
  if (!title || !image) return;
  title.textContent = item.title;
  meta.textContent = `${t("reader.chapter")} ${String(readerState.page + 1).padStart(2, "0")} / 03`;
  seriesName.textContent = item.title.toUpperCase();
  number.textContent = String(readerState.page + 1).padStart(2, "0");
  image.src = page.src;
  image.alt = `${item.title} reader page ${readerState.page + 1}`;
  image.style.objectPosition = page.position;
  caption.textContent = page.caption;
  progress.style.width = `${((readerState.page + 1) / pages.length) * 100}%`;
  prev.disabled = readerState.page === 0;
  const nextLabel = $("#readerNext span");
  if (nextLabel) nextLabel.textContent = readerState.page === pages.length - 1 ? t("reader.finish") : t("reader.next");
  updateReaderSaveState();
}

function updateReaderSaveState() {
  const button = $("#readerSave");
  if (!button) return;
  const saved = state.favorites.includes(readerState.id);
  button.classList.toggle("is-saved", saved);
  button.setAttribute("aria-pressed", String(saved));
}

function openReader(id) {
  if (!series.some((item) => item.id === id)) return;
  readerState.id = id;
  readerState.page = 0;
  renderReader();
  openModal("readerModal");
}

function openModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.add("is-open");
  modal.setAttribute("aria-hidden", "false");
  document.body.classList.add("is-locked");
  const focusable = modal.querySelector("button, input");
  window.setTimeout(() => focusable?.focus(), 30);
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (!modal) return;
  modal.classList.remove("is-open");
  modal.setAttribute("aria-hidden", "true");
  if (!$$('.modal.is-open').length) document.body.classList.remove("is-locked");
}

function closeAllModals() {
  $$('.modal.is-open').forEach((modal) => closeModal(modal.id));
}

function scrollToCatalog({ library = false } = {}) {
  state.libraryOnly = library;
  state.search = "";
  const input = $("#globalSearch");
  if (input) input.value = "";
  renderCatalog();
  $("#catalog")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function resetFilters() {
  state.genre = "all";
  state.search = "";
  state.libraryOnly = false;
  state.sort = "popular";
  $("#sortSelect").value = "popular";
  $("#globalSearch").value = "";
  $$(".chip").forEach((chip) => chip.classList.toggle("is-selected", chip.dataset.genre === "all"));
  renderCatalog();
  showToast(t("toast.reset"));
}

// General click delegation keeps cards rendered from data interactive.
document.addEventListener("click", (event) => {
  const readButton = event.target.closest("[data-read]");
  if (readButton) {
    event.preventDefault();
    openReader(readButton.dataset.read);
    return;
  }

  const saveButton = event.target.closest("[data-save]");
  if (saveButton) {
    event.preventDefault();
    toggleFavorite(saveButton.dataset.save);
    return;
  }

  const closeButton = event.target.closest("[data-close-modal]");
  if (closeButton) {
    closeModal(closeButton.dataset.closeModal);
    return;
  }

  const filterLink = event.target.closest("[data-filter]");
  if (filterLink) {
    event.preventDefault();
    scrollToCatalog();
    return;
  }
});

$$("[data-language]").forEach((button) => button.addEventListener("click", () => applyLanguage(button.dataset.language)));

$("#searchTrigger")?.addEventListener("click", () => {
  const drawer = $("#searchDrawer");
  const open = drawer.classList.toggle("is-open");
  drawer.setAttribute("aria-hidden", String(!open));
  if (open) window.setTimeout(() => $("#globalSearch")?.focus(), 120);
});

$("#globalSearch")?.addEventListener("input", (event) => {
  state.search = event.target.value;
  renderCatalog();
});
$("#globalSearch")?.addEventListener("keydown", (event) => {
  if (event.key === "Enter") $("#catalog")?.scrollIntoView({ behavior: "smooth", block: "start" });
});

$("#filterToggle")?.addEventListener("click", () => {
  const panel = $("#filterPanel");
  const open = panel.classList.toggle("is-open");
  panel.setAttribute("aria-hidden", String(!open));
});
$$(".chip").forEach((chip) => chip.addEventListener("click", () => {
  state.genre = chip.dataset.genre;
  state.libraryOnly = false;
  $$(".chip").forEach((entry) => entry.classList.toggle("is-selected", entry === chip));
  renderCatalog();
}));
$("#sortSelect")?.addEventListener("change", (event) => { state.sort = event.target.value; renderCatalog(); });
$("#resetFilters")?.addEventListener("click", resetFilters);
$("#emptyReset")?.addEventListener("click", resetFilters);

$$("[data-view]").forEach((button) => button.addEventListener("click", () => {
  state.view = button.dataset.view;
  $$("[data-view]").forEach((entry) => entry.classList.toggle("is-selected", entry === button));
  renderCatalog();
}));

$("#surpriseMe")?.addEventListener("click", () => {
  const pick = series[Math.floor(Math.random() * series.length)];
  showToast(`${t("toast.surprise")}: ${pick.title}`);
  window.setTimeout(() => openReader(pick.id), 340);
});

$("#openLibrary")?.addEventListener("click", () => scrollToCatalog({ library: true }));

$("#menuToggle")?.addEventListener("click", () => {
  const menu = $(".main-nav");
  const open = menu.classList.toggle("is-open");
  $("#menuToggle").setAttribute("aria-expanded", String(open));
});
$$(".nav-link").forEach((link) => link.addEventListener("click", (event) => {
  $$(".nav-link").forEach((item) => item.classList.toggle("is-active", item === link));
  $(".main-nav")?.classList.remove("is-open");
  $("#menuToggle")?.setAttribute("aria-expanded", "false");
  if (link.dataset.nav === "library") {
    event.preventDefault();
    scrollToCatalog({ library: true });
  }
  if (link.dataset.nav === "catalog") {
    state.libraryOnly = false;
    renderCatalog();
  }
}));

$("#openAuth")?.addEventListener("click", () => openModal("authModal"));
$("#footerLogin")?.addEventListener("click", () => openModal("authModal"));
$("#fakeLogin")?.addEventListener("click", () => {
  closeModal("authModal");
  showToast(t("toast.login"));
});

$("#readerPrev")?.addEventListener("click", () => {
  if (readerState.page > 0) { readerState.page -= 1; renderReader(); }
});
$("#readerNext")?.addEventListener("click", () => {
  if (readerState.page < readerPages(series.find((item) => item.id === readerState.id)).length - 1) {
    readerState.page += 1;
    renderReader();
  } else {
    closeModal("readerModal");
    showToast(t("toast.saved"));
  }
});
$("#readerSave")?.addEventListener("click", () => toggleFavorite(readerState.id));
$("#readerPlay")?.addEventListener("click", () => showToast(t("toast.surprise")));

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closeAllModals();
    $("#searchDrawer")?.classList.remove("is-open");
    $("#searchDrawer")?.setAttribute("aria-hidden", "true");
    $(".main-nav")?.classList.remove("is-open");
  }
  if ($("#readerModal")?.classList.contains("is-open")) {
    if (event.key === "ArrowRight") $("#readerNext")?.click();
    if (event.key === "ArrowLeft") $("#readerPrev")?.click();
  }
});

const observedSections = ["catalog", "trending", "library", "about"].map((id) => document.getElementById(id)).filter(Boolean);
const navObserver = new IntersectionObserver((entries) => {
  const visible = entries.filter((entry) => entry.isIntersecting).sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
  if (!visible) return;
  $$(".nav-link").forEach((link) => link.classList.toggle("is-active", link.dataset.nav === visible.target.id));
}, { rootMargin: "-30% 0px -60%", threshold: [0.05, 0.2, 0.5] });
observedSections.forEach((section) => navObserver.observe(section));

applyLanguage("ru");
