/* ============================================================
   Обложки-заглушки. Реальной манги пока нет, поэтому каждая
   обложка — детерминированно сгенерированный SVG из названия.
   Когда появятся настоящие сканы, верни из data.js поле
   `cover` (URL) — и замени uri(): ML.Cover.uri(m) -> m.cover.
   ============================================================ */
(function () {
  "use strict";

  var ML = (window.ML = window.ML || {});
  var cache = {};

  var PALETTES = [
    ["#7c5cff", "#2dd4bf", "#0b1020"],
    ["#f4536c", "#7c5cff", "#120a1a"],
    ["#2dd4bf", "#4aa8e0", "#06121a"],
    ["#ff8b3d", "#f4536c", "#1a0c08"],
    ["#3ecf8e", "#2dd4bf", "#04140f"],
    ["#4aa8e0", "#7c5cff", "#070d1c"],
    ["#f5c344", "#ff8b3d", "#181002"],
    ["#b56cff", "#f4536c", "#12061a"],
    ["#9d82ff", "#3ecf8e", "#0a0f1c"],
    ["#e05c8a", "#ff8b3d", "#170813"],
    ["#5eead4", "#9d82ff", "#051018"],
    ["#f97316", "#facc15", "#160c02"]
  ];

  function hash(str) {
    var h = 2166136261;
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }

  function rnd(seed) {
    var s = seed || 1;
    return function () {
      s = (s * 1664525 + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  function esc(s) {
    return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  function wrap(title, perLine) {
    var words = title.split(" ");
    var lines = [];
    var cur = "";
    words.forEach(function (w) {
      if (!cur.length) { cur = w; return; }
      if ((cur + " " + w).length <= perLine) cur += " " + w;
      else { lines.push(cur); cur = w; }
    });
    if (cur) lines.push(cur);
    return lines.slice(0, 3);
  }

  function buildCover(title, sub, seedKey, w, h) {
    var seed = hash(seedKey || title);
    var r = rnd(seed);
    var pal = PALETTES[seed % PALETTES.length];
    var c1 = pal[0], c2 = pal[1], c3 = pal[2];
    var uid = "g" + seed.toString(36);
    var variant = Math.floor(r() * 4);

    var parts = [];
    parts.push(
      '<defs>' +
      '<linearGradient id="bg' + uid + '" x1="0" y1="0" x2="1" y2="1">' +
      '<stop offset="0" stop-color="' + c1 + '"/>' +
      '<stop offset="0.55" stop-color="' + c2 + '"/>' +
      '<stop offset="1" stop-color="' + c3 + '"/></linearGradient>' +
      '<radialGradient id="glow' + uid + '" cx="0.25" cy="0.18" r="0.85">' +
      '<stop offset="0" stop-color="#ffffff" stop-opacity="0.28"/>' +
      '<stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>' +
      '<linearGradient id="bot' + uid + '" x1="0" y1="0" x2="0" y2="1">' +
      '<stop offset="0" stop-color="' + c3 + '" stop-opacity="0"/>' +
      '<stop offset="0.62" stop-color="' + c3 + '" stop-opacity="0.9"/>' +
      '<stop offset="1" stop-color="#05070c" stop-opacity="0.99"/></linearGradient>' +
      '<pattern id="dots' + uid + '" width="11" height="11" patternUnits="userSpaceOnUse">' +
      '<circle cx="3" cy="3" r="1.5" fill="#ffffff" fill-opacity="0.14"/></pattern>' +
      "</defs>"
    );

    parts.push('<rect width="' + w + '" height="' + h + '" fill="url(#bg' + uid + ')"/>');
    parts.push('<rect width="' + w + '" height="' + h + '" fill="url(#glow' + uid + ')"/>');

    // силуэт / геометрия по варианту
    var cx = w * (0.5 + (r() - 0.5) * 0.3);
    var cy = h * (0.34 + r() * 0.08);
    if (variant === 0) {
      parts.push('<circle cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" r="' + (w * 0.3).toFixed(1) + '" fill="#ffffff" fill-opacity="0.1"/>');
      parts.push('<circle cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" r="' + (w * 0.19).toFixed(1) + '" fill="' + c3 + '" fill-opacity="0.45"/>');
    } else if (variant === 1) {
      parts.push('<path d="M0 ' + (h * 0.62).toFixed(0) + ' Q ' + (w * 0.5).toFixed(0) + " " + (h * 0.3).toFixed(0) + " " + w + " " + (h * 0.66).toFixed(0) + " L " + w + " " + h + " L 0 " + h + ' Z" fill="' + c3 + '" fill-opacity="0.55"/>');
      parts.push('<circle cx="' + (w * 0.72).toFixed(0) + '" cy="' + (h * 0.2).toFixed(0) + '" r="' + (w * 0.13).toFixed(0) + '" fill="#fff" fill-opacity="0.16"/>');
    } else if (variant === 2) {
      parts.push('<rect x="' + (-w * 0.2).toFixed(0) + '" y="' + (h * 0.2).toFixed(0) + '" width="' + (w * 1.5).toFixed(0) + '" height="' + (h * 0.16).toFixed(0) + '" fill="#ffffff" fill-opacity="0.12" transform="rotate(-18 ' + (w * 0.5).toFixed(0) + " " + (h * 0.5).toFixed(0) + ')"/>');
      parts.push('<rect x="' + (-w * 0.2).toFixed(0) + '" y="' + (h * 0.42).toFixed(0) + '" width="' + (w * 1.5).toFixed(0) + '" height="' + (h * 0.08).toFixed(0) + '" fill="' + c3 + '" fill-opacity="0.5" transform="rotate(-18 ' + (w * 0.5).toFixed(0) + " " + (h * 0.5).toFixed(0) + ')"/>');
    } else {
      parts.push('<path d="M' + (w * 0.5).toFixed(0) + " " + (h * 0.14).toFixed(0) + " L " + (w * 0.82).toFixed(0) + " " + (h * 0.52).toFixed(0) + " L " + (w * 0.18).toFixed(0) + " " + (h * 0.52).toFixed(0) + ' Z" fill="#ffffff" fill-opacity="0.12"/>');
      parts.push('<circle cx="' + (w * 0.5).toFixed(0) + '" cy="' + (h * 0.44).toFixed(0) + '" r="' + (w * 0.1).toFixed(0) + '" fill="' + c3 + '" fill-opacity="0.6"/>');
    }

    parts.push('<rect width="' + w + '" height="' + h + '" fill="url(#dots' + uid + ')"/>');
    parts.push('<rect y="' + (h * 0.52).toFixed(0) + '" width="' + w + '" height="' + (h * 0.48).toFixed(0) + '" fill="url(#bot' + uid + ')"/>');

    // текст
    var lines = wrap(title, w > 240 ? 17 : 15);
    var fs = w > 240 ? 27 : 21;
    var lh = fs * 1.16;
    var startY = h - 46 - (lines.length - 1) * lh;
    lines.forEach(function (line, i) {
      parts.push(
        '<text x="' + (w * 0.07).toFixed(0) + '" y="' + (startY + i * lh).toFixed(1) +
        '" font-family="Arial, Helvetica, sans-serif" font-weight="800" font-size="' + fs +
        '" fill="#ffffff" stroke="' + c3 + '" stroke-width="4" paint-order="stroke fill" letter-spacing="-0.4">' +
        esc(line) + "</text>"
      );
    });

    if (sub) {
      parts.push(
        '<text x="' + (w * 0.07).toFixed(0) + '" y="' + (h - 20).toFixed(0) +
        '" font-family="Arial, Helvetica, sans-serif" font-weight="700" font-size="' + Math.round(fs * 0.5) +
        '" fill="#ffffff" fill-opacity="0.66" letter-spacing="1.6">' + esc(sub.toUpperCase()) + "</text>"
      );
    }

    parts.push('<rect x="0.5" y="0.5" width="' + (w - 1) + '" height="' + (h - 1) + '" fill="none" stroke="#ffffff" stroke-opacity="0.09"/>');

    return '<svg xmlns="http://www.w3.org/2000/svg" width="' + w + '" height="' + h +
      '" viewBox="0 0 ' + w + " " + h + '">' + parts.join("") + "</svg>";
  }

  ML.Cover = {
    svg: function (title, sub, seedKey, w, h) {
      return buildCover(title, sub, seedKey, w, h);
    },
    uri: function (title, sub, seedKey, w, h) {
      w = w || 300; h = h || 420;
      var key = (seedKey || title) + "|" + w + "x" + h + "|" + sub;
      if (cache[key]) return cache[key];
      var svg = buildCover(title, sub, seedKey, w, h);
      var uri = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
      cache[key] = uri;
      return uri;
    },
    /* Страница главы: заглушка вместо настоящего скана */
    pageSvg: function (title, chapter, pageNum, total) {
      var seed = hash(title + "|" + chapter + "|" + pageNum);
      var r = rnd(seed);
      var w = 800, h = 1130;
      var p = [];
      p.push('<defs>' +
        '<pattern id="halftone" width="18" height="18" patternUnits="userSpaceOnUse">' +
        '<circle cx="5" cy="5" r="2.4" fill="#0e1117" fill-opacity="0.12"/></pattern>' +
        "</defs>");
      p.push('<rect width="' + w + '" height="' + h + '" fill="#f3f4f6"/>');
      p.push('<rect width="' + w + '" height="' + h + '" fill="url(#halftone)"/>');

      // рамки панелей
      var panels = [
        [50, 60, 700, 300],
        [50, 400, 330, 260],
        [420, 400, 330, 260],
        [50, 700, 700, 300]
      ];
      panels.forEach(function (rect, i) {
        var x = rect[0], y = rect[1], pw = rect[2], ph = rect[3];
        var g = 200 + Math.floor(r() * 40);
        p.push('<rect x="' + x + '" y="' + y + '" width="' + pw + '" height="' + ph + '" fill="rgb(' + g + "," + g + "," + (g + 4) + ')" stroke="#14181f" stroke-width="4"/>');
        // «динамика» внутри панели
        p.push('<path d="M' + x + " " + (y + ph) + " L " + (x + pw) + " " + y + '" stroke="#14181f" stroke-opacity="0.12" stroke-width="2"/>');
        p.push('<circle cx="' + (x + pw * (0.25 + r() * 0.5)).toFixed(0) + '" cy="' + (y + ph * (0.3 + r() * 0.4)).toFixed(0) + '" r="' + (30 + r() * 50).toFixed(0) + '" fill="#14181f" fill-opacity="0.12"/>');
      });

      p.push('<rect x="0" y="0" width="' + w + '" height="120" fill="#0e1117"/>');
      p.push('<text x="40" y="60" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="800" fill="#ffffff">' + esc(title) + "</text>");
      p.push('<text x="40" y="95" font-family="Arial, Helvetica, sans-serif" font-size="22" fill="#8b95a7">Глава ' + esc(chapter) + " · страница " + pageNum + " из " + total + "</text>");
      p.push('<text x="40" y="' + (h - 45) + '" font-family="Arial, Helvetica, sans-serif" font-size="22" fill="#6b7484">' +
        "Демонстрационная страница: реальные сканы тайтла ещё не загружены" + "</text>");
      return '<svg xmlns="http://www.w3.org/2000/svg" width="' + w + '" height="' + h + '" viewBox="0 0 ' + w + " " + h + '">' + p.join("") + "</svg>";
    },
    pageUri: function (title, chapter, pageNum, total) {
      var key = "page|" + title + "|" + chapter + "|" + pageNum;
      if (cache[key]) return cache[key];
      var uri = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(this.pageSvg(title, chapter, pageNum, total));
      cache[key] = uri;
      return uri;
    }
  };
})();
