/* Шапка, футер, роутинг и запуск приложения */
(function () {
  "use strict";

  var ML = (window.ML = window.ML || {});

  var NAV = [
    { href: "#/", key: "home", label: "Главная" },
    { href: "#/catalog", key: "catalog", label: "Каталог" },
    { href: "#/top", key: "top", label: "Топ" },
    { href: "#/genres", key: "genres", label: "Жанры" },
    { href: "#/teams", key: "teams", label: "Команды" },
    { href: "#/favorites", key: "favorites", label: "Избранное" }
  ];

  /* ---------------- Шапка ---------------- */
  function renderHeader(root, routeKey) {
    var user = ML.user.current();

    var searchBox = ML.el("div", { class: "header-search" });
    var input = ML.el("input", {
      type: "text", placeholder: "Поиск по названию или жанру…", autocomplete: "off"
    });
    var dropdown = null;

    function closeDropdown() {
      if (dropdown) { dropdown.remove(); dropdown = null; }
    }

    function openDropdown(html) {
      closeDropdown();
      dropdown = ML.el("div", { class: "search-dropdown", html: html });
      searchBox.appendChild(dropdown);
    }

    input.addEventListener("input", function () {
      var q = input.value.trim();
      if (!q) { closeDropdown(); return; }
      var results = ML.search(q);
      if (!results.length) {
        openDropdown('<div class="search-empty">По запросу «' + ML.escape(q) + '» ничего не найдено</div>');
        return;
      }
      openDropdown(results.map(function (m) {
        return '<a class="search-item" href="#/manga/' + m.slug + '" data-close="1">' +
          ML.coverImg(m, 76, 108) +
          "<div><div class=\"si-title\">" + ML.escape(m.title) + "</div>" +
          '<div class="si-meta">' + m.typeName + " · " + m.year + " · " + ML.escape(m.genres.slice(0, 3).join(", ")) + "</div></div></a>";
      }).join(""));
      ML.lazy(dropdown);
    });

    input.addEventListener("keydown", function (e) {
      if (e.key === "Enter") {
        var q = input.value.trim();
        if (q) location.hash = "#/catalog?q=" + encodeURIComponent(q);
      }
      if (e.key === "Escape") { closeDropdown(); input.blur(); }
    });

    document.addEventListener("click", function (e) {
      if (dropdown && !searchBox.contains(e.target)) closeDropdown();
      if (dropdown && e.target.closest && e.target.closest("[data-close]")) closeDropdown();
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "/" && document.activeElement !== input && !/input|textarea/i.test(document.activeElement.tagName)) {
        e.preventDefault();
        searchBox.classList.add("open");
        input.focus();
      }
    });

    searchBox.appendChild(input);
    searchBox.appendChild(ML.el("span", { class: "s-ico", html: ML.icon("search", 16) }));
    searchBox.appendChild(ML.el("span", { class: "s-kbd", text: "/" }));

    var searchToggle = ML.el("button", {
      class: "icon-btn search-toggle", title: "Поиск",
      html: ML.icon("search", 19),
      onclick: function () { searchBox.classList.toggle("open"); input.focus(); }
    });
    searchToggle.style.display = "none";

    /* тема */
    var themeBtn = ML.el("button", {
      class: "icon-btn",
      title: "Переключить тему",
      html: ML.icon(ML.store.get("theme", "dark") === "light" ? "moon" : "sun", 18),
      onclick: function () {
        var next = ML.store.get("theme", "dark") === "dark" ? "light" : "dark";
        ML.store.set("theme", next);
        document.documentElement.setAttribute("data-theme", next);
        themeBtn.innerHTML = ML.icon(next === "light" ? "moon" : "sun", 18);
        ML.toast(next === "light" ? "Светлая тема" : "Тёмная тема");
      }
    });

    var favBtn = ML.el("a", {
      class: "icon-btn", href: "#/favorites", title: "Закладки",
      html: ML.icon("bookmark", 18)
    });

    var userBlock;
    if (user) {
      userBlock = ML.el("div", { class: "header-user" });
      var chip = ML.el("a", { class: "user-chip", href: "#/favorites" }, [
        ML.el("span", {
          class: "avatar",
          text: ML.user.initial(user.nick),
          style: "background:" + ML.user.color(user.nick)
        }),
        ML.el("span", { text: user.nick })
      ]);
      var logout = ML.el("button", {
        class: "icon-btn", title: "Выйти", html: ML.icon("x", 16),
        onclick: function () {
          ML.user.logout();
          ML.toast("Вы вышли из аккаунта");
          ML.rerender();
        }
      });
      userBlock.appendChild(chip);
      userBlock.appendChild(logout);
    } else {
      userBlock = ML.el("div", { class: "header-user" });
      userBlock.appendChild(ML.el("a", { class: "btn btn-ghost btn-sm", href: "#/login", text: "Войти" }));
      userBlock.appendChild(ML.el("a", { class: "btn btn-primary btn-sm", href: "#/login?mode=register", text: "Регистрация" }));
    }

    var burger = ML.el("button", {
      class: "icon-btn burger", title: "Меню", html: ML.icon("menu", 20),
      onclick: function () {
        var nav = ML.qs(".main-nav");
        var open = nav.style.display === "flex";
        nav.style.display = open ? "" : "flex";
        nav.style.position = open ? "" : "absolute";
        nav.style.top = open ? "" : "58px";
        nav.style.left = open ? "" : "0";
        nav.style.right = open ? "" : "0";
        nav.style.flexDirection = open ? "" : "column";
        nav.style.background = open ? "" : "var(--surface)";
        nav.style.padding = open ? "" : "10px";
        nav.style.borderBottom = open ? "" : "1px solid var(--line)";
        nav.style.alignItems = open ? "" : "stretch";
      }
    });

    root.innerHTML = "";
    root.appendChild(ML.el("div", { class: "container" }, [
      ML.el("div", { class: "header-inner" }, [
        burger,
        ML.el("a", { class: "logo", href: "#/" }, [
          ML.el("span", { class: "logo-mark", text: "M" }),
          ML.el("span", { class: "logo-text", html: "Manga<span>Hub</span>" })
        ]),
        ML.el("nav", {
          class: "main-nav",
          html: NAV.map(function (n) {
            return '<a href="' + n.href + '" class="' + (n.key === routeKey ? "active" : "") + '">' + n.label + "</a>";
          }).join("")
        }),
        ML.el("div", { class: "header-spacer" }),
        searchBox,
        searchToggle,
        favBtn,
        themeBtn,
        userBlock
      ])
    ]));
  }

  /* ---------------- Футер ---------------- */
  function renderFooter(root) {
    var genres = ML.db().genres.slice(0, 8);
    root.innerHTML = "";
    root.appendChild(ML.el("div", { class: "container" }, [
      ML.el("div", { class: "footer-grid" }, [
        ML.el("div", {}, [
          ML.el("a", { class: "logo", href: "#/" }, [
            ML.el("span", { class: "logo-mark", text: "M" }),
            ML.el("span", { class: "logo-text", html: "Manga<span>Hub</span>" })
          ]),
          ML.el("p", {
            class: "footer-about",
            text: "Каталог манги, манхвы, маньхуа и комиксов: свежие главы, рейтинги, закладки и удобная читалка. " +
              "Первый тайтл с настоящими страницами уже в каталоге, новые серии подключаются через data.js."
          })
        ]),
        ML.el("div", {}, [
          ML.el("h4", { text: "Разделы" }),
          ML.el("ul", {
            html: [
              '<li><a href="#/catalog">Каталог</a></li>',
              '<li><a href="#/top">Топ тайтлов</a></li>',
              '<li><a href="#/genres">Жанры</a></li>',
              '<li><a href="#/teams">Команды перевода</a></li>',
              '<li><a href="#/favorites">Мои закладки</a></li>'
            ].join("")
          })
        ]),
        ML.el("div", {}, [
          ML.el("h4", { text: "Жанры" }),
          ML.el("ul", {
            html: genres.map(function (g) {
              return '<li><a href="#/catalog?genres=' + encodeURIComponent(g.name) + '">' + g.name + "</a></li>";
            }).join("")
          })
        ]),
        ML.el("div", {}, [
          ML.el("h4", { text: "Информация" }),
          ML.el("ul", {
            html: [
              '<li><a href="#/about">О проекте</a></li>',
              '<li><a href="#/feedback">Обратная связь</a></li>',
              '<li><a href="#/login">Вход и регистрация</a></li>',
              '<li><a href="#/catalog?type=manhwa">Манхва</a></li>',
              '<li><a href="#/catalog?type=manhua">Маньхуа</a></li>'
            ].join("")
          })
        ])
      ]),
      ML.el("div", { class: "footer-bottom" }, [
        ML.el("span", { text: "© " + new Date().getFullYear() + " MangaHub — учебный демо-проект" }),
        ML.el("span", { text: "«Поезд в 7:42» — Аяцуки Канамэ; перевод Sakura Scans RU (демо)" })
      ])
    ]));
  }

  /* ---------------- Роутер ---------------- */
  var PAGES = {};
  ML.register = function (name, fn) { PAGES[name] = fn; };

  ML.rerender = function () { route(); };

  function route() {
    var r = ML.route();
    var parts = r.parts;
    var main = ML.qs("#page");
    window.scrollTo(0, 0);

    var name = parts[0] || "home";
    // #/manga/<slug>/read/<chapter> — это читалка, а не страница тайтла
    if (name === "manga" && parts[2] === "read") name = "reader";
    var fn = PAGES[name];

    if (fn) {
      fn(main, r);
    } else {
      main.innerHTML =
        '<div class="container"><div class="empty-state">' +
        '<div class="ico">🔍</div><h3>Страница не найдена</h3>' +
        "<p>Адрес <code>" + ML.escape(r.path) + "</code> не существует.</p>" +
        '<a class="btn btn-primary" href="#/">На главную</a>' +
        "</div></div>";
    }

    renderHeader(ML.qs("#header"), name === "manga" || name === "reader" ? "catalog" : name);
    document.body.classList.toggle("no-scroll", false);
    ML.lazy(main);
    document.title = (main.getAttribute("data-title") ? main.getAttribute("data-title") + " — " : "") + "MangaHub";
  }

  function boot() {
    ML.store.get("theme", "dark");
    document.documentElement.setAttribute("data-theme", ML.store.get("theme", "dark"));

    renderFooter(ML.qs("#footer"));

    window.addEventListener("hashchange", route);
    route();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
