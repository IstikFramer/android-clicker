/* МангаЛайф — логика сайта (вебтун-версия, 2 тайтла + 18+) */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

/* ---------- Тема день/ночь (по умолчанию светлая) ---------- */
function initTheme() {
  const btn = $("#themeToggle");
  const apply = (t) => {
    document.documentElement.dataset.theme = t;
    if (btn) {
      btn.innerHTML = t === "dark"
        ? '<svg class="ic"><use href="#i-sun"/></svg>'
        : '<svg class="ic"><use href="#i-moon"/></svg>';
    }
  };
  apply(localStorage.getItem("ml-theme") || "light");
  if (btn) btn.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    localStorage.setItem("ml-theme", next);
    apply(next);
  });
}

/* ---------- 18+ подтверждение ---------- */
function adultConfirmed() {
  try { return !!localStorage.getItem("ml-adult-ok"); } catch (e) { return false; }
}

function initAdultGate() {
  const gate = $("#adultGate");
  if (!gate) return;
  const yes = $("#agYes");
  if (yes) yes.addEventListener("click", () => {
    try { localStorage.setItem("ml-adult-ok", "1"); } catch (e) {}
    document.documentElement.classList.remove("adult-locked");
  });
}

/* ---------- Поиск в шапке (пока в каталоге два тайтла) ---------- */
function initSearch() {
  const inp = $("#searchInput");
  if (!inp) return;
  inp.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && inp.value.trim()) location.href = "manga.html";
  });
}

/* ---------- Лепестки сакуры ---------- */
function initPetals() {
  const host = $("#petals");
  if (!host) return;
  for (let i = 0; i < 14; i++) {
    const p = document.createElement("i");
    p.className = "petal";
    const s = 6 + Math.random() * 10;
    p.style.left = Math.random() * 100 + "%";
    p.style.width = s + "px";
    p.style.height = s * 1.15 + "px";
    p.style.animationDuration = 7 + Math.random() * 9 + "s";
    p.style.animationDelay = -Math.random() * 16 + "s";
    p.style.opacity = 0.35 + Math.random() * 0.5;
    host.appendChild(p);
  }
}

