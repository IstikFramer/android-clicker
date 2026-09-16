/* Каталог с фильтрами */
(function () {
  "use strict";

  var ML = window.ML;

  var SORTS = [
    { key: "updated", label: "По дате обновления" },
    { key: "popular", label: "По популярности" },
    { key: "rating", label: "По рейтингу" },
    { key: "name", label: "По алфавиту" },
    { key: "year", label: "По году выхода" },
    { key: "chapters", label: "По числу глав" }
  ];

  var PER_PAGE = 24;

  function emptyState() {
    return '<div class="empty-state"><div class="ico">📭</div><h3>Ничего не найдено</h3>' +
      "<p>Попробуй убрать часть фильтров или изменить запрос.</p>" +
      '<button class="btn btn-primary" data-reset>Сбросить фильтры</button></div>';
  }

  function filterFn(st) {
    var q = (st.q || "").trim().toLowerCase();
    return function (m) {
      if (q && m.title.toLowerCase().indexOf(q) === -1 &&
        m.altTitle.toLowerCase().indexOf(q) === -1 &&
        m.genres.join(" ").toLowerCase().indexOf(q) === -1) return false;
      if (st.types.length && st.types.indexOf(m.type) === -1) return false;
      if (st.statuses.length && st.statuses.indexOf(m.status) === -1) return false;
      if (st.ages.length && st.ages.indexOf(m.age) === -1) return false;
      if (st.countries.length && st.countries.indexOf(m.country) === -1) return false;
      if (st.genres.length && !st.genres.every(function (g) { return m.genres.indexOf(g) !== -1; })) return false;
      if (st.genresAny.length && !st.genresAny.some(function (g) { return m.genres.indexOf(g) !== -1; })) return false;
      if (st.yearFrom && m.year < parseInt(st.yearFrom, 10)) return false;
      if (st.yearTo && m.year > parseInt(st.yearTo, 10)) return false;
      return true;
    };
  }

  function sortList(list, sort) {
    var by = {
      updated: function (a, b) { return a.updated < b.updated ? 1 : -1; },
      popular: function (a, b) { return b.views - a.views; },
      rating: function (a, b) { return b.rating - a.rating || b.views - a.views; },
      name: function (a, b) { return a.title.localeCompare(b.title, "ru"); },
      year: function (a, b) { return b.year - a.year || b.views - a.views; },
      chapters: function (a, b) { return b.chaptersCount - a.chaptersCount; }
    };
    return list.sort(by[sort] || by.updated);
  }

  function csv(v) { return v ? String(v).split(",").filter(Boolean) : []; }

  ML.register("catalog", function (root, r) {
    var st = {
      q: r.query.q || "",
      types: csv(r.query.type),
      statuses: csv(r.query.status),
      ages: csv(r.query.age),
      countries: csv(r.query.country),
      genres: csv(r.query.genres),
      genresAny: [],
      yearFrom: r.query.from || "",
      yearTo: r.query.to || "",
      sort: r.query.sort || "updated",
      view: ML.store.get("catalogView", "grid"),
      page: parseInt(r.query.page, 10) || 1,
      collapsed: ML.store.get("filtersCollapsed", {})
    };

    root.setAttribute("data-title", "Каталог");

    root.innerHTML =
      '<div class="container">' +
      '<div class="crumbs"><a href="#/">Главная</a><span class="sep">/</span><span>Каталог</span></div>' +
      '<div class="page-head"><h1 class="page-title">Каталог манги, манхвы и маньхуа</h1>' +
      '<div class="page-sub">Фильтры, сортировка и поиск по ' + ML.all().length + " тайтлам демо-базы</div></div>" +
      '<div class="catalog-layout">' +
      '<aside class="filters" id="filters"></aside>' +
      "<div>" +
      '<div class="toolbar" id="toolbar"></div>' +
      '<div class="active-filters" id="afilters"></div>' +
      '<div id="results"></div>' +
      '<div id="pager"></div>' +
      "</div></div></div>";

    var filtersEl = ML.qs("#filters", root);
    var toolbarEl = ML.qs("#toolbar", root);
    var afiltersEl = ML.qs("#afilters", root);
    var resultsEl = ML.qs("#results", root);
    var pagerEl = ML.qs("#pager", root);

    /* ---------- фильтры ---------- */
    function group(title, key, bodyHtml) {
      var collapsed = !!st.collapsed[key];
      return '<div class="f-group' + (collapsed ? " collapsed" : "") + '" data-group="' + key + '">' +
        "<h4>" + title + ML.icon("chevronDown", 14) + "</h4>" +
        '<div class="f-body' + (/Жанры|Страна/.test(title) ? " col" : "") + '">' + bodyHtml + "</div></div>";
    }

    function checkboxGroup(values, field, current, counter) {
      return values.map(function (v) {
        var val = typeof v === "string" ? v : v.key;
        var label = typeof v === "string" ? v : v.name;
        var checked = current.indexOf(val) !== -1;
        return '<label class="f-check"><input type="checkbox" data-field="' + field + '" value="' + ML.escape(val) + '"' +
          (checked ? " checked" : "") + "><span>" + ML.escape(label) + "</span>" +
          '<span class="count">' + (counter ? counter(val) : "") + "</span></label>";
      }).join("");
    }

    function renderFilters() {
      var db = ML.db();
      var base = ML.all();

      function count(field, val) {
        return base.filter(function (m) {
          if (field === "type") return m.type === val;
          if (field === "status") return m.status === val;
          if (field === "age") return m.age === val;
          if (field === "country") return m.country === val;
          return m.genres.indexOf(val) !== -1;
        }).length;
      }

      filtersEl.innerHTML =
        '<div class="filters-head"><h3>Фильтры</h3>' +
        '<button class="btn btn-sm btn-ghost" data-clear>Сбросить</button></div>' +
        '<input class="f-search" data-field="q" placeholder="Название в каталоге…" value="' + ML.escape(st.q) + '">' +
        group("Тип", "type", checkboxGroup(db.types, "types", st.types, function (v) { return count("type", v); })) +
        group("Статус", "status", checkboxGroup(db.statuses, "statuses", st.statuses, function (v) { return count("status", v); })) +
        group("Страна", "country", checkboxGroup(["Япония", "Южная Корея", "Китай", "США"], "countries", st.countries, function (v) { return count("country", v); })) +
        group("Возраст", "age", checkboxGroup(["16+", "18+"], "ages", st.ages, function (v) { return count("age", v); })) +
        group("Год выпуска", "year",
          '<div style="display:flex;gap:6px;width:100%">' +
          '<input class="f-search" data-field="yearFrom" placeholder="от" value="' + ML.escape(st.yearFrom) + '" style="margin:0">' +
          '<input class="f-search" data-field="yearTo" placeholder="до" value="' + ML.escape(st.yearTo) + '" style="margin:0">' +
          "</div>") +
        group("Жанры", "genres",
          '<input class="f-search" data-field="genreSearch" placeholder="Найти жанр…">' +
          checkboxGroup(db.genres.map(function (g) { return g.name; }), "genres", st.genres, function (v) { return count("genres", v); }));

      ML.qsa(".f-group h4", filtersEl).forEach(function (h) {
        h.addEventListener("click", function () {
          var g = h.parentNode;
          var key = g.getAttribute("data-group");
          g.classList.toggle("collapsed");
          st.collapsed[key] = g.classList.contains("collapsed");
          ML.store.set("filtersCollapsed", st.collapsed);
        });
      });

      ML.qsa("input[type=checkbox]", filtersEl).forEach(function (cb) {
        cb.addEventListener("change", function () {
          var field = cb.getAttribute("data-field");
          var val = cb.value;
          var arr = st[field];
          if (cb.checked) { if (arr.indexOf(val) === -1) arr.push(val); }
          else st[field] = arr.filter(function (x) { return x !== val; });
          st.page = 1;
          render();
        });
      });

      var genreSearch = ML.qs('[data-field="genreSearch"]', filtersEl);
      if (genreSearch) {
        genreSearch.addEventListener("input", function () {
          var v = genreSearch.value.trim().toLowerCase();
          ML.qsa('[data-field="genres"]', filtersEl).forEach(function (cb) {
            var label = cb.parentNode;
            var match = !v || label.textContent.toLowerCase().indexOf(v) !== -1;
            label.style.display = match ? "" : "none";
          });
        });
      }

      var q = ML.qs('[data-field="q"]', filtersEl);
      var qTimer = null;
      q.addEventListener("input", function () {
        clearTimeout(qTimer);
        qTimer = setTimeout(function () {
          st.q = q.value;
          st.page = 1;
          render();
        }, 220);
      });

      ["yearFrom", "yearTo"].forEach(function (f) {
        var inp = ML.qs('[data-field="' + f + '"]', filtersEl);
        if (!inp) return;
        inp.addEventListener("input", function () {
          st[f] = inp.value;
          st.page = 1;
          render();
        });
      });

      ML.qs("[data-clear]", filtersEl).addEventListener("click", function () {
        st.q = ""; st.types = []; st.statuses = []; st.ages = []; st.countries = [];
        st.genres = []; st.genresAny = []; st.yearFrom = ""; st.yearTo = ""; st.page = 1;
        renderFilters(); render();
      });
    }

    /* ---------- активные фильтры ---------- */
    function renderActive() {
      var chips = [];
      function push(label, clearFn) {
        chips.push({ label: label, clear: clearFn });
      }
      if (st.q) push("Поиск: " + st.q, function () { st.q = ""; });
      ML.db().types.forEach(function (t) {
        if (st.types.indexOf(t.key) !== -1) push(t.name, function () { st.types = st.types.filter(function (x) { return x !== t.key; }); });
      });
      st.statuses.forEach(function (s) {
        push(s, function () { st.statuses = st.statuses.filter(function (x) { return x !== s; }); });
      });
      st.ages.forEach(function (a) {
        push("Возраст " + a, function () { st.ages = st.ages.filter(function (x) { return x !== a; }); });
      });
      st.countries.forEach(function (c) {
        push(c, function () { st.countries = st.countries.filter(function (x) { return x !== c; }); });
      });
      st.genres.forEach(function (g) {
        push(g, function () { st.genres = st.genres.filter(function (x) { return x !== g; }); });
      });

      if (!chips.length) { afiltersEl.innerHTML = ""; return; }
      afiltersEl.innerHTML = chips.map(function (c, i) {
        return '<span class="af-chip">' + ML.escape(c.label) +
          '<button data-i="' + i + '" title="Убрать">×</button></span>';
      }).join("");
      ML.qsa("button", afiltersEl).forEach(function (b) {
        b.addEventListener("click", function () {
          chips[parseInt(b.getAttribute("data-i"), 10)].clear();
          st.page = 1;
          renderFilters();
          render();
        });
      });
    }

    /* ---------- тулбар + результаты ---------- */
    function render() {
      var list = sortList(ML.all().filter(filterFn(st)), st.sort);
      var totalPages = Math.max(1, Math.ceil(list.length / PER_PAGE));
      if (st.page > totalPages) st.page = totalPages;
      var slice = list.slice((st.page - 1) * PER_PAGE, st.page * PER_PAGE);

      toolbarEl.innerHTML =
        '<span class="count">Найдено: <b>' + list.length + "</b> " + ML.plural(list.length, ["тайтл", "тайтла", "тайтлов"]) + "</span>" +
        '<span style="flex:1"></span>' +
        '<select class="select" data-sort>' + SORTS.map(function (s) {
          return '<option value="' + s.key + '"' + (s.key === st.sort ? " selected" : "") + ">" + s.label + "</option>";
        }).join("") + "</select>" +
        '<div class="view-toggle">' +
        '<button data-v="grid" class="' + (st.view === "grid" ? "active" : "") + '" title="Сетка">' + ML.icon("grid", 15) + "</button>" +
        '<button data-v="rows" class="' + (st.view === "rows" ? "active" : "") + '" title="Список">' + ML.icon("list", 15) + "</button>" +
        "</div>";

      ML.qs("[data-sort]", toolbarEl).addEventListener("change", function (e) {
        st.sort = e.target.value;
        st.page = 1;
        render();
      });
      ML.qsa(".view-toggle button", toolbarEl).forEach(function (b) {
        b.addEventListener("click", function () {
          st.view = b.getAttribute("data-v");
          ML.store.set("catalogView", st.view);
          render();
        });
      });

      renderActive();

      if (!slice.length) {
        resultsEl.innerHTML = emptyState();
        var rb = ML.qs("[data-reset]", resultsEl);
        if (rb) rb.addEventListener("click", function () { ML.qs("[data-clear]", filtersEl).click(); });
      } else if (st.view === "grid") {
        resultsEl.innerHTML = '<div class="grid-cards">' + slice.map(function (m) { return ML.cardHtml(m); }).join("") + "</div>";
      } else {
        resultsEl.innerHTML = '<div class="grid-rows">' + slice.map(function (m) { return ML.rowCardHtml(m); }).join("") + "</div>";
      }

      // пагинация
      if (totalPages > 1) {
        var btns = [];
        btns.push('<button data-p="' + (st.page - 1) + '"' + (st.page === 1 ? " disabled" : "") + ">←</button>");
        var from = Math.max(1, st.page - 2), to = Math.min(totalPages, from + 4);
        from = Math.max(1, to - 4);
        if (from > 1) btns.push('<button data-p="1">1</button><button disabled>…</button>');
        for (var i = from; i <= to; i++) {
          btns.push('<button data-p="' + i + '" class="' + (i === st.page ? "active" : "") + '">' + i + "</button>");
        }
        if (to < totalPages) btns.push('<button disabled>…</button><button data-p="' + totalPages + '">' + totalPages + "</button>");
        btns.push('<button data-p="' + (st.page + 1) + '"' + (st.page === totalPages ? " disabled" : "") + ">→</button>");
        pagerEl.innerHTML = '<div class="pagination">' + btns.join("") + "</div>";
        ML.qsa("button[data-p]", pagerEl).forEach(function (b) {
          b.addEventListener("click", function () {
            st.page = parseInt(b.getAttribute("data-p"), 10);
            render();
            window.scrollTo({ top: 0, behavior: "smooth" });
          });
        });
      } else {
        pagerEl.innerHTML = "";
      }

      ML.lazy(resultsEl);
    }

    renderFilters();
    render();
  });
})();
