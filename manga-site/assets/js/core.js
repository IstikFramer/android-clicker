/* Утилиты MangaHub */
(function () {
  "use strict";

  var ML = (window.ML = window.ML || {});

  /* ---------- DOM ---------- */
  ML.el = function (tag, attrs, children) {
    var node = document.createElement(tag);
    attrs = attrs || {};
    Object.keys(attrs).forEach(function (k) {
      var v = attrs[k];
      if (v === null || v === undefined || v === false) return;
      if (k === "class") node.className = v;
      else if (k === "html") node.innerHTML = v;
      else if (k === "text") node.textContent = v;
      else if (k === "style") node.setAttribute("style", v);
      else if (k.slice(0, 2) === "on" && typeof v === "function") node.addEventListener(k.slice(2), v);
      else node.setAttribute(k, v);
    });
    (children || []).forEach(function (c) {
      if (!c) return;
      node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
    });
    return node;
  };

  ML.qs = function (sel, root) { return (root || document).querySelector(sel); };
  ML.qsa = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };

  ML.escape = function (s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  };

  /* ---------- Форматирование ---------- */
  var MONTHS = ["января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"];

  ML.fmtNum = function (n) {
    n = Number(n) || 0;
    if (n >= 1e6) return (n / 1e6).toFixed(n >= 1e7 ? 0 : 1).replace(".", ",") + " млн";
    if (n >= 1e3) return (n / 1e3).toFixed(n >= 1e5 ? 0 : 1).replace(".", ",") + " тыс";
    return String(n);
  };

  ML.fmtDate = function (iso) {
    if (!iso) return "—";
    var p = iso.split("-");
    return parseInt(p[2], 10) + " " + MONTHS[parseInt(p[1], 10) - 1] + " " + p[0];
  };

  ML.fmtDateShort = function (iso) {
    if (!iso) return "—";
    var p = iso.split("-");
    return p[2] + "." + p[1] + "." + p[0].slice(2);
  };

  ML.timeAgo = function (iso) {
    if (!iso) return "";
    // «сегодня» берём из данных, чтобы относительные даты совпадали с базой
    var meta = (window.MANGA_DB && window.MANGA_DB.meta) || {};
    var now = new Date((meta.today || new Date().toISOString().slice(0, 10)) + "T12:00:00Z");
    var d = new Date(iso + "T12:00:00Z");
    var days = Math.round((now - d) / 86400000);
    if (days <= 0) return "сегодня";
    if (days === 1) return "вчера";
    if (days < 7) return days + " " + ML.plural(days, ["день", "дня", "дней"]) + " назад";
    if (days < 31) return Math.floor(days / 7) + " нед. назад";
    if (days < 365) return Math.floor(days / 30) + " мес. назад";
    return ML.fmtDate(iso);
  };

  ML.plural = function (n, forms) {
    var n10 = n % 10, n100 = n % 100;
    if (n10 === 1 && n100 !== 11) return forms[0];
    if (n10 >= 2 && n10 <= 4 && (n100 < 10 || n100 >= 20)) return forms[1];
    return forms[2];
  };

  /* ---------- Роутер ---------- */
  ML.route = function () {
    var hash = location.hash.replace(/^#/, "") || "/";
    var qi = hash.indexOf("?");
    var path = qi === -1 ? hash : hash.slice(0, qi);
    var query = {};
    if (qi !== -1) {
      hash.slice(qi + 1).split("&").forEach(function (pair) {
        if (!pair) return;
        var kv = pair.split("=");
        query[decodeURIComponent(kv[0])] = decodeURIComponent(kv[1] || "");
      });
    }
    var parts = path.split("/").filter(Boolean);
    return { path: path, parts: parts, query: query };
  };

  ML.go = function (hash) { location.hash = hash; };

  ML.qsBuild = function (obj) {
    var out = [];
    Object.keys(obj).forEach(function (k) {
      var v = obj[k];
      if (v === undefined || v === null || v === "" || v === false) return;
      out.push(encodeURIComponent(k) + "=" + encodeURIComponent(Array.isArray(v) ? v.join(",") : v));
    });
    return out.length ? "?" + out.join("&") : "";
  };

  ML.activePath = function () {
    var p = ML.route().path;
    if (p === "/" || p === "") return "home";
    return p.split("/")[1];
  };

  /* ---------- Хранилище ---------- */
  var mem = {};
  ML.store = {
    get: function (key, def) {
      try {
        var raw = localStorage.getItem("ml_" + key);
        return raw === null ? def : JSON.parse(raw);
      } catch (e) { return mem[key] === undefined ? def : mem[key]; }
    },
    set: function (key, val) {
      mem[key] = val;
      try { localStorage.setItem("ml_" + key, JSON.stringify(val)); } catch (e) {}
      return val;
    },
    remove: function (key) {
      delete mem[key];
      try { localStorage.removeItem("ml_" + key); } catch (e) {}
    }
  };

  /* ---------- Пользователь (демо, без бэкенда) ---------- */
  ML.user = {
    current: function () { return ML.store.get("user", null); },
    login: function (nick) {
      var u = { nick: nick, since: new Date().toISOString().slice(0, 10) };
      ML.store.set("user", u);
      return u;
    },
    logout: function () { ML.store.remove("user"); },
    color: function (nick) {
      var palette = ["#7c5cff", "#2dd4bf", "#f4536c", "#ff8b3d", "#3ecf8e", "#4aa8e0", "#f5c344", "#b56cff"];
      var h = 0;
      for (var i = 0; i < nick.length; i++) h = (h * 31 + nick.charCodeAt(i)) >>> 0;
      return palette[h % palette.length];
    },
    initial: function (nick) { return (nick || "?").trim().charAt(0).toUpperCase(); }
  };

  ML.favorites = {
    list: function () { return ML.store.get("favorites", []); },
    has: function (slug) { return this.list().indexOf(slug) !== -1; },
    toggle: function (slug) {
      var list = this.list();
      var i = list.indexOf(slug);
      if (i === -1) { list.unshift(slug); ML.toast("Добавлено в закладки"); }
      else { list.splice(i, 1); ML.toast("Убрано из закладок"); }
      ML.store.set("favorites", list);
      return i === -1;
    }
  };

  ML.reading = {
    list: function () { return ML.store.get("reading", []); },
    mark: function (slug, chapterNumber) {
      var list = this.list().filter(function (r) { return r.slug !== slug; });
      list.unshift({ slug: slug, chapter: chapterNumber, at: Date.now() });
      ML.store.set("reading", list.slice(0, 40));
    },
    readChapters: function (slug) { return ML.store.get("read_" + slug, []); },
    markChapter: function (slug, num) {
      var arr = this.readChapters(slug);
      if (arr.indexOf(num) === -1) arr.push(num);
      ML.store.set("read_" + slug, arr);
    },
    clearAll: function () { ML.store.remove("reading"); }
  };

  /* ---------- Данные ---------- */
  ML.db = function () { return window.MANGA_DB; };

  ML.all = function () { return ML.db().manga; };

  ML.bySlug = function (slug) {
    var list = ML.all();
    for (var i = 0; i < list.length; i++) if (list[i].slug === slug) return list[i];
    return null;
  };

  ML.chapterOf = function (slug, number) {
    var m = ML.bySlug(slug);
    if (!m) return null;
    for (var i = 0; i < m.chapters.length; i++) {
      if (String(m.chapters[i].number) === String(number)) return { m: m, ch: m.chapters[i], index: i };
    }
    return null;
  };

  ML.top = function (limit, filterFn) {
    var arr = ML.all().filter(function (m) { return m.rating > 0; });
    if (filterFn) arr = arr.filter(filterFn);
    arr.sort(function (a, b) { return b.rating - a.rating || b.views - a.views; });
    return arr.slice(0, limit || 10);
  };

  ML.updated = function (limit) {
    return ML.all()
      .filter(function (m) { return m.chaptersCount > 0; })
      .slice()
      .sort(function (a, b) { return b.updated < a.updated ? -1 : b.updated > a.updated ? 1 : 0; })
      .slice(0, limit || 12);
  };

  ML.search = function (q) {
    q = (q || "").trim().toLowerCase();
    if (!q) return [];
    return ML.all().filter(function (m) {
      return (m.title.toLowerCase().indexOf(q) !== -1 ||
        m.altTitle.toLowerCase().indexOf(q) !== -1 ||
        m.genres.join(" ").toLowerCase().indexOf(q) !== -1);
    }).slice(0, 12);
  };

  ML.genreCount = function (name) {
    return ML.all().filter(function (m) { return m.genres.indexOf(name) !== -1; }).length;
  };

  /* ---------- SVG иконки ---------- */
  var ICONS = {
    search: '<path d="M21 21l-4.3-4.3M17 10.5a6.5 6.5 0 11-13 0 6.5 6.5 0 0113 0z"/>',
    star: '<path d="M12 2.5l2.9 5.9 6.6.9-4.8 4.6 1.2 6.5-5.9-3.1-5.9 3.1 1.2-6.5L2.5 9.3l6.6-.9L12 2.5z" fill="currentColor" stroke="none"/>',
    heart: '<path d="M20.8 5.6a5 5 0 00-7.1 0L12 7.3l-1.7-1.7a5 5 0 10-7.1 7.1l8.8 8.8 8.8-8.8a5 5 0 000-7.1z"/>',
    bookmark: '<path d="M6 3h12v18l-6-4-6 4V3z"/>',
    eye: '<path d="M1.5 12S5.5 5 12 5s10.5 7 10.5 7-4 7-10.5 7S1.5 12 1.5 12z"/><circle cx="12" cy="12" r="3"/>',
    chevron: '<path d="M9 18l6-6-6-6"/>',
    chevronLeft: '<path d="M15 18l-6-6 6-6"/>',
    chevronDown: '<path d="M6 9l6 6 6-6"/>',
    grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    list: '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    book: '<path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.6 1.6 0 00-2.7 1.1V21a2 2 0 11-4 0v-.1A1.6 1.6 0 006.6 19l-.1.1a2 2 0 11-2.8-2.8l.1-.1A1.6 1.6 0 002.5 15H2a2 2 0 110-4h.1A1.6 1.6 0 004 8.6l-.1-.1a2 2 0 112.8-2.8l.1.1A1.6 1.6 0 009 4.6V4a2 2 0 114 0v.1a1.6 1.6 0 002.7 1.1l.1-.1a2 2 0 112.8 2.8l-.1.1a1.6 1.6 0 001.1 2.7H21a2 2 0 110 4h-.1a1.6 1.6 0 00-1.5 1z"/>',
    bell: '<path d="M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.7 21a2 2 0 01-3.4 0"/>',
    user: '<path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    menu: '<path d="M3 6h18M3 12h18M3 18h18"/>',
    x: '<path d="M18 6L6 18M6 6l12 12"/>',
    fire: '<path d="M12 22c4 0 7-2.7 7-6.5 0-3-2-5.5-3.5-7C14 6.9 13 5 13 5s-.5 2-2 3.5S8 11 8 13c-1-.7-1.5-2-1.5-3.5C5 11 5 12.5 5 15.5 5 19.3 8 22 12 22z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    users: '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.9M16 3.1a4 4 0 010 7.8"/>',
    filter: '<path d="M22 3H2l8 9.5V19l4 2v-8.5L22 3z"/>',
    download: '<path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>',
    share: '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="M8.6 13.5l6.8 4M15.4 6.5l-6.8 4"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    moon: '<path d="M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z"/>',
    arrowRight: '<path d="M5 12h14M12 5l7 7-7 7"/>',
    reply: '<path d="M9 17l-5-5 5-5"/><path d="M4 12h11a5 5 0 015 5v2"/>',
    flag: '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><path d="M4 22v-7"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    layers: '<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>'
  };

  ML.icon = function (name, size, extra) {
    var d = ICONS[name] || "";
    var s = size || 18;
    return '<svg viewBox="0 0 24 24" width="' + s + '" height="' + s + '" fill="none" stroke="currentColor" ' +
      'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" ' + (extra || "") + '>' + d + "</svg>";
  };

  /* ---------- Тосты ---------- */
  ML.toast = function (text) {
    var box = ML.qs(".toasts");
    if (!box) {
      box = ML.el("div", { class: "toasts" });
      document.body.appendChild(box);
    }
    var t = ML.el("div", { class: "toast", text: text });
    box.appendChild(t);
    setTimeout(function () {
      t.style.opacity = "0";
      t.style.transition = "opacity .3s";
      setTimeout(function () { t.remove(); }, 300);
    }, 2200);
  };

  /* ---------- Ленивые картинки ---------- */
  ML.lazy = function (root) {
    var imgs = ML.qsa("img[data-lazy]", root);
    if (!("IntersectionObserver" in window)) {
      imgs.forEach(function (img) { ML.applyLazy(img); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          ML.applyLazy(e.target);
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: "300px" });
    imgs.forEach(function (img) { io.observe(img); });
  };

  ML.applyLazy = function (img) {
    var url = img.getAttribute("data-url") || "";
    img.removeAttribute("data-lazy");
    img.onerror = function () { img.style.background = "var(--surface-3)"; };
    if (url) img.src = url;
  };

  /* ---------- Общие рендеры ---------- */
  ML.typeBadge = function (m) {
    return '<span class="badge badge-' + m.type + '">' + m.typeName + "</span>";
  };

  ML.statusBadge = function (m) {
    return '<span class="st st-' + m.status + '">' + m.statusName + "</span>";
  };

  ML.ratingHtml = function (m) {
    if (!m.rating) return '<span class="rating-pill" style="color:var(--muted-2)">—</span>';
    return '<span class="rating-pill">' + ML.icon("star", 13) + m.rating.toFixed(1) + "</span>";
  };

  ML.coverImg = function (m, w, h, cls) {
    return '<img class="' + (cls || "") + '" data-lazy="cover" data-url="' + ML.escape(m.cover || "") + '" ' +
      'alt="' + ML.escape(m.title) + '">';
  };

  ML.cardHtml = function (m, opts) {
    opts = opts || {};
    var last = m.lastChapter ? "гл. " + m.lastChapter : (m.status === "anons" ? "анонс" : "нет глав");
    return '<a class="card" href="#/manga/' + m.slug + '">' +
      '<div class="card-cover">' +
      ML.coverImg(m, 300, 420) +
      '<span class="c-badge">' + ML.typeBadge(m) + "</span>" +
      (m.rating ? '<span class="c-rating">' + ML.icon("star", 11) + m.rating.toFixed(1) + "</span>" : "") +
      '<span class="c-chapter">' + last + "</span>" +
      "</div>" +
      '<div class="card-title">' + ML.escape(m.title) + "</div>" +
      '<div class="card-meta">' + m.year + " · " + ML.escape(m.genres.slice(0, 2).join(", ")) + "</div>" +
      "</a>";
  };

  ML.rowCardHtml = function (m) {
    return '<a class="row-card" href="#/manga/' + m.slug + '">' +
      ML.coverImg(m, 148, 208) +
      "<div>" +
      '<div class="rc-title">' + ML.escape(m.title) + "</div>" +
      '<div class="rc-desc">' + ML.escape(m.description) + "</div>" +
      '<div class="rc-meta">' + ML.typeBadge(m) + ML.statusBadge(m) +
      '<span>' + ML.icon("eye", 12) + " " + ML.fmtNum(m.views) + "</span>" +
      (m.rating ? "<span>" + ML.ratingHtml(m) + "</span>" : "") +
      "</div>" +
      "</div></a>";
  };

  ML.sideItemHtml = function (m, i) {
    return '<a class="side-item" href="#/manga/' + m.slug + '">' +
      '<span class="side-num">' + (i + 1) + "</span>" +
      ML.coverImg(m, 88, 124) +
      "<div><div class=\"si-t\">" + ML.escape(m.title) + "</div>" +
      '<div class="si-m">' + ML.ratingHtml(m) + " · " + ML.fmtNum(m.views) + " просмотров</div></div>" +
      "</a>";
  };

  ML.chipHtml = function (name, cls) {
    return '<a class="chip ' + (cls || "") + '" href="#/catalog?genres=' +
      encodeURIComponent(name) + '">' + ML.escape(name) + "</a>";
  };
})();
