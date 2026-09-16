/* Главная страница */
(function () {
  "use strict";

  var ML = window.ML;

  function heroSlides(items) {
    return items.map(function (m, i) {
      var coverUri = m.cover;
      return '<div class="hero-slide' + (i === 0 ? " active" : "") + '" data-i="' + i + '">' +
        '<div class="hero-bg" style="background-image:url(\'' + coverUri + '\')"></div>' +
        '<div class="hero-content">' +
        '<img class="hero-cover" src="' + m.cover + '" alt="' + ML.escape(m.title) + '">' +
        '<div class="hero-info">' +
        '<div class="hero-kicker">' + m.typeName + " · " + m.year + " · " + m.statusName + "</div>" +
        '<h2 class="hero-title">' + ML.escape(m.title) + "</h2>" +
        '<p class="hero-desc">' + ML.escape(m.description) + "</p>" +
        '<div class="hero-tags">' + m.genres.slice(0, 5).map(function (g) {
          return '<a class="chip on-hero" href="#/catalog?genres=' + encodeURIComponent(g) + '">' + ML.escape(g) + "</a>";
        }).join("") +
        '<span class="chip on-hero">' + ML.icon("star", 12) + " " + (m.rating ? m.rating.toFixed(1) : "—") + "</span>" +
        '<span class="chip on-hero">' + ML.icon("eye", 12) + " " + ML.fmtNum(m.views) + "</span>" +
        "</div>" +
        '<div class="hero-actions">' +
        '<a class="btn btn-primary" href="#/manga/' + m.slug + "/read/1\">" + ML.icon("book", 16) + " Читать</a>" +
        '<a class="btn btn-ghost" style="color:#dfe5f0;border-color:rgba(255,255,255,.25)" href="#/manga/' + m.slug + '">' + ML.icon("info", 16) + " О тайтле</a>" +
        "</div></div></div></div>";
    }).join("");
  }

  function sectionCard(title, href, bodyHtml, extraHtml) {
    return '<section class="section">' +
      '<div class="section-head"><h2 class="section-title"><span class="bar"></span>' + title + "</h2>" +
      (extraHtml || "") +
      '<a class="link-more" href="' + href + '">Все ' + ML.icon("chevron", 14) + "</a></div>" +
      bodyHtml + "</section>";
  }

  ML.register("home", function (root) {
    var db = ML.db();
    var heroItems = ML.top(6);
    var latest = ML.updated(12);
    var popular = ML.all().slice().sort(function (a, b) { return b.views - a.views; }).slice(0, 12);
    var fresh = ML.all().filter(function (m) { return m.year >= 2024; })
      .sort(function (a, b) { return b.year - a.year || b.views - a.views; }).slice(0, 6);
    var ongoing = ML.all().filter(function (m) { return m.status === "ongoing"; })
      .sort(function (a, b) { return b.rating - a.rating; }).slice(0, 6);

    var topSide = ML.top(8).map(function (m, i) { return ML.sideItemHtml(m, i); }).join("");
    var newSide = fresh.slice(0, 5).map(function (m, i) { return ML.sideItemHtml(m, i); }).join("");

    root.setAttribute("data-title", "Читай мангу, манхву и маньхуа");

    root.innerHTML =
      '<div class="container">' +

      '<div class="hero-slider" id="hero">' +
      heroSlides(heroItems) +
      '<button class="hero-arrow prev" aria-label="Назад">' + ML.icon("chevronLeft", 18) + "</button>" +
      '<button class="hero-arrow next" aria-label="Вперёд">' + ML.icon("chevron", 18) + "</button>" +
      '<div class="hero-nav">' + heroItems.map(function (m, i) {
        return '<button class="hero-dot' + (i === 0 ? " active" : "") + '" data-i="' + i + '" aria-label="Слайд ' + (i + 1) + '"></button>';
      }).join("") + "</div>" +
      "</div>" +

      '<div style="display:grid;grid-template-columns:1fr 320px;gap:24px;align-items:start" class="home-cols">' +
      "<div>" +

      sectionCard("Последние обновления", "#/catalog?sort=updated",
        '<div class="grid-cards">' + latest.map(function (m) { return ML.cardHtml(m); }).join("") + "</div>") +

      sectionCard("Сейчас читают", "#/catalog?sort=views",
        '<div class="grid-cards">' + popular.map(function (m) { return ML.cardHtml(m); }).join("") + "</div>",
        '<div class="view-toggle" id="popToggle">' +
        '<button data-v="grid" class="active" title="Сеткой">' + ML.icon("grid", 15) + "</button>" +
        '<button data-v="rows" title="Списком">' + ML.icon("list", 15) + "</button></div>") +

      sectionCard("Новинки " + new Date().getFullYear(), "#/catalog?sort=year",
        '<div class="grid-cards">' + fresh.map(function (m) { return ML.cardHtml(m); }).join("") + "</div>") +

      sectionCard("Продолжается", "#/catalog?status=ongoing",
        '<div class="grid-cards">' + ongoing.map(function (m) { return ML.cardHtml(m); }).join("") + "</div>") +

      '<section class="section"><div class="section-head"><h2 class="section-title"><span class="bar"></span>Жанры</h2>' +
      '<a class="link-more" href="#/genres">Все жанры ' + ML.icon("chevron", 14) + "</a></div>" +
      '<div class="hero-tags">' + db.genres.slice(0, 18).map(function (g) {
        return ML.chipHtml(g.name);
      }).join("") + "</div></section>" +

      "</div>" +

      '<aside>' +
      '<div class="side-card"><h3>' + ML.icon("fire", 16) + " Топ тайтлов</h3><div class=\"side-list\">" + topSide + "</div></div>" +
      '<div class="side-card"><h3>' + ML.icon("clock", 16) + " Свежие релизы</h3><div class=\"side-list\">" + newSide + "</div></div>" +
      '<div class="side-card"><h3>' + ML.icon("info", 16) + " О проекте</h3>" +
      '<p style="font-size:12.5px;color:var(--muted);margin:0 0 10px;line-height:1.55">MangaHub — каталог в стиле манга-библиотек. ' +
      "Сейчас здесь " + db.manga.length + " " + ML.plural(db.manga.length, ["тайтл", "тайтла", "тайтлов"]) + ", и у «Поезда в 7:42» уже читаются настоящие страницы.</p>" +
      '<a class="btn btn-sm btn-ghost btn-block" href="#/about">Подробнее</a>' +
      "</div>" +
      "</aside>" +

      "</div></div>";

    /* --- слайдер --- */
    var slider = ML.qs("#hero", root);
    var slides = ML.qsa(".hero-slide", slider);
    var dots = ML.qsa(".hero-dot", slider);
    var current = 0;
    var timer = null;

    function go(i) {
      current = (i + slides.length) % slides.length;
      slides.forEach(function (s, k) { s.classList.toggle("active", k === current); });
      dots.forEach(function (d, k) { d.classList.toggle("active", k === current); });
    }
    function auto() {
      clearInterval(timer);
      timer = setInterval(function () { go(current + 1); }, 6500);
    }
    dots.forEach(function (d) {
      d.addEventListener("click", function () { go(parseInt(d.getAttribute("data-i"), 10)); auto(); });
    });
    ML.qs(".hero-arrow.prev", slider).addEventListener("click", function () { go(current - 1); auto(); });
    ML.qs(".hero-arrow.next", slider).addEventListener("click", function () { go(current + 1); auto(); });
    auto();

    /* --- переключатель вида --- */
    var toggle = ML.qs("#popToggle", root);
    if (toggle) {
      ML.qsa("button", toggle).forEach(function (b) {
        b.addEventListener("click", function () {
          ML.qsa("button", toggle).forEach(function (x) { x.classList.remove("active"); });
          b.classList.add("active");
          var section = b.closest(".section");
          var v = b.getAttribute("data-v");
          var html = v === "grid"
            ? '<div class="grid-cards">' + popular.map(function (m) { return ML.cardHtml(m); }).join("") + "</div>"
            : '<div class="grid-rows">' + popular.slice(0, 8).map(function (m) { return ML.rowCardHtml(m); }).join("") + "</div>";
          var target = section.querySelector(".grid-cards, .grid-rows");
          target.outerHTML = html;
          ML.lazy(section);
        });
      });
    }
  });
})();
