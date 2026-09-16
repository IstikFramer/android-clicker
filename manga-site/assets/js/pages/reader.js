/* Читалка */
(function () {
  "use strict";

  var ML = window.ML;

  function defaults() {
    return { mode: "strip", width: 800, gap: 6, fit: "width" };
  }

  ML.register("reader", function (root, r) {
    var slug = r.parts[1];
    // маршрут: #/manga/<slug>/read/<chapter>
    var number = r.parts[3] || "1";
    var found = ML.chapterOf(slug, number);

    if (!found) {
      var exists = ML.bySlug(slug);
      root.innerHTML = '<div class="container"><div class="empty-state"><div class="ico">📄</div>' +
        "<h3>Глава не найдена</h3>" +
        "<p>" + (exists ? "У тайтла «" + ML.escape(exists.title) + "» нет главы " + ML.escape(number) + "." : "Тайтл не найден.") + "</p>" +
        '<a class="btn btn-primary" href="#/manga/' + ML.escape(slug) + '">К списку глав</a></div></div>';
      return;
    }

    var m = found.m, ch = found.ch, index = found.index;
    var prev = m.chapters[index - 1];
    var next = m.chapters[index + 1];

    var settings = Object.assign(defaults(), ML.store.get("readerSettings", {}));
    ML.reading.mark(m.slug, ch.number);
    ML.reading.markChapter(m.slug, ch.number);

    // реальные сканы главы; если у главы нет pages — показываем заглушку-анонс
    var pageUrls = Array.isArray(ch.pages) ? ch.pages : [];
    var pages = pageUrls.map(function (_, i) { return i + 1; });
    var current = 0;

    root.setAttribute("data-title", m.title + " — глава " + ch.number);

    root.innerHTML =
      '<div class="reader-shell">' +
      '<div class="reader-topbar"><div class="container"><div class="rt-inner">' +
      '<a class="icon-btn" href="#/manga/' + m.slug + '" title="К тайтлу">' + ML.icon("chevronLeft", 19) + "</a>" +
      '<div class="rt-title"><a href="#/manga/' + m.slug + '">' + ML.escape(m.title) + "</a>" +
      "<span>Глава " + ch.number + " — " + ML.escape(ch.title) + " · " + pageUrls.length + " стр.</span></div>" +
      '<div class="rt-progress"><i id="rt-progress"></i></div>' +
      '<div class="rt-actions">' +
      '<a class="icon-btn" title="Предыдущая глава"' + (prev ? ' href="#/manga/' + m.slug + "/read/" + prev.number + '"' : " disabled") + ">" + ML.icon("chevronLeft", 18) + "</a>" +
      '<a class="icon-btn" title="Следующая глава"' + (next ? ' href="#/manga/' + m.slug + "/read/" + next.number + '"' : " disabled") + ">" + ML.icon("chevron", 18) + "</a>" +
      '<button class="icon-btn" id="rt-settings" title="Настройки">' + ML.icon("settings", 18) + "</button>" +
      '<button class="icon-btn" id="rt-full" title="Во весь экран">' + ML.icon("layers", 18) + "</button>" +
      "</div></div></div></div>" +

      '<div class="reader-body">' +
      (pageUrls.length
        ? '<div class="reader-notice">' + ML.icon("info", 18) +
          "<span><b>Глава с реальными сканами.</b> Пузыри с текстом — на русском, вывески и ономатопея — на японском. " +
          "Прогресс чтения сохраняется в браузере.</span></div>"
        : '<div class="reader-notice">' + ML.icon("info", 18) +
          "<span><b>Сканы этой главы ещё не загружены.</b> Файлы кладутся в assets/img/&lt;slug&gt;/ и прописываются в data.js.</span></div>") +

      '<div class="reader-pages' + (settings.mode === "paged" ? " paged" : "") + '" id="pages" style="max-width:' + settings.width + 'px;gap:' + settings.gap + 'px">' +
      pageUrls.map(function (url, idx) {
        var n = idx + 1;
        return '<div class="reader-page-wrap' + (settings.mode === "paged" && n === 1 ? " current-wrap" : "") + '">' +
          '<img class="' + (n === 1 ? "current" : "") + '" data-page="' + n + '" data-lazy="page" ' +
          'data-url="' + url + '" alt="Страница ' + n + '">' +
          '<span class="reader-page-num">' + n + " / " + pageUrls.length + "</span>" +
          "</div>";
      }).join("") +
      "</div>" +

      '<div class="reader-paged-nav">' +
      '<button class="btn btn-ghost" data-prev-page>← Предыдущая страница</button>' +
      '<span id="page-indicator" style="font-size:13px;color:var(--muted)"></span>' +
      '<button class="btn btn-ghost" data-next-page>Следующая страница →</button>' +
      "</div>" +

      '<div class="reader-bottom">' +
      (prev ? '<a class="btn btn-ghost" href="#/manga/' + m.slug + "/read/" + prev.number + '">' + ML.icon("chevronLeft", 16) + " Пред. глава</a>" : "") +
      '<select class="select reader-chapter-select" id="ch-select">' +
      m.chapters.map(function (c) {
        return '<option value="' + c.number + '"' + (c.number === ch.number ? " selected" : "") + ">" +
          (c.kind === "extra" ? "Экстра " : "Глава ") + c.number + " — " + ML.escape(c.title) + "</option>";
      }).join("") + "</select>" +
      (next ? '<a class="btn btn-primary" href="#/manga/' + m.slug + "/read/" + next.number + '">След. глава ' + ML.icon("chevron", 16) + "</a>" : '<span class="btn btn-ghost">Это последняя глава</span>') +
      "</div>" +
      "</div></div>";

    /* ---------- ленивые страницы (src подставляется из data-url) ---------- */
    var imgs = ML.qsa("#pages img", root);
    ML.lazy(root);

    /* ---------- прогресс ---------- */
    var bar = ML.qs("#rt-progress", root);
    function updateProgress() {
      var h = document.documentElement;
      var scrolled = h.scrollTop / Math.max(1, h.scrollHeight - h.clientHeight);
      var pageIdx = current;
      if (settings.mode === "strip") {
        // определяем по последней видимой странице
        var best = 0;
        imgs.forEach(function (img, i) {
          if (img.getBoundingClientRect().top < window.innerHeight * 0.6) best = i;
        });
        pageIdx = best;
        scrolled = (pageIdx + 1) / pages.length;
      }
      bar.style.width = Math.min(100, Math.round(scrolled * 100)) + "%";
    }
    window.addEventListener("scroll", updateProgress);
    updateProgress();

    /* ---------- постраничный режим ---------- */
    var indicator = ML.qs("#page-indicator", root);
    function setPage(i, scroll) {
      current = Math.max(0, Math.min(pages.length - 1, i));
      imgs.forEach(function (img, k) {
        img.classList.toggle("current", k === current);
      });
      if (indicator) indicator.textContent = "Страница " + (current + 1) + " из " + pageUrls.length;
      bar.style.width = Math.round((current + 1) / pages.length * 100) + "%";
      if (scroll) window.scrollTo({ top: 0, behavior: "smooth" });
    }

    ML.qsa("[data-prev-page]", root).forEach(function (b) {
      b.addEventListener("click", function () { setPage(current - 1, true); });
    });
    ML.qsa("[data-next-page]", root).forEach(function (b) {
      b.addEventListener("click", function () { setPage(current + 1, true); });
    });
    if (settings.mode === "paged") setPage(0, false);

    document.addEventListener("keydown", function handler(e) {
      if (!document.body.contains(root)) { document.removeEventListener("keydown", handler); return; }
      if (settings.mode === "paged") {
        if (e.key === "ArrowRight" || e.key === "PageDown") { e.preventDefault(); setPage(current + 1, true); }
        if (e.key === "ArrowLeft" || e.key === "PageUp") { e.preventDefault(); setPage(current - 1, true); }
      }
    });

    /* ---------- выбор главы ---------- */
    ML.qs("#ch-select", root).addEventListener("change", function (e) {
      location.hash = "#/manga/" + m.slug + "/read/" + e.target.value;
    });

    /* ---------- полноэкранный режим ---------- */
    ML.qs("#rt-full", root).addEventListener("click", function () {
      var bar = ML.qs(".reader-topbar", root);
      var on = bar.style.display === "none";
      bar.style.display = on ? "" : "none";
      ML.qs(".reader-notice", root).style.display = on ? "" : "none";
      ML.toast(on ? "Панель показана" : "Режим без панелей — нажмите ещё раз");
    });

    /* ---------- панель настроек ---------- */
    var panelOpen = false;
    var panel = null;

    function closePanel() {
      if (panel) { panel.remove(); panel = null; panelOpen = false; }
    }

    ML.qs("#rt-settings", root).addEventListener("click", function () {
      if (panelOpen) { closePanel(); return; }
      panelOpen = true;
      panel = ML.el("div", { class: "reader-settings" });
      panel.innerHTML =
        '<div class="rs-row"><label>Режим чтения</label>' +
        '<div class="seg" data-seg="mode">' +
        '<button data-v="strip" class="' + (settings.mode === "strip" ? "active" : "") + '">Лента</button>' +
        '<button data-v="paged" class="' + (settings.mode === "paged" ? "active" : "") + '">Постранично</button>' +
        "</div></div>" +
        '<div class="rs-row"><label>Ширина: <span id="w-val">' + settings.width + "px</span></label>" +
        '<input type="range" min="400" max="1200" step="20" value="' + settings.width + '" data-w></div>' +
        '<div class="rs-row"><label>Отступ: <span id="g-val">' + settings.gap + "px</span></label>" +
        '<input type="range" min="0" max="24" step="2" value="' + settings.gap + '" data-g></div>' +
        '<div class="rs-hint">Горячие клавиши: ← → — страницы (в постраничном режиме), Esc — закрыть настройки. ' +
        "Прогресс чтения сохраняется в браузере.</div>";
      document.body.appendChild(panel);

      function save() { ML.store.set("readerSettings", settings); }

      ML.qsa("[data-seg=mode] button", panel).forEach(function (b) {
        b.addEventListener("click", function () {
          ML.qsa("[data-seg=mode] button", panel).forEach(function (x) { x.classList.remove("active"); });
          b.classList.add("active");
          settings.mode = b.getAttribute("data-v");
          save();
          var pagesEl = ML.qs("#pages", root);
          pagesEl.classList.toggle("paged", settings.mode === "paged");
          ML.qsa(".reader-paged-nav", root).forEach(function (n) {
            n.style.display = settings.mode === "paged" ? "flex" : "none";
          });
          if (settings.mode === "paged") setPage(0, false);
          else window.scrollTo(0, 0);
        });
      });

      var wInput = ML.qs("[data-w]", panel);
      wInput.addEventListener("input", function () {
        settings.width = parseInt(wInput.value, 10);
        ML.qs("#w-val", panel).textContent = settings.width + "px";
        ML.qs("#pages", root).style.maxWidth = settings.width + "px";
        save();
      });

      var gInput = ML.qs("[data-g]", panel);
      gInput.addEventListener("input", function () {
        settings.gap = parseInt(gInput.value, 10);
        ML.qs("#g-val", panel).textContent = settings.gap + "px";
        ML.qs("#pages", root).style.gap = settings.gap + "px";
        save();
      });
    });

    ML.qsa(".reader-paged-nav", root).forEach(function (n) {
      n.style.display = settings.mode === "paged" ? "flex" : "none";
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && panelOpen) closePanel();
    });
    document.addEventListener("click", function (e) {
      if (panelOpen && panel && !panel.contains(e.target) && !e.target.closest("#rt-settings")) closePanel();
    });
  });
})();
