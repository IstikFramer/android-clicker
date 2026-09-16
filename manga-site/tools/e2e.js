/* E2E-прогон MangaHub на jsdom: грузит реальные HTML-страницы, исполняет
   реальные скрипты сайта и кликает по реальным элементам.
   Запуск:  cd manga-site && npm test   (нужен jsdom: npm install) */
"use strict";

const fs = require("fs");
const path = require("path");
const Module = require("module");

const ROOT = path.join(__dirname, "..");
const CANDIDATES = [
  path.join(ROOT, "node_modules"),
  path.join(__dirname, "..", "..", "..", ".e2e", "node_modules")
];
const NODE_MODULES = CANDIDATES.find((p) => fs.existsSync(path.join(p, "jsdom")));
if (!NODE_MODULES) {
  console.error("Не найден jsdom. Установите зависимости: cd manga-site && npm install");
  process.exit(1);
}
Module.globalPaths.push(NODE_MODULES);

const { JSDOM, VirtualConsole } = require(path.join(NODE_MODULES, "jsdom"));

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
  const MIME = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".jpg": "image/jpeg" };
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
   поэтому подставляем общий бэкенд. */
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
function resetStorage() { sharedStore.clear(); }

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
    resources: "usable",
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

async function openPage(file, hash) {
  const dom = makeDom(file, hash);
  const t0 = Date.now();
  while (Date.now() - t0 < 15000) {
    const w = dom.window;
    if (w.MANGA_DB && w.ML && w.document.querySelector("#page") &&
        w.document.querySelector("#page").innerHTML.trim().length > 0) return dom;
    await sleep(25);
  }
  throw new Error("страница " + file + " не отрисовалась за 15 c");
}

const SLUG = "poezd-v-742";

