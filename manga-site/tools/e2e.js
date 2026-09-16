/* E2E-прогон MangaHub на jsdom: грузит реальные HTML-страницы, исполняет
   реальные скрипты сайта и кликает по реальным элементам.
   Запуск:  cd manga-site && node tools/e2e.js            (jsdom из ../../.e2e) */
"use strict";

const fs = require("fs");
const path = require("path");
const Module = require("module");

const ROOT = path.join(__dirname, "..");
/* jsdom ищется сначала в manga-site/node_modules, затем в соседней папке .e2e */
const CANDIDATES = [
  path.join(__dirname, "..", "node_modules"),
  path.join(__dirname, "..", "..", "..", ".e2e", "node_modules")
];
const NODE_MODULES = CANDIDATES.find((p) => fs.existsSync(path.join(p, "jsdom")));
if (!NODE_MODULES) {
  console.error("Не найден jsdom. Установите зависимости: cd manga-site && npm install");
  process.exit(1);
}
Module.globalPaths.push(NODE_MODULES);

const { JSDOM, VirtualConsole, ResourceLoader } = require(path.join(NODE_MODULES, "jsdom"));

let passed = 0;
let failed = 0;
const failures = [];

function check(name, cond, extra) {
  if (cond) { passed++; console.log("  ok    " + name); }
  else {
    failed++;
    console.log("  FAIL  " + name + (extra !== undefined ? "   -> " + extra : ""));
    failures.push(name);
  }
}
function section(t) { console.log("\n== " + t); }

function resetStorage() { sharedStore.clear(); }

class IO {
  constructor(cb) { this.cb = cb; }
  observe(el) { this.cb([{ isIntersecting: true, target: el }], this); }
  unobserve() {}
  disconnect() {}
  takeRecords() { return []; }
}

/* локальный статический сервер: нужен, чтобы jsdom работал с нормальным
   http-origin (localStorage для file:// недоступен) */
function startServer() {
  const http = require("http");
  const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8" };
  const server = http.createServer((req, res) => {
    let p = decodeURIComponent(req.url.split("?")[0]);
    if (p === "/") p = "/index.html";
    const file = path.join(ROOT, p);
    if (!file.startsWith(ROOT) || !fs.existsSync(file)) { res.writeHead(404); res.end("404"); return; }
    res.writeHead(200, { "Content-Type": MIME[path.extname(file)] || "application/octet-stream" });
    res.end(fs.readFileSync(file));
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve({ server, port: server.address().port })));
}

let BASE = "http://localhost:8000/";

/* В jsdom localStorage у каждого окна свой. Для сайта это один origin,
   поэтому подставляем общий бэкенд — иначе закладки/логин «не переживут»
   переход на другую страницу. */
const sharedStore = new Map();
function sharedStorage() {
  return {
    getItem: (k) => (sharedStore.has(String(k)) ? sharedStore.get(String(k)) : null),
    setItem: (k, v) => { sharedStore.set(String(k), String(v)); },
    removeItem: (k) => { sharedStore.delete(String(k)); },
    clear: () => { sharedStore.clear(); },
    key: (i) => [...sharedStore.keys()][i] ?? null,
    get length() { return sharedStore.size; }
  };
}

function makeDom(file, hash) {
  const html = fs.readFileSync(path.join(ROOT, file), "utf8");
  const vc = new VirtualConsole();
  const jsErrors = [];
  vc.on("jsdomError", (e) => {
    if (/not implemented/i.test(e.message)) return;
    jsErrors.push(e.message);
  });
  vc.on("error", (...a) => jsErrors.push(String(a.join(" "))));

  const dom = new JSDOM(html, {
    url: BASE + file + (hash || ""),
    beforeParse(w) {
      Object.defineProperty(w, "localStorage", { value: sharedStorage(), configurable: true });
    },
    runScripts: "dangerously",
    resources: "usable",                 // грузим локальные assets/js/*.js
    pretendToBeVisual: true,
    virtualConsole: vc
  });

  const w = dom.window;
  w.IntersectionObserver = IO;
  w.scrollTo = () => {};
  w.HTMLElement.prototype.scrollIntoView = () => {};
  w.navigator.clipboard = { writeText: () => Promise.resolve() };
  w.__jsErrors = jsErrors;
  w.__file = file;
  return dom;
}