/* ---------- Читалка (поддерживает ?manga=vd|km&chapter=N) ---------- */
function initReader() {
  const root = $("#reader");
  if (!root) return;

  const params = new URLSearchParams(location.search);
  const t = getTitle(params.get("manga"));
  const chNum = parseInt(params.get("chapter") || "1", 10);
  const ch = getChapter(t, chNum) || t.chapters[t.chapters.length - 1];

  $("#chLabel").textContent = `${t.title} · Глава ${ch.num} · ${ch.title}`;
  document.title = `${t.title} — Глава ${ch.num} · ${SITE.name}`;

  const back = $("#rbBack");
  if (back) {
    back.href = t.id === "km" ? "title-km.html" : "manga.html";
    const bt = $("#rbBackText");
    if (bt) bt.textContent = t.title;
  }

  const saved = JSON.parse(localStorage.getItem("ml-settings") || "{}");
  let mode = saved.mode === "paged" ? "paged" : "scroll";
  let width = saved.width || "850px";

  const pagesData = ch.pages.map((src, i) => ({ src, num: i + 1 }));
  const els = [];

  function missingPageEl(p) {
    const d = document.createElement("div");
    d.className = "page-missing";
    d.innerHTML = `<div><div class="big">🌸</div><b>Страница ${p.num}</b><br>появится в следующем обновлении —<br>история продолжается!</div>`;
    return d;
  }

  pagesData.forEach((p) => {
    const wrap = document.createElement("div");
    wrap.className = "page";
    const img = document.createElement("img");
    img.loading = "lazy";
    img.alt = `${t.title} — глава ${ch.num}, страница ${p.num}`;
    img.src = p.src;
    img.addEventListener("error", () => {
      wrap.innerHTML = "";
      wrap.appendChild(missingPageEl(p));
    });
    wrap.appendChild(img);
    root.appendChild(wrap);
    els.push(wrap);
  });

  /* ---- прокрутка: какая страница сейчас на экране ---- */
  function currentScrollIndex() {
    const mid = window.scrollY + window.innerHeight * 0.45;
    let idx = 0;
    els.forEach((el, i) => {
      if (el.offsetTop <= mid) idx = i;
    });
    return idx;
  }

  /* ---- постраничный режим ---- */
  let cur = 0;
  function showPage(i) {
    if (i < 0) i = 0;
    if (i > els.length - 1) i = els.length - 1;
    cur = i;
    els.forEach((el, j) => el.classList.toggle("cur", j === i));
    updateHud();
    window.scrollTo({ top: 0 });
  }

  const left = document.createElement("div");
  left.className = "reader-side left";
  left.innerHTML = "<span>‹</span>";
  left.addEventListener("click", () => showPage(cur - 1));

  const right = document.createElement("div");
  right.className = "reader-side right";
  right.innerHTML = "<span>›</span>";
  right.addEventListener("click", () => showPage(cur + 1));

  function applyMode() {
    root.classList.toggle("paged", mode === "paged");
    if (mode === "paged") {
      document.body.appendChild(left);
      document.body.appendChild(right);
      showPage(Math.min(cur, els.length - 1));
    } else {
      left.remove();
      right.remove();
      els.forEach((el) => el.classList.remove("cur"));
      updateHud();
    }
    $$("#modeSeg button").forEach((b) => b.classList.toggle("on", b.dataset.mode === mode));
  }

  function applyWidth() {
    document.documentElement.style.setProperty("--reader-w", width);
    $$("#widthSeg button").forEach((b) => b.classList.toggle("on", b.dataset.w === width));
  }

  function saveSettings() {
    localStorage.setItem("ml-settings", JSON.stringify({ mode, width }));
  }

  /* ---- HUD ---- */
  const counter = $("#pageCounter");
  const prog = $("#rprog");
  function updateHud() {
    if (mode === "paged") {
      counter.textContent = `${cur + 1} / ${els.length}`;
      prog.style.width = `${((cur + 1) / els.length) * 100}%`;
    } else {
      const i = currentScrollIndex();
      counter.textContent = `${i + 1} / ${els.length}`;
      const doc = document.documentElement;
      const p = (window.scrollY / Math.max(1, doc.scrollHeight - window.innerHeight)) * 100;
      prog.style.width = Math.min(100, p) + "%";
    }
  }

  window.addEventListener("scroll", () => {
    if (mode === "scroll") updateHud();
  }, { passive: true });

  document.addEventListener("keydown", (e) => {
    if (mode !== "paged") return;
    if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); showPage(cur - 1); }
    if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") { e.preventDefault(); showPage(cur + 1); }
  });

  $$("#modeSeg button").forEach((b) =>
    b.addEventListener("click", () => { mode = b.dataset.mode; saveSettings(); applyMode(); })
  );
  $$("#widthSeg button").forEach((b) =>
    b.addEventListener("click", () => { width = b.dataset.w; saveSettings(); applyWidth(); })
  );

  applyWidth();
  applyMode();
  updateHud();

  /* ---- карточка конца главы ---- */
  const next = getChapter(t, ch.num + 1);
  const prev = getChapter(t, ch.num - 1);
  const endText = $("#endText");
  if (endText) {
    endText.innerHTML = next
      ? `Глава ${next.num} «${next.title}» уже доступна!`
      : `Глава ${ch.num + 1} появится по твоему следующему запросу.<br>Просто напиши «дальше»!`;
  }
  const actions = $("#endActions");
  if (actions) {
    actions.innerHTML = "";
    const add = (href, cls, icon, text) => {
      const a = document.createElement("a");
      a.className = cls;
      a.href = href;
      a.innerHTML = `<svg class="ic"><use href="#${icon}"/></svg> ${text}`;
      actions.appendChild(a);
    };
    const allHref = t.id === "km" ? "title-km.html" : "manga.html";
    if (prev) add(`read.html?manga=${t.id}&chapter=${prev.num}`, "btn ghost", "i-arrow-l", `Глава ${prev.num}`);
    if (next) add(`read.html?manga=${t.id}&chapter=${next.num}`, "btn", "i-arrow-r", `Глава ${next.num} · ${next.title}`);
    add(allHref, "btn ghost", "i-layers", "Все главы");
  }

  const chLabelEl = $("#cmtCh");
  if (chLabelEl) chLabelEl.textContent = `${t.title}, глава ${ch.num}`;

  initComments(t, ch.num);
}

