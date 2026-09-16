/* Страница тайтла */
(function () {
  "use strict";

  var ML = window.ML;

  function similar(m, limit) {
    return ML.all()
      .filter(function (x) {
        return x.slug !== m.slug && x.genres.some(function (g) { return m.genres.indexOf(g) !== -1; });
      })
      .sort(function (a, b) {
        var sa = a.genres.filter(function (g) { return m.genres.indexOf(g) !== -1; }).length;
        var sb = b.genres.filter(function (g) { return m.genres.indexOf(g) !== -1; }).length;
        return sb - sa || b.rating - a.rating;
      })
      .slice(0, limit || 5);
  }

  ML.register("manga", function (root, r) {
    var m = ML.bySlug(r.parts[1]);
    if (!m) {
      root.innerHTML = '<div class="container"><div class="empty-state"><div class="ico">📖</div>' +
        "<h3>Тайтл не найден</h3><p>Возможно, он был удалён или ссылка устарела.</p>" +
        '<a class="btn btn-primary" href="#/catalog">В каталог</a></div></div>';
      return;
    }

    root.setAttribute("data-title", m.title);

    var isFav = ML.favorites.has(m.slug);
    var votes = ML.store.get("votes_" + m.slug, null);
    var read = ML.reading.readChapters(m.slug);

    var progress = m.chaptersCount ? Math.round(read.length / m.chaptersCount * 100) : 0;

    root.innerHTML =
      '<div class="container">' +
      '<div class="crumbs"><a href="#/">Главная</a><span class="sep">/</span>' +
      '<a href="#/catalog?type=' + m.type + '">' + m.typeName + '</a><span class="sep">/</span>' +
      "<span>" + ML.escape(m.title) + "</span></div>" +

      '<div class="manga-head">' +
      '<div class="manga-backdrop" style="background-image:url(\'' + ML.Cover.uri(m.title, m.typeName, m.slug, 600, 840) + '\')"></div>' +
      '<div class="manga-head-inner">' +
      '<div class="manga-cover-wrap">' +
      '<img class="manga-cover" src="' + ML.Cover.uri(m.title, m.typeName, m.slug, 400, 560) + '" alt="' + ML.escape(m.title) + '">' +
      '<div class="manga-cover-actions">' +
      '<button class="icon-btn" data-fav title="В закладки" style="background:var(--surface);border:1px solid var(--line)">' +
      '<span style="color:' + (isFav ? "var(--red)" : "var(--muted)") + '">' + ML.icon("heart", 17, isFav ? 'fill="currentColor"' : "") + "</span></button>" +
      '<button class="icon-btn" data-share title="Поделиться" style="background:var(--surface);border:1px solid var(--line)">' + ML.icon("share", 17) + "</button>" +
      "</div></div>" +

      "<div>" +
      '<h1 class="manga-title">' + ML.escape(m.title) + "</h1>" +
      '<div class="manga-alt">' + ML.escape(m.altTitle) + " · " + m.year + "</div>" +
      '<div class="manga-tags">' +
      ML.typeBadge(m) + ML.statusBadge(m) +
      '<span class="chip">' + m.age + "</span>" +
      m.genres.map(function (g) { return ML.chipHtml(g); }).join("") +
      "</div>" +

      '<div class="manga-actions">' +
      (m.chaptersCount
        ? '<a class="btn btn-primary btn-lg" href="#/manga/' + m.slug + "/read/" + (read.length ? m.chapters[Math.min(read.length, m.chaptersCount - 1)].number : m.chapters[0].number) + '">' +
          ML.icon("book", 17) + (read.length ? "Продолжить" : "Читать") + "</a>"
        : '<button class="btn btn-primary btn-lg" disabled>' + ML.icon("clock", 17) + " Ждём релиз</button>") +
      '<button class="btn btn-ghost btn-lg" data-fav2>' + ML.icon("heart", 16) + (isFav ? " В закладках" : " В закладки") + "</button>" +
      '<button class="btn btn-ghost btn-lg" data-subscribe>' + ML.icon("bell", 16) + " Подписаться</button>" +
      "</div>" +

      '<div class="stats-row">' +
      '<div class="stat-box"><div class="v" style="color:var(--yellow)">' + (m.rating ? m.rating.toFixed(1) : "—") + "</div>" +
      '<div class="l">' + ML.fmtNum(m.votes) + " оценок</div></div>" +
      '<div class="stat-box"><div class="v">' + ML.fmtNum(m.views) + "</div><div class=\"l\">просмотров</div></div>" +
      '<div class="stat-box"><div class="v">' + ML.fmtNum(m.favorites) + "</div><div class=\"l\">в закладках</div></div>" +
      '<div class="stat-box"><div class="v">' + m.chaptersCount + "</div><div class=\"l\">" + ML.plural(m.chaptersCount, ["глава", "главы", "глав"]) + "</div></div>" +
      '<div class="stat-box"><div class="v">' + progress + "%</div><div class=\"l\">ваш прогресс</div></div>" +
      "</div>" +

      '<dl class="info-table">' +
      "<dt>Тип</dt><dd>" + m.typeName + "</dd>" +
      "<dt>Страна</dt><dd>" + m.country + "</dd>" +
      "<dt>Автор</dt><dd>" + ML.escape(m.authors.join(", ")) + "</dd>" +
      "<dt>Художник</dt><dd>" + ML.escape(m.artists.join(", ")) + "</dd>" +
      "<dt>Издатель</dt><dd>" + m.publisher + "</dd>" +
      "<dt>Перевод</dt><dd><a href=\"#/teams\">" + m.translator + "</a></dd>" +
      "<dt>Статус</dt><dd>" + m.statusName + "</dd>" +
      (m.lastChapter ? "<dt>Обновлено</dt><dd>Глава " + m.lastChapter + " · " + ML.timeAgo(m.lastChapterDate) + "</dd>" : "") +
      "</dl>" +
      "</div></div></div>" +

      '<div class="manga-body">' +
      "<div>" +
      '<div class="tabs" id="tabs">' +
      '<button class="tab active" data-tab="info">Описание</button>' +
      '<button class="tab" data-tab="chapters">Главы <span class="n">' + m.chaptersCount + "</span></button>" +
      '<button class="tab" data-tab="reviews">Отзывы <span class="n">' + m.reviews.length + "</span></button>" +
      '<button class="tab" data-tab="comments">Комментарии <span class="n">' + m.comments.length + "</span></button>" +
      "</div>" +
      '<div id="tab-body"></div>' +
      "</div>" +

      '<aside>' +
      '<div class="side-card"><h3>' + ML.icon("star", 15) + " Оценка</h3>" +
      '<div class="stars" id="stars">' + [1, 2, 3, 4, 5].map(function (i) {
        return '<button data-v="' + i + '" class="' + (votes >= i ? "on" : "") + '">' + ML.icon("star", 22, votes >= i ? 'fill="currentColor"' : "") + "</button>";
      }).join("") + "</div>" +
      '<div style="font-size:12px;color:var(--muted);margin-top:8px" id="vote-msg">' +
      (votes ? "Ваша оценка: " + votes + " из 5" : "Поставьте оценку тайтлу") + "</div>" +
      "</div>" +
      '<div class="side-card"><h3>' + ML.icon("layers", 15) + " Похожие тайтлы</h3><div class=\"side-list\">" +
      similar(m, 5).map(function (x, i) { return ML.sideItemHtml(x, i); }).join("") +
      "</div></div>" +
      '<div class="side-card"><h3>' + ML.icon("info", 15) + " Дисклеймер</h3>" +
      '<p style="font-size:12px;color:var(--muted);margin:0;line-height:1.55">Страницы глав здесь — сгенерированные заглушки. ' +
      "Настоящие сканы тайтла в демо-базу не загружены.</p></div>" +
      "</aside>" +
      "</div></div>";

    /* ---------- вкладки ---------- */
    var body = ML.qs("#tab-body", root);

    function tabInfo() {
      body.innerHTML =
        '<p class="desc-text">' + ML.escape(m.description) + "</p>" +
        '<div style="margin-top:22px;display:flex;gap:8px;flex-wrap:wrap">' +
        m.genres.map(function (g) { return ML.chipHtml(g, "accent"); }).join("") +
        "</div>" +
        '<div style="margin-top:22px;border-top:1px solid var(--line-soft);padding-top:16px;font-size:12.5px;color:var(--muted-2)">' +
        "Добавлено: " + ML.fmtDate(m.updated) + " · ID тайтла: " + m.slug +
        "</div>";
    }

    function tabChapters() {
      if (!m.chapters.length) {
        body.innerHTML = '<div class="empty-state"><div class="ico">⏳</div><h3>Глав пока нет</h3>' +
          "<p>Тайтл анонсирован, главы появятся позже.</p></div>";
        return;
      }
      var order = ML.store.get("chOrder_" + m.slug, "desc");
      var onlyUnread = ML.store.get("chUnread_" + m.slug, false);
      var query = "";

      function list() {
        var arr = m.chapters.slice();
        if (query) {
          var q = query.toLowerCase();
          arr = arr.filter(function (c) {
            return ("глава " + c.number + " " + c.title).toLowerCase().indexOf(q) !== -1;
          });
        }
        if (onlyUnread) arr = arr.filter(function (c) { return read.indexOf(c.number) === -1; });
        // в данных главы лежат по возрастанию (1 → N)
        if (order === "desc") arr.reverse();
        return arr;
      }

      function draw() {
        var arr = list();
        body.innerHTML =
          '<div class="chapters-toolbar">' +
          '<input class="f-search" data-chq placeholder="Поиск главы…" value="' + ML.escape(query) + '" style="max-width:240px">' +
          '<button class="btn btn-sm btn-ghost" data-order>' + (order === "desc" ? "Сначала новые" : "Сначала старые") + "</button>" +
          '<button class="btn btn-sm btn-ghost" data-unread>' + (onlyUnread ? "Только непрочитанные ✓" : "Все главы") + "</button>" +
          '<span style="margin-left:auto;font-size:12.5px;color:var(--muted)">Прочитано ' + read.length + " из " + m.chaptersCount + "</span>" +
          "</div>" +
          (arr.length
            ? '<div class="chapter-list">' + arr.map(function (c) {
                var isRead = read.indexOf(c.number) !== -1;
                return '<a class="chapter-row' + (isRead ? " read" : "") + '" href="#/manga/' + m.slug + "/read/" + c.number + '">' +
                  '<span class="num">' + (c.kind === "extra" ? "Экстра " : "Гл. ") + c.number + "</span>" +
                  '<span class="ttl">' + ML.escape(c.title) + "</span>" +
                  '<span class="date">' + ML.timeAgo(c.date) + "</span>" +
                  '<span class="views">' + ML.icon("eye", 13) + " " + ML.fmtNum(c.views) + "</span>" +
                  '<span class="go">' + ML.icon("chevron", 16) + "</span>" +
                  "</a>";
              }).join("") + "</div>"
            : '<div class="empty-state"><h3>Ничего не найдено</h3><p>Попробуйте другой запрос.</p></div>');

        var qi = ML.qs("[data-chq]", body);
        if (qi) {
          qi.addEventListener("input", function () {
            query = qi.value;
            var pos = qi.selectionStart;
            draw();
            var again = ML.qs("[data-chq]", body);
            again.focus();
            again.setSelectionRange(pos, pos);
          });
        }
        ML.qs("[data-order]", body).addEventListener("click", function () {
          order = order === "desc" ? "asc" : "desc";
          ML.store.set("chOrder_" + m.slug, order);
          draw();
        });
        ML.qs("[data-unread]", body).addEventListener("click", function () {
          onlyUnread = !onlyUnread;
          ML.store.set("chUnread_" + m.slug, onlyUnread);
          draw();
        });
      }
      draw();
    }

    function tabReviews() {
      body.innerHTML = m.reviews.map(function (rv) {
        return '<div class="review-card">' +
          '<div class="rv-head">' +
          '<span class="avatar sm" style="background:' + ML.user.color(rv.author) + '">' + ML.user.initial(rv.author) + "</span>" +
          '<div><div class="rv-title">' + ML.escape(rv.title) + "</div>" +
          '<div style="font-size:11.5px;color:var(--muted-2)">' + ML.escape(rv.author) + " · " + ML.fmtDate(rv.date) + "</div></div>" +
          '<span class="rv-score">' + rv.score + "/5</span>" +
          "</div>" +
          '<p style="margin:0;font-size:13.5px;color:#c9d2e0">' + ML.escape(rv.text) + "</p>" +
          "</div>";
      }).join("") +
      '<button class="btn btn-ghost" data-add-review>' + ML.icon("plus", 15) + " Написать отзыв</button>";

      ML.qs("[data-add-review]", body).addEventListener("click", function () {
        ML.toast("Отзывы откроются, когда появится бэкенд");
      });
    }

    function tabComments() {
      var user = ML.user.current();
      var mine = ML.store.get("comments_" + m.slug, []);
      var all = mine.concat(m.comments);

      body.innerHTML =
        '<div class="comment-form">' +
        (user ? '<span class="avatar" style="background:' + ML.user.color(user.nick) + '">' + ML.user.initial(user.nick) + "</span>" : "") +
        '<textarea placeholder="' + (user ? "Написать комментарий…" : "Войдите, чтобы оставить комментарий") + '"' + (user ? "" : " disabled") + '></textarea>' +
        '<button class="btn btn-primary" data-send' + (user ? "" : " disabled") + ">Отправить</button>" +
        "</div>" +
        all.map(function (c) {
          return '<div class="comment">' +
            '<span class="avatar" style="background:' + ML.user.color(c.author) + '">' + ML.user.initial(c.author) + "</span>" +
            '<div class="c-body"><div class="c-head">' +
            '<span class="c-name">' + ML.escape(c.author) + "</span>" +
            '<span class="c-date">' + ML.timeAgo(c.date) + "</span></div>" +
            '<div class="c-text">' + ML.escape(c.text) + "</div>" +
            '<div class="c-actions">' +
            '<button data-like>' + ML.icon("heart", 13) + " " + c.likes + "</button>" +
            '<button data-reply>' + ML.icon("reply", 13) + " Ответить</button>" +
            '<button data-flag>' + ML.icon("flag", 13) + " Пожаловаться</button>" +
            "</div></div></div>";
        }).join("");

      var send = ML.qs("[data-send]", body);
      if (send && !send.disabled) {
        send.addEventListener("click", function () {
          var ta = ML.qs("textarea", body);
          var text = ta.value.trim();
          if (!text) { ML.toast("Комментарий пустой"); return; }
          var arr = ML.store.get("comments_" + m.slug, []);
          arr.unshift({
            author: user.nick,
            text: text,
            date: "2025-06-10",
            likes: 0,
            avatar: 0
          });
          ML.store.set("comments_" + m.slug, arr);
          ML.toast("Комментарий опубликован");
          tabComments();
        });
      }

      ML.qsa("[data-like]", body).forEach(function (b) {
        b.addEventListener("click", function () {
          b.style.color = "var(--red)";
          var parts = b.textContent.trim().split(" ");
          b.innerHTML = ML.icon("heart", 13, 'fill="currentColor"') + " " + (parseInt(parts[parts.length - 1], 10) + 1);
        });
      });
      ML.qsa("[data-reply]", body).forEach(function (b) {
        b.addEventListener("click", function () {
          var name = b.closest(".comment").querySelector(".c-name").textContent;
          var ta = ML.qs("textarea", body);
          if (ta && !ta.disabled) { ta.value = name + ", "; ta.focus(); }
          else ML.toast("Сначала войдите");
        });
      });
      ML.qsa("[data-flag]", body).forEach(function (b) {
        b.addEventListener("click", function () { ML.toast("Жалоба отправлена (демо)"); });
      });
    }

    var tabs = { info: tabInfo, chapters: tabChapters, reviews: tabReviews, comments: tabComments };
    ML.qsa(".tab", root).forEach(function (t) {
      t.addEventListener("click", function () {
        ML.qsa(".tab", root).forEach(function (x) { x.classList.remove("active"); });
        t.classList.add("active");
        tabs[t.getAttribute("data-tab")]();
      });
    });
    tabInfo();

    /* ---------- действия ---------- */
    function syncFav() {
      var on = ML.favorites.has(m.slug);
      ML.qsa("[data-fav] span", root).forEach(function (s) {
        s.style.color = on ? "var(--red)" : "var(--muted)";
        s.innerHTML = ML.icon("heart", 17, on ? 'fill="currentColor"' : "");
      });
      var b2 = ML.qs("[data-fav2]", root);
      b2.innerHTML = ML.icon("heart", 16, on ? 'fill="currentColor"' : "") + (on ? " В закладках" : " В закладки");
    }
    ML.qsa("[data-fav], [data-fav2]", root).forEach(function (b) {
      b.addEventListener("click", function () { ML.favorites.toggle(m.slug); syncFav(); });
    });

    ML.qs("[data-subscribe]", root).addEventListener("click", function () {
      ML.toast("Подписка оформлена (демо)");
    });

    ML.qs("[data-share]", root).addEventListener("click", function () {
      var url = location.origin + location.pathname + "#/manga/" + m.slug;
      if (navigator.clipboard) navigator.clipboard.writeText(url).catch(function () {});
      ML.toast("Ссылка скопирована: " + url);
    });

    ML.qsa("#stars button", root).forEach(function (b) {
      b.addEventListener("click", function () {
        var v = parseInt(b.getAttribute("data-v"), 10);
        ML.store.set("votes_" + m.slug, v);
        ML.qsa("#stars button", root).forEach(function (x) {
          var on = parseInt(x.getAttribute("data-v"), 10) <= v;
          x.classList.toggle("on", on);
          x.innerHTML = ML.icon("star", 22, on ? 'fill="currentColor"' : "");
        });
        ML.qs("#vote-msg", root).textContent = "Ваша оценка: " + v + " из 5";
        ML.toast("Оценка сохранена");
      });
    });

    ML.lazy(root);
  });
})();
