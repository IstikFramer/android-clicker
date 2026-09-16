/* Топ, жанры, команды, избранное, авторизация, инфостраницы */
(function () {
  "use strict";

  var ML = window.ML;

  /* ---------------- Топ ---------------- */
  ML.register("top", function (root, r) {
    var tab = r.query.tab || "all";
    root.setAttribute("data-title", "Топ тайтлов");

    var filters = {
      all: function () { return true; },
      manga: function (m) { return m.type === "manga"; },
      manhwa: function (m) { return m.type === "manhwa"; },
      manhua: function (m) { return m.type === "manhua"; },
      comic: function (m) { return m.type === "comic"; },
      ongoing: function (m) { return m.status === "ongoing"; },
      completed: function (m) { return m.status === "completed"; }
    };

    var list = ML.all().filter(function (m) { return m.rating > 0; })
      .filter(filters[tab] || filters.all)
      .sort(function (a, b) { return b.rating - a.rating || b.views - a.views; });

    var podium = list.slice(0, 3);
    var rest = list.slice(3);

    root.innerHTML =
      '<div class="container">' +
      '<div class="crumbs"><a href="#/">Главная</a><span class="sep">/</span><span>Топ</span></div>' +
      '<div class="page-head"><h1 class="page-title">Топ тайтлов</h1>' +
      '<div class="page-sub">Рейтинг составлен по оценкам читателей демо-базы</div></div>' +

      '<div class="tabs" style="margin-bottom:20px">' +
      [["all", "Все"], ["manga", "Манга"], ["manhwa", "Манхва"], ["manhua", "Маньхуа"],
        ["comic", "Комиксы"], ["ongoing", "Выпускается"], ["completed", "Завершено"]].map(function (t) {
          return '<a class="tab' + (tab === t[0] ? " active" : "") + '" href="#/top?tab=' + t[0] + '">' + t[1] + "</a>";
        }).join("") +
      "</div>" +

      (podium.length ? '<div class="grid-cards" style="grid-template-columns:repeat(auto-fit,minmax(200px,1fr));margin-bottom:26px">' +
        podium.map(function (m, i) {
          return '<a class="card" href="#/manga/' + m.slug + '" style="position:relative">' +
            '<div class="card-cover" style="aspect-ratio:3/4">' +
            ML.coverImg(m, 360, 480) +
            '<span class="c-rating" style="top:10px;right:10px;font-size:14px;padding:4px 9px">' + ML.icon("star", 14) + m.rating.toFixed(1) + "</span>" +
            '<span class="c-badge" style="font-size:22px;font-weight:900;color:#fff;text-shadow:0 2px 8px #000;top:8px;left:10px">#' + (i + 1) + "</span>" +
            "</div>" +
            '<div class="card-title" style="font-size:15px">' + ML.escape(m.title) + "</div>" +
            '<div class="card-meta">' + m.typeName + " · " + m.year + " · " + ML.fmtNum(m.views) + " просмотров</div>" +
            "</a>";
        }).join("") + "</div>" : "") +

      (rest.length ? '<div class="chapter-list">' +
      rest.map(function (m, i) {
        return '<a class="chapter-row" style="grid-template-columns:44px 60px 1fr 120px 110px 30px" href="#/manga/' + m.slug + '">' +
          '<span class="num" style="color:var(--muted)">' + (i + 4) + "</span>" +
          '<span style="width:44px;height:62px;border-radius:4px;overflow:hidden;flex:none">' + ML.coverImg(m, 90, 126) + "</span>" +
          '<span class="ttl" style="color:var(--text);font-weight:600">' + ML.escape(m.title) + "</span>" +
          '<span>' + ML.typeBadge(m) + "</span>" +
          '<span class="views">' + ML.icon("star", 13) + " " + m.rating.toFixed(1) + " · " + ML.fmtNum(m.views) + "</span>" +
          '<span class="go">' + ML.icon("chevron", 16) + "</span>" +
          "</a>";
      }).join("") +
      "</div>" : "") + "</div>";
  });

  /* ---------------- Жанры ---------------- */
  ML.register("genres", function (root) {
    root.setAttribute("data-title", "Жанры");
    var genres = ML.db().genres.map(function (g) {
      return { name: g.name, count: ML.genreCount(g.name) };
    }).sort(function (a, b) { return b.count - a.count; });

    root.innerHTML =
      '<div class="container">' +
      '<div class="crumbs"><a href="#/">Главная</a><span class="sep">/</span><span>Жанры</span></div>' +
      '<div class="page-head"><h1 class="page-title">Жанры</h1>' +
      '<div class="page-sub">' + genres.length + " жанров в демо-каталоге</div></div>" +
      '<div class="genre-grid">' +
      genres.map(function (g) {
        return '<a class="genre-tile" href="#/catalog?genres=' + encodeURIComponent(g.name) + '">' +
          "<span>" + ML.escape(g.name) + "</span>" +
          '<span class="n">' + g.count + "</span></a>";
      }).join("") +
      "</div>" +

      '<section class="section"><div class="section-head"><h2 class="section-title"><span class="bar"></span>Лучшее в жанре «' + ML.escape(genres[0].name) + '»</h2></div>' +
      (genres[0].count
        ? '<div class="grid-cards">' +
          ML.all().filter(function (m) { return m.genres.indexOf(genres[0].name) !== -1; })
            .sort(function (a, b) { return b.rating - a.rating; }).slice(0, 6)
            .map(function (m) { return ML.cardHtml(m); }).join("") +
          "</div>"
        : '<div class="empty-state"><p>В этом жанре пока пусто.</p></div>') +
      "</section>" +
      "</div>";
  });

  /* ---------------- Команды ---------------- */
  ML.register("teams", function (root) {
    root.setAttribute("data-title", "Команды перевода");
    var teams = ML.db().translators.map(function (name) {
      var titles = ML.all().filter(function (m) { return m.translator === name; });
      var chapters = titles.reduce(function (acc, m) { return acc + m.chaptersCount; }, 0);
      return { name: name, titles: titles, chapters: chapters };
    }).sort(function (a, b) { return b.chapters - a.chapters; });

    root.innerHTML =
      '<div class="container">' +
      '<div class="crumbs"><a href="#/">Главная</a><span class="sep">/</span><span>Команды</span></div>' +
      '<div class="page-head"><h1 class="page-title">Команды перевода</h1>' +
      '<div class="page-sub">Демо-список: настоящие команды к тайтлам ещё не привязаны</div></div>' +
      '<div class="team-grid">' +
      teams.map(function (t) {
        return '<div class="team-card">' +
          '<div style="display:flex;gap:10px;align-items:center">' +
          '<span class="avatar" style="background:' + ML.user.color(t.name) + '">' + ML.user.initial(t.name) + "</span>" +
          "<div><div class=\"tn\">" + ML.escape(t.name) + "</div>" +
          '<div class="tm">' + t.titles.length + " " + ML.plural(t.titles.length, ["тайтл", "тайтла", "тайтлов"]) +
          " · " + t.chapters + " глав</div></div></div>" +
          '<div class="tt">' + t.titles.slice(0, 3).map(function (m) {
            return '<a class="chip" href="#/manga/' + m.slug + '">' + ML.escape(m.title) + "</a>";
          }).join("") + (t.titles.length > 3 ? '<span class="chip">+' + (t.titles.length - 3) + "</span>" : "") + "</div>" +
          "</div>";
      }).join("") +
      "</div></div>";
  });

  /* ---------------- Избранное ---------------- */
  ML.register("favorites", function (root) {
    var user = ML.user.current();
    root.setAttribute("data-title", "Избранное");

    var favs = ML.favorites.list().map(ML.bySlug).filter(Boolean);
    var history = ML.reading.list().map(function (rec) {
      var m = ML.bySlug(rec.slug);
      return m ? { m: m, chapter: rec.chapter } : null;
    }).filter(Boolean);

    var historyHtml = history.length
      ? '<div class="grid-cards">' + history.slice(0, 12).map(function (rec) {
          return '<a class="card" href="#/manga/' + rec.m.slug + "/read/" + rec.chapter + '">' +
            '<div class="card-cover">' +
            ML.coverImg(rec.m) +
            '<span class="c-chapter">гл. ' + rec.chapter + "</span></div>" +
            '<div class="card-title">' + ML.escape(rec.m.title) + "</div>" +
            '<div class="card-meta">Продолжить чтение</div></a>';
        }).join("") + "</div>"
      : '<div class="empty-state"><div class="ico">📚</div><h3>Истории пока нет</h3>' +
        "<p>Откройте любую главу — она появится здесь.</p>" +
        '<a class="btn btn-primary" href="#/catalog">В каталог</a></div>';

    root.innerHTML =
      '<div class="container">' +
      '<div class="crumbs"><a href="#/">Главная</a><span class="sep">/</span><span>Избранное</span></div>' +
      '<div class="page-head"><h1 class="page-title">' + (user ? "Привет, " + ML.escape(user.nick) : "Избранное") + "</h1>" +
      '<div class="page-sub">Закладки и история чтения хранятся локально в вашем браузере</div></div>' +

      '<section class="section"><div class="section-head"><h2 class="section-title"><span class="bar"></span>Закладки <span style="color:var(--muted);font-weight:600;font-size:14px">' + favs.length + "</span></h2></div>" +
      (favs.length
        ? '<div class="grid-cards">' + favs.map(function (m) { return ML.cardHtml(m); }).join("") + "</div>"
        : '<div class="empty-state"><div class="ico">🔖</div><h3>Закладок пока нет</h3>' +
          "<p>Нажмите «В закладки» на странице тайтла.</p>" +
          '<a class="btn btn-primary" href="#/catalog">Найти что почитать</a></div>') +
      "</section>" +

      '<section class="section"><div class="section-head"><h2 class="section-title"><span class="bar"></span>Продолжить чтение</h2>' +
      (history.length ? '<button class="link-more" id="clear-history" style="border:0;background:none;color:var(--muted);cursor:pointer">Очистить историю</button>' : "") +
      "</div>" + historyHtml + "</section>" +
      "</div>";

    var clear = ML.qs("#clear-history", root);
    if (clear) {
      clear.addEventListener("click", function () {
        ML.reading.clearAll();
        ML.toast("История очищена");
        ML.rerender();
      });
    }
  });

  /* ---------------- Вход / регистрация ---------------- */
  ML.register("login", function (root, r) {
    var mode = r.query.mode === "register" ? "register" : "login";
    root.setAttribute("data-title", mode === "register" ? "Регистрация" : "Вход");

    root.innerHTML =
      '<div class="container">' +
      '<div class="auth-card">' +
      '<div class="auth-tabs">' +
      '<button data-m="login" class="' + (mode === "login" ? "active" : "") + '">Вход</button>' +
      '<button data-m="register" class="' + (mode === "register" ? "active" : "") + '">Регистрация</button>' +
      "</div>" +
      '<form id="auth-form">' +
      '<div class="field"><label>Никнейм</label><input name="nick" required minlength="3" maxlength="20" placeholder="Например, MangaReader"></div>' +
      '<div class="field"><label>Почта</label><input name="email" type="email" placeholder="you@example.com"></div>' +
      '<div class="field"><label>Пароль</label><input name="pass" type="password" required minlength="4" placeholder="••••••••"></div>' +
      '<button class="btn btn-primary btn-block btn-lg" type="submit">' + (mode === "register" ? "Создать аккаунт" : "Войти") + "</button>" +
      "</form>" +
      '<div class="auth-hint">Бэкенда пока нет: вход работает локально, аккаунт сохраняется в браузере. ' +
      "Никакие данные никуда не отправляются.</div>" +
      "</div></div>";

    var form = ML.qs("#auth-form", root);
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var nick = (form.elements.namedItem("nick").value || "").trim();
      if (!nick) return;
      ML.user.login(nick);
      ML.toast("Добро пожаловать, " + nick + "!");
      location.hash = "#/favorites";
    });

    ML.qsa(".auth-tabs button", root).forEach(function (b) {
      b.addEventListener("click", function () {
        location.hash = "#/login" + (b.getAttribute("data-m") === "register" ? "?mode=register" : "");
      });
    });
  });

  /* ---------------- О проекте ---------------- */
  ML.register("about", function (root) {
    var db = ML.db();
    var chapters = db.manga.reduce(function (a, m) { return a + m.chaptersCount; }, 0);
    root.setAttribute("data-title", "О проекте");

    root.innerHTML =
      '<div class="container">' +
      '<div class="crumbs"><a href="#/">Главная</a><span class="sep">/</span><span>О проекте</span></div>' +
      '<div class="page-head"><h1 class="page-title">О проекте</h1></div>' +
      '<div class="prose">' +
      "<p>MangaHub — многостраничный каталог манги, манхвы, маньхуа и комиксов, собранный как статический сайт " +
      "без сборки и зависимостей: чистый HTML, CSS и JavaScript, данные лежат в одном файле data.js.</p>" +
      "<p>Первая серия — «Поезд в 7:42» Аяцуки Канамэ: цветная обложка и чёрно-белая первая глава из девяти страниц, " +
      "пузыри с текстом на русском, вывески и ономатопея на японском.</p>" +

      "<h2>Что уже работает</h2><ul>" +
      "<li>Главная со слайдером, лентами «Последние обновления», «Сейчас читают», «Новинки»</li>" +
      "<li>Каталог с фильтрами по типу, статусу, стране, возрасту, годам и жанрам, сортировкой и пагинацией</li>" +
      "<li>Страница тайтла: описание, список глав, отзывы, комментарии, оценка, похожие тайтлы</li>" +
      "<li>Читалка с режимами «лента» и «постранично», настройками ширины и прогрессом чтения</li>" +
      "<li>Топ, жанры, команды перевода, избранное, история чтения, вход и регистрация</li>" +
      "<li>Закладки, оценки и прогресс сохраняются в localStorage</li>" +
      "</ul>" +

      "<h2>Что сейчас в базе</h2><ul>" +
      "<li>" + db.manga.length + " " + ML.plural(db.manga.length, ["тайтл", "тайтла", "тайтлов"]) + " и " + chapters + " " + ML.plural(chapters, ["глава", "главы", "глав"]) + " с настоящими страницами</li>" +
      "<li>Обложка — цветная, страницы главы — чёрно-белые сканы с русскими пузырями</li>" +
      "<li>Аккаунт, комментарии и оценки работают локально, без сервера</li>" +
      "</ul>" +

      "<h2>Как добавить новую мангу</h2>" +
      "<p>База ведётся вручную в <code>manga-site/assets/js/data.js</code>:</p>" +
      "<ul><li>положите обложку и страницы главы в <code>assets/img/&lt;slug&gt;/</code>,</li>" +
      "<li>добавьте объект тайтла в массив <code>manga</code>: поле <code>cover</code> — путь к обложке, " +
      "массив <code>pages</code> у главы — пути к страницам по порядку,</li>" +
      "<li>или подмените <code>window.MANGA_DB</code> ответом API — структура та же.</li></ul>" +

      "<h2>Как запустить</h2>" +
      "<p>Из папки <code>manga-site</code>:</p>" +
      "<ul><li><code>python3 -m http.server 8000</code> — затем открыть http://localhost:8000</li>" +
      "<li>или любой другой статический сервер (<code>npx serve</code>, nginx и т.д.)</li></ul>" +
      "</div></div>";
  });

  /* ---------------- Обратная связь ---------------- */
  ML.register("feedback", function (root) {
    root.setAttribute("data-title", "Обратная связь");
    root.innerHTML =
      '<div class="container">' +
      '<div class="crumbs"><a href="#/">Главная</a><span class="sep">/</span><span>Обратная связь</span></div>' +
      '<div class="page-head"><h1 class="page-title">Обратная связь</h1>' +
      '<div class="page-sub">Нашли баг или хотите предложить тайтл? Напишите.</div></div>' +
      '<div class="auth-card" style="max-width:560px">' +
      '<form id="fb-form">' +
      '<div class="field"><label>Имя</label><input name="name" required placeholder="Как к вам обращаться"></div>' +
      '<div class="field"><label>Тема</label>' +
      '<select class="select" name="topic" style="width:100%;height:40px">' +
      "<option>Ошибка на сайте</option><option>Предложить тайтл</option>" +
      "<option>Проблема с переводом</option><option>Другое</option></select></div>" +
      '<div class="field"><label>Сообщение</label><textarea name="text" required placeholder="Опишите подробно…"></textarea></div>' +
      '<button class="btn btn-primary btn-block btn-lg" type="submit">Отправить</button>' +
      "</form>" +
      '<div class="auth-hint">Форма демонстрационная: отправка не настроена, письмо никуда не уходит.</div>' +
      "</div></div>";

    ML.qs("#fb-form", root).addEventListener("submit", function (e) {
      e.preventDefault();
      ML.toast("Спасибо! (демо-отправка, бэкенда нет)");
      e.target.reset();
    });
  });
})();