/* ---------- Комментарии ---------- */
function initComments(t, chNum) {
  const list = $("#cmtList");
  const form = $("#cmtForm");
  if (!list || !form) return;

  const key = `ml-comments-${t.id}-ch${chNum}`;
  const presetsByTitle = {
    km: {
      1: [
        { name: "офисный_планктон", text: "«Смотреть в потолок. ПОТОЛОК.» — я рыдал 😂 классика жанра", time: "40 мин назад" },
        { name: "строгая_начальница", text: "Алиса в очках и с папкой — неоспоримая сила. Жду главу 2 и этот номер в отеле 🔥", time: "2 ч назад" },
        { name: "стикер_обиделся", text: "«за пиджак. не думай, что это извинение» — лучший персонаж этой главы, спасибо", time: "4 ч назад" },
      ],
    },
    vd: {
      1: [
        { name: "Сакура_фан", text: "Кирилл такой дерзкий! 😍 «Рисуй меня когда хочешь» — ах, сердце 💘", time: "2 ч назад" },
        { name: "манга_любитель", text: "Рисунок просто топ, лепестки на каждой странице — глаз радуется 💯", time: "5 ч назад" },
        { name: "Анюта", text: "Аня — это буквально я на уроках рисую вместо конспектов 🙈 жду 2 главу!!", time: "8 ч назад" },
      ],
      2: [
        { name: "команда_Ани", text: "ВИКА УЙДИ ОТ НЕГО 😤😤 Аня, держись, мы за тебя!", time: "1 ч назад" },
        { name: "реалист", text: "Скринтон на лице Вики на 5-й странице — прямо мурашки. Стиль топ 💜", time: "3 ч назад" },
        { name: "Мила_лучшая", text: "«Почти пара»… кому-то сейчас разбивали сердце 💔 жду главу 3!!", time: "6 ч назад" },
      ],
      3: [
        { name: "кошачьи_уши", text: "«Вот эта — лучшая. Забираю.» — Кирилл с кошачьими ушами теперь канон, я плакаю 😂🐱", time: "30 мин назад" },
        { name: "стратег_Мила", text: "Операция «Весенний фестиваль» — Мила главнокомандующий этого сайта. Схема с кошкой top 🗺️", time: "2 ч назад" },
        { name: "сок_щит", text: "«Делиться — полезнее» + треснувшая улыбка Вики = самая жестокая сцена за 3 главы 🔥", time: "4 ч назад" },
      ],
    },
  };
  const presets = (presetsByTitle[t.id] && presetsByTitle[t.id][chNum]) || [];
  const saved = JSON.parse(localStorage.getItem(key) || "[]");

  function render() {
    list.innerHTML = "";
    [...presets, ...saved].forEach((c) => {
      const div = document.createElement("div");
      div.className = "cmt";
      const initial = (c.name || "?").trim().charAt(0).toUpperCase();
      div.innerHTML = `
        <div class="avatar">${initial}</div>
        <div class="cmt-body">
          <div><span class="cmt-name"></span><span class="cmt-time"></span></div>
          <div class="cmt-text"></div>
        </div>`;
      div.querySelector(".cmt-name").textContent = c.name;
      div.querySelector(".cmt-time").textContent = c.time;
      div.querySelector(".cmt-text").textContent = c.text;
      list.appendChild(div);
    });
  }

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const name = $("#cmtName").value.trim() || "Аноним";
    const text = $("#cmtText").value.trim();
    if (!text) return;
    saved.push({ name, text, time: "только что" });
    localStorage.setItem(key, JSON.stringify(saved));
    form.reset();
    render();
  });

  render();
}

/* ---------- Запуск ---------- */
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initAdultGate();
  initSearch();
  initPetals();
  initReader();
});