/* ждём, пока jsdom подгрузит и выполнит локальные скрипты страницы */
async function openPage(file, hash, keepStorage) {
  const dom = makeDom(file, hash);
  const t0 = Date.now();
  while (Date.now() - t0 < 15000) {
    const w = dom.window;
    if (w.MANGA_DB && w.ML && w.document.querySelector("#page") &&
        w.document.querySelector("#page").innerHTML.trim().length > 0) {
      if (keepStorage !== false && !w.__storageKept) { /* хранилище общее для origin */ }
      return dom;
    }
    await sleep(25);
  }
  throw new Error("страница " + file + " не отрисовалась за 15 c");
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const click = (el) => {
  if (!el) throw new Error("клик по несуществующему элементу");
  return el.dispatchEvent(new el.ownerDocument.defaultView.MouseEvent("click", { bubbles: true, cancelable: true }));
};
const input = (el) => {
  if (!el) throw new Error("input по несуществующему элементу");
  return el.dispatchEvent(new el.ownerDocument.defaultView.Event("input", { bubbles: true }));
};
const change = (el) => {
  if (!el) throw new Error("change по несуществующему элементу");
  return el.dispatchEvent(new el.ownerDocument.defaultView.Event("change", { bubbles: true }));
};

async function main() {
  const srv = await startServer();
  BASE = "http://localhost:" + srv.port + "/";
  console.log("статический сервер: " + BASE);
  resetStorage();
  const clearStorage = () => {
    try { require(path.join(NODE_MODULES, "jsdom")); } catch (e) {}
  };


  /* ---------- Главная ---------- */
  section("index.html  #/");
  {
    const dom = await openPage("index.html", "#/");
    const d = dom.window.document;
    check("шапка отрисована", !!d.querySelector(".header-inner"));
    check("навигация из 6 пунктов", d.querySelectorAll(".main-nav a").length === 6,
      d.querySelectorAll(".main-nav a").length);
    check("слайдер: 6 слайдов", d.querySelectorAll(".hero-slide").length === 6,
      d.querySelectorAll(".hero-slide").length);
    check("первый слайд активен", d.querySelector(".hero-slide").classList.contains("active"));
    check("обложек-карточек >= 30", d.querySelectorAll(".card").length >= 30, d.querySelectorAll(".card").length);
    check("все обложки получили src", d.querySelectorAll("img[data-lazy]").length === 0 &&
      d.querySelectorAll("img[src^='data:image/svg+xml']").length > 10);
    check("топ-список >= 8", d.querySelectorAll(".side-card .side-item").length >= 8);
    check("футер отрисован", !!d.querySelector(".footer-grid"));
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    const href = d.querySelector(".card").getAttribute("href");
    check("ссылка карточки = #/manga/<slug>", /^#\/manga\/[a-z0-9-]+$/.test(href), href);
    dom.window.close();
  }

  /* ---------- Каталог ---------- */
  section("catalog.html  #/catalog");
  {
    const dom = await openPage("catalog.html", "#/catalog");
    const d = dom.window.document;
    check("сайдбар фильтров", !!d.querySelector(".filters"));
    check("групп фильтров = 6", d.querySelectorAll(".f-group").length === 6, d.querySelectorAll(".f-group").length);
    check("первая страница = 24 карточки", d.querySelectorAll("#results .card").length === 24,
      d.querySelectorAll("#results .card").length);
    check("пагинация", !!d.querySelector(".pagination"));

    const manhwa = [...d.querySelectorAll('input[data-field="types"]')].find((i) => i.value === "manhwa");
    click(manhwa);
    const badges = [...d.querySelectorAll("#results .badge")].map((b) => b.textContent.trim());
    check("фильтр «Манхва» оставляет только манхву",
      badges.length > 0 && badges.every((b) => b === "Манхва"), badges.slice(0, 6).join(","));
    check("чип активного фильтра", !!d.querySelector(".af-chip"));

    const genre = [...d.querySelectorAll('input[data-field="genres"]')].find((i) => i.value === "Романтика");
    click(genre);
    const after = d.querySelectorAll("#results .card").length;
    check("жанр+тип сузили выдачу", after > 0 && after < 24, after);

    const sel = d.querySelector("[data-sort]");
    sel.value = "rating";
    change(sel);
    check("сортировка не сломала выдачу", d.querySelectorAll("#results .card").length === after);

    click(d.querySelector(".af-chip button"));
    check("удаление чипа снимает фильтр", d.querySelectorAll("#results .card").length > after);

    click(d.querySelector("[data-clear]"));
    check("сброс → 24 карточки", d.querySelectorAll("#results .card").length === 24,
      d.querySelectorAll("#results .card").length);

    click(d.querySelectorAll(".view-toggle button")[1]);
    check("переключение на список", d.querySelectorAll("#results .row-card").length > 0);

    const page2 = d.querySelector('.pagination button[data-p="2"]');
    click(page2);
    const rowsP2 = d.querySelectorAll("#results .row-card").length;
    const activePage = d.querySelector(".pagination button.active");
    check("переход на 2-ю страницу", rowsP2 > 0 && activePage && activePage.textContent === "2",
      "строк=" + rowsP2 + ", active=" + (activePage ? activePage.textContent : "null"));

    const q = d.querySelector('[data-field="q"]');
    q.value = "zzz-нет-такого";
    input(q);
    await sleep(400);
    check("пустой поиск → заглушка", !!d.querySelector("#results .empty-state"));
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();
  }

  /* ---------- Каталог по ссылке с параметрами ---------- */
  section("catalog.html  #/catalog?type=manga&genres=Экшен");
  {
    const dom = await openPage("catalog.html", "#/catalog?type=manga&genres=" + encodeURIComponent("Экшен"));
    const d = dom.window.document;
    const badges = [...d.querySelectorAll("#results .badge")].map((b) => b.textContent.trim());
    check("из URL подхватился тип «Манга»",
      badges.length > 0 && badges.every((b) => b === "Манга"), badges.slice(0, 5).join(","));
    check("из URL подхватился жанр", (d.querySelector(".af-chip") || {}).textContent !== undefined &&
      d.querySelectorAll(".af-chip").length === 2, d.querySelectorAll(".af-chip").length);
    dom.window.close();
  }

  /* ---------- Страница тайтла ---------- */
  resetStorage();
  section("manga.html  #/manga/krov-titana");
  {
    const dom = await openPage("manga.html", "#/manga/krov-titana");
    const d = dom.window.document;
    const db = dom.window.MANGA_DB;
    const m = db.manga.find((x) => x.slug === "krov-titana");
    check("заголовок тайтла", d.querySelector(".manga-title").textContent === m.title,
      d.querySelector(".manga-title").textContent);
    check("жанров в шапке = " + m.genres.length,
      d.querySelectorAll(".manga-tags .chip").length === m.genres.length + 1,
      d.querySelectorAll(".manga-tags .chip").length);
    check("4 вкладки", d.querySelectorAll(".tab").length === 4);
    check("кнопка «Читать» ведёт в читалку",
      /^#\/manga\/krov-titana\/read\/\d+$/.test(d.querySelector(".manga-actions a.btn-primary").getAttribute("href")),
      d.querySelector(".manga-actions a.btn-primary").getAttribute("href"));
    check("похожие тайтлы", d.querySelectorAll(".side-list .side-item").length === 5);
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));

    // вкладка глав
    click([...d.querySelectorAll(".tab")].find((t) => t.dataset.tab === "chapters"));
    const rows = d.querySelectorAll(".chapter-row");
    check("список глав = " + m.chaptersCount, rows.length === m.chaptersCount, rows.length);
    check("первая строка — последняя глава",
      rows[0].querySelector(".num").textContent.trim() === "Гл. " + m.chapters[m.chaptersCount - 1].number,
      rows[0].querySelector(".num").textContent);

    click(d.querySelector("[data-order]"));
    const rowsAsc = d.querySelectorAll(".chapter-row");
    check("сортировка «сначала старые» меняет порядок",
      rowsAsc[0].querySelector(".num").textContent.trim() === "Гл. " + m.chapters[0].number,
      rowsAsc[0].querySelector(".num").textContent);

    const chq = d.querySelector("[data-chq]");
    chq.value = "Глава 5 ";
    input(chq);
    check("поиск по главам работает", d.querySelectorAll(".chapter-row").length === 1,
      d.querySelectorAll(".chapter-row").length);

    // вкладка комментариев
    click([...d.querySelectorAll(".tab")].find((t) => t.dataset.tab === "comments"));
    check("комментарии = " + m.comments.length, d.querySelectorAll(".comment").length === m.comments.length,
      d.querySelectorAll(".comment").length);
    check("форма заблокирована без входа", d.querySelector("[data-send]").disabled === true);

    // закладки
    click(d.querySelector("[data-fav2]"));
    check("закладка добавлена", JSON.parse(sharedStore.get("ml_favorites") || "[]").includes("krov-titana"),
      sharedStore.get("ml_favorites"));
    click(d.querySelector("[data-fav2]"));
    check("закладка убрана", !JSON.parse(sharedStore.get("ml_favorites") || "[]").includes("krov-titana"));

    // оценка
    click([...d.querySelectorAll("#stars button")].find((b) => b.dataset.v === "4"));
    check("оценка сохранена в localStorage", sharedStore.get("ml_votes_krov-titana") === "4",
      sharedStore.get("ml_votes_krov-titana"));
    check("нет ошибок JS после действий", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();
  }

  /* ---------- Читалка ---------- */
  resetStorage();
  section("reader.html  #/manga/krov-titana/read/1");
  {
    const dom = await openPage("reader.html", "#/manga/krov-titana/read/1");
    const d = dom.window.document;
    const m = dom.window.MANGA_DB.manga.find((x) => x.slug === "krov-titana");
    const ch1 = m.chapters.find((c) => c.number === "1");
    check("страниц в главе = " + ch1.pages, d.querySelectorAll("#pages img").length === ch1.pages,
      d.querySelectorAll("#pages img").length);
    check("страницы получили src", d.querySelectorAll("#pages img[data-lazy]").length === 0);
    check("номер главы в шапке", d.querySelector(".rt-title span").textContent.includes("Глава 1"));
    check("селектор глав = " + m.chaptersCount, d.querySelectorAll("#ch-select option").length === m.chaptersCount,
      d.querySelectorAll("#ch-select option").length);
    check("прогресс чтения записан",
      JSON.parse(sharedStore.get("ml_read_krov-titana") || "[]").includes("1"));
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));

    // настройки: постраничный режим
    click(d.querySelector("#rt-settings"));
    check("панель настроек открылась", !!d.querySelector(".reader-settings"));
    click([...d.querySelectorAll("[data-seg=mode] button")].find((b) => b.dataset.v === "paged"));
    check("режим «постранично» включён", d.querySelector("#pages").classList.contains("paged"));
    check("видна только одна страница", d.querySelectorAll("#pages img.current").length === 1);
    click(d.querySelector("[data-next-page]"));
    check("переход на 2-ю страницу", d.querySelectorAll("#pages img")[1].classList.contains("current"));
    const saved = JSON.parse(sharedStore.get("ml_readerSettings"));
    check("настройки сохранены", saved.mode === "paged", JSON.stringify(saved));

    // следующая глава
    const nextHref = [...d.querySelectorAll(".reader-bottom a")].map((a) => a.getAttribute("href"));
    check("есть ссылка на следующую главу", nextHref.some((h) => /read\/2$/.test(h)), nextHref.join(","));
    dom.window.close();
  }

  /* ---------- Избранное + вход ---------- */
  resetStorage();
  resetStorage();
  section("favorites.html  #/favorites");
  {
    // пустое состояние
    const empty = await openPage("favorites.html", "#/favorites");
    check("без закладок показывается заглушка", empty.window.document.body.innerHTML.includes("Закладок пока нет"));
    check("без истории показывается заглушка", empty.window.document.body.innerHTML.includes("Истории пока нет"));
    empty.window.close();

    // наполняем хранилище и открываем заново
    sharedStore.set("ml_favorites", JSON.stringify(["krov-titana", "povelitel-vozvrashchaetsya"]));
    sharedStore.set("ml_reading", JSON.stringify([{ slug: "krov-titana", chapter: "3", at: 1 }]));
    const dom = await openPage("favorites.html", "#/favorites");
    const d = dom.window.document;
    check("закладки отрисованы", d.querySelectorAll(".grid-cards .card").length === 3,
      d.querySelectorAll(".grid-cards .card").length); // 2 закладки + 1 в истории
    check("история чтения показывает главу 3", d.body.innerHTML.includes("гл. 3"));

    click(d.querySelector("#clear-history"));
    check("очистка истории сработала", sharedStore.get("ml_reading") === undefined,
      String(sharedStore.get("ml_reading")));
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();
  }

  section("login.html  #/login");
  {
    const dom = await openPage("login.html", "#/login");
    const d = dom.window.document;
    const form = d.querySelector("#auth-form");
    d.querySelector('[name="nick"]').value = "Тестер";
    d.querySelector('[name="pass"]').value = "1234";
    form.dispatchEvent(new dom.window.Event("submit", { bubbles: true, cancelable: true }));
    check("аккаунт создан", JSON.parse(sharedStore.get("ml_user")).nick === "Тестер",
      sharedStore.get("ml_user"));
    check("переход на избранное", dom.window.location.hash === "#/favorites", dom.window.location.hash);
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();

    const dom2 = await openPage("index.html", "#/");
    const d2 = dom2.window.document;
    check("в шапке появился ник пользователя", d2.querySelector(".user-chip") !== null &&
      d2.querySelector(".user-chip").textContent.includes("Тестер"), d2.querySelector(".user-chip")?.textContent);
    dom2.window.close();
  }

  /* ---------- Остальные страницы ---------- */
  const routes = [
    ["top.html", "#/top", ".chapter-row", "Топ: список тайтлов"],
    ["genres.html", "#/genres", ".genre-tile", "Жанры: плитки"],
    ["teams.html", "#/teams", ".team-card", "Команды: карточки"],
    ["about.html", "#/about", ".prose", "О проекте: текст"],
    ["feedback.html", "#/feedback", "#fb-form", "Обратная связь: форма"]
  ];
  for (const [file, hash, sel, label] of routes) {
    section(file + "  " + hash);
    const dom = await openPage(file, hash);
    const d = dom.window.document;
    check(label, d.querySelectorAll(sel).length > 0, d.querySelectorAll(sel).length);
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();
  }

  /* ---------- 404 и смена hash ---------- */
  section("роутинг: 404 и hashchange");
  {
    const dom = await openPage("index.html", "#/nesuschestvuet");
    const d = dom.window.document;
    check("несуществующий адрес → 404-блок", d.body.innerHTML.includes("Страница не найдена"));
    dom.window.location.hash = "#/genres";
    dom.window.dispatchEvent(new dom.window.Event("hashchange"));
    check("hashchange переключил страницу", d.querySelectorAll(".genre-tile").length > 0,
      d.querySelectorAll(".genre-tile").length);
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();
  }

  srv.server.close();
  console.log("\n----------------------------------------");
  console.log("Пройдено: " + passed + ", провалено: " + failed);
  if (failures.length) {
    console.log("Провалы:\n - " + failures.join("\n - "));
    process.exit(1);
  }
}

main().catch((e) => {
  console.error("\nТест упал: " + (e && e.message ? e.message : e));
  if (e && e.stack) console.error(e.stack.split("\n").slice(0, 6).join("\n"));
  process.exit(1);
});