async function main() {
  const srv = await startServer();
  BASE = "http://localhost:" + srv.port + "/";
  console.log("статический сервер: " + BASE);

  /* ---------- Главная ---------- */
  section("index.html  #/");
  {
    const dom = await openPage("index.html", "#/");
    const d = dom.window.document;
    const db = dom.window.MANGA_DB;
    check("шапка отрисована", !!d.querySelector(".header-inner"));
    check("слайдер: 1 слайд с реальным тайтлом", d.querySelectorAll(".hero-slide").length === db.manga.length,
      d.querySelectorAll(".hero-slide").length);
    check("обложка в слайдере — реальный файл", d.querySelector(".hero-cover").getAttribute("src") === db.manga[0].cover,
      d.querySelector(".hero-cover").getAttribute("src"));
    check("карточки секций отрисованы", d.querySelectorAll(".card").length >= 4, d.querySelectorAll(".card").length);
    check("обложки карточек — реальные файлы", [...d.querySelectorAll(".card img")].every((i) => (i.getAttribute("src") || "").startsWith("assets/img/")),
      d.querySelector(".card img") && d.querySelector(".card img").getAttribute("src"));
    check("футер отрисован", !!d.querySelector(".footer-grid"));
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();
  }

  /* ---------- Каталог ---------- */
  section("catalog.html  #/catalog");
  {
    const dom = await openPage("catalog.html", "#/catalog");
    const d = dom.window.document;
    check("групп фильтров = 6", d.querySelectorAll(".f-group").length === 6);
    check("в каталоге 1 тайтл", d.querySelectorAll("#results .card").length === 1,
      d.querySelectorAll("#results .card").length);
    check("пагинации нет (тайтл один)", !d.querySelector(".pagination"));

    const manhwa = [...d.querySelectorAll('input[data-field="types"]')].find((i) => i.value === "manhwa");
    click(manhwa);
    check("фильтр «Манхва» даёт пустую выдачу", !!d.querySelector("#results .empty-state"));
    click(d.querySelector("[data-clear]"));
    check("сброс возвращает тайтл", d.querySelectorAll("#results .card").length === 1);

    const genre = [...d.querySelectorAll('input[data-field="genres"]')].find((i) => i.value === "Романтика");
    click(genre);
    check("жанр «Романтика» оставляет тайтл", d.querySelectorAll("#results .card").length === 1);

    const act = [...d.querySelectorAll('input[data-field="genres"]')].find((i) => i.value === "Экшен");
    click(act);
    check("несовместимые жанры → пусто", !!d.querySelector("#results .empty-state"));
    click(d.querySelector("[data-clear]"));
    const hits = () => d.querySelectorAll("#results .card").length + d.querySelectorAll("#results .row-card").length;

    click(d.querySelectorAll(".view-toggle button")[1]);
    check("режим списка работает", d.querySelectorAll("#results .row-card").length === 1);

    const q = d.querySelector('[data-field="q"]');
    q.value = "zzz-нет-такого";
    input(q);
    await sleep(400);
    check("пустой поиск → заглушка", !!d.querySelector("#results .empty-state"));

    q.value = "7:42";
    input(q);
    await sleep(400);
    check("поиск «7:42» находит тайтл", hits() === 1, hits());
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();
  }

  /* ---------- Каталог с параметрами из URL ---------- */
  section("catalog.html  #/catalog?type=manga&genres=Школа");
  {
    const dom = await openPage("catalog.html", "#/catalog?type=manga&genres=" + encodeURIComponent("Школа"));
    const d = dom.window.document;
    check("из URL подхватились фильтры", d.querySelectorAll(".af-chip").length === 2,
      d.querySelectorAll(".af-chip").length);
    check("тайтл найден", d.querySelectorAll("#results .card").length + d.querySelectorAll("#results .row-card").length === 1,
      d.querySelectorAll("#results .card").length + "/" + d.querySelectorAll("#results .row-card").length);
    dom.window.close();
  }

  /* ---------- Страница тайтла ---------- */
  resetStorage();
  section("manga.html  #/manga/" + SLUG);
  {
    const dom = await openPage("manga.html", "#/manga/" + SLUG);
    const d = dom.window.document;
    const m = dom.window.MANGA_DB.manga[0];
    check("заголовок тайтла", d.querySelector(".manga-title").textContent === m.title,
      d.querySelector(".manga-title").textContent);
    check("обложка — реальный файл", d.querySelector(".manga-cover").getAttribute("src") === m.cover);
    check("4 вкладки", d.querySelectorAll(".tab").length === 4);
    check("кнопка «Читать» ведёт в читалку",
      d.querySelector(".manga-actions a.btn-primary").getAttribute("href") === "#/manga/" + SLUG + "/read/1",
      d.querySelector(".manga-actions a.btn-primary").getAttribute("href"));
    check("похожих пока нет — заглушка", d.body.innerHTML.includes("Пока не собрались похожие тайтлы"));
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));

    click([...d.querySelectorAll(".tab")].find((t) => t.dataset.tab === "chapters"));
    const rows = d.querySelectorAll(".chapter-row");
    check("список глав = 1", rows.length === 1, rows.length);
    check("строка — глава 1", rows[0].querySelector(".num").textContent.trim() === "Гл. 1",
      rows[0].querySelector(".num").textContent);

    click([...d.querySelectorAll(".tab")].find((t) => t.dataset.tab === "comments"));
    check("комментариев = " + m.comments.length, d.querySelectorAll(".comment").length === m.comments.length,
      d.querySelectorAll(".comment").length);
    check("форма заблокирована без входа", d.querySelector("[data-send]").disabled === true);

    click(d.querySelector("[data-fav2]"));
    check("закладка добавлена", JSON.parse(sharedStore.get("ml_favorites")).includes(SLUG));
    click([...d.querySelectorAll("#stars button")].find((b) => b.dataset.v === "5"));
    check("оценка сохранена", sharedStore.get("ml_votes_" + SLUG) === "5");
    check("нет ошибок JS после действий", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();
  }

  /* ---------- Читалка ---------- */
  resetStorage();
  section("reader.html  #/manga/" + SLUG + "/read/1");
  {
    const dom = await openPage("reader.html", "#/manga/" + SLUG + "/read/1");
    const d = dom.window.document;
    const m = dom.window.MANGA_DB.manga[0];
    const pagesCount = m.chapters[0].pages.length;
    check("страниц в главе = " + pagesCount, d.querySelectorAll("#pages img").length === pagesCount,
      d.querySelectorAll("#pages img").length);
    check("страницы ссылаются на реальные файлы",
      [...d.querySelectorAll("#pages img")].every((i) => i.getAttribute("data-url").startsWith("assets/img/")),
      d.querySelector("#pages img").getAttribute("data-url"));
    check("ленивая загрузка подставила src", d.querySelector("#pages img").getAttribute("src").endsWith("p01.jpg"),
      d.querySelector("#pages img").getAttribute("src"));
    check("номер главы в шапке", d.querySelector(".rt-title span").textContent.includes("Глава 1"));
    check("селектор глав = 1", d.querySelectorAll("#ch-select option").length === 1);
    check("последняя глава — кнопка-заглушка", d.body.innerHTML.includes("Это последняя глава"));
    check("прогресс чтения записан", JSON.parse(sharedStore.get("ml_read_" + SLUG)).includes("1"));
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));

    click(d.querySelector("#rt-settings"));
    check("панель настроек открылась", !!d.querySelector(".reader-settings"));
    click([...d.querySelectorAll("[data-seg=mode] button")].find((b) => b.dataset.v === "paged"));
    check("постраничный режим включён", d.querySelector("#pages").classList.contains("paged"));
    check("видна одна страница", d.querySelectorAll("#pages img.current").length === 1);
    click(d.querySelector("[data-next-page]"));
    check("переход на 2-ю страницу", d.querySelectorAll("#pages img")[1].classList.contains("current"));
    const saved = JSON.parse(sharedStore.get("ml_readerSettings"));
    check("настройки сохранены", saved.mode === "paged");
    dom.window.close();
  }

  /* ---------- Избранное ---------- */
  resetStorage();
  section("favorites.html  #/favorites");
  {
    const empty = await openPage("favorites.html", "#/favorites");
    check("без закладок — заглушка", empty.window.document.body.innerHTML.includes("Закладок пока нет"));
    empty.window.close();

    sharedStore.set("ml_favorites", JSON.stringify([SLUG]));
    sharedStore.set("ml_reading", JSON.stringify([{ slug: SLUG, chapter: "1", at: 1 }]));
    const dom = await openPage("favorites.html", "#/favorites");
    const d = dom.window.document;
    check("закладка и история отрисованы", d.querySelectorAll(".grid-cards .card").length === 2,
      d.querySelectorAll(".grid-cards .card").length);
    click(d.querySelector("#clear-history"));
    check("очистка истории сработала", sharedStore.get("ml_reading") === undefined);
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();
  }

  /* ---------- Вход ---------- */
  section("login.html  #/login");
  {
    const dom = await openPage("login.html", "#/login");
    const d = dom.window.document;
    d.querySelector('[name="nick"]').value = "Тестер";
    d.querySelector('[name="pass"]').value = "1234";
    d.querySelector("#auth-form").dispatchEvent(new dom.window.Event("submit", { bubbles: true, cancelable: true }));
    check("аккаунт создан", JSON.parse(sharedStore.get("ml_user")).nick === "Тестер");
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();

    const dom2 = await openPage("index.html", "#/");
    check("ник в шапке", dom2.window.document.querySelector(".user-chip").textContent.includes("Тестер"));
    dom2.window.close();
  }

  /* ---------- Остальные страницы ---------- */
  const routes = [
    ["top.html", "#/top", ".genre-tile", null, (d) => d.querySelectorAll(".card").length >= 1, "Топ: подиум с тайтлом"],
    ["genres.html", "#/genres", null, null, (d) => d.querySelectorAll(".genre-tile").length === 30, "Жанры: 30 плиток"],
    ["genres.html", "#/genres", null, null, (d) => d.querySelectorAll(".grid-cards .card").length === 1, "Жанры: топ-секция по «Романтике»"],
    ["teams.html", "#/teams", null, null, (d) => d.querySelectorAll(".team-card").length === 1, "Команды: 1 карточка"],
    ["about.html", "#/about", null, null, (d) => d.body.innerHTML.includes("Поезд в 7:42"), "О проекте: упоминается тайтл"],
    ["feedback.html", "#/feedback", null, null, (d) => !!d.querySelector("#fb-form"), "Обратная связь: форма"]
  ];
  for (const [file, hash, , , testFn, label] of routes) {
    section(file + "  " + hash);
    const dom = await openPage(file, hash);
    check(label, testFn(dom.window.document));
    check("нет ошибок JS", dom.window.__jsErrors.length === 0, dom.window.__jsErrors.join(" | "));
    dom.window.close();
  }

  /* ---------- 404 и hashchange ---------- */
  section("роутинг: 404 и hashchange");
  {
    const dom = await openPage("index.html", "#/nesuschestvuet");
    const d = dom.window.document;
    check("несуществующий адрес → 404", d.body.innerHTML.includes("Страница не найдена"));
    dom.window.location.hash = "#/manga/" + SLUG;
    dom.window.dispatchEvent(new dom.window.Event("hashchange"));
    check("hashchange переключил на тайтл", !!d.querySelector(".manga-title"));
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
