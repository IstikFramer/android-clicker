# MANGVERSE — манга-платформа 2026

Многостраничный манга-сайт в тёмно-фиолетово-чёрном стиле 2026: глассморфизм, неоновые
свечения, плавающая навигация. Стек: **React + Vite + React Router**.

## Запуск

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # production-сборка → dist/
npm run preview    # предпросмотр сборки
```

## Страницы

| Маршрут            | Страница                                                        |
| ------------------ | --------------------------------------------------------------- |
| `/`                | Главная: hero-баннер, топы, новые главы, жанры, CTA             |
| `/catalog`         | Каталог: поиск, фильтры по жанрам/статусу, сортировка           |
| `/manga/:id`       | Страница манги: описание, главы, похожие, избранное             |
| `/reader/:id/:n`   | Читалка: страница за страницей, прогресс, клавиши ← →           |
| `/search`          | Поиск по названию, автору, жанру                                |
| `/rankings`        | Ранки: по рейтингу / по просмотрам                              |
| `/favorites`       | Избранное (localStorage)                                        |

## Как выгрузить свои манги

Все данные лежат в **`src/data/manga.js`** — это единственный файл, который нужно менять.

```js
{
  id: 'unique-slug',          // уникальный slug (латиница)
  title: 'Название',
  author: 'Автор / студия',
  year: 2026,
  status: 'ongoing',          // 'ongoing' | 'done'
  rating: 9.0,                // 0–10
  views: 123456,
  color: ['#7c3aed', '#0f0a1f'], // градиент обложки (CSS-арт)
  genres: ['фантастика'],      // слова из GENRES (или новые — подхватятся сами)
  description: 'Описание серии…',
  chapters: [
    { number: 1, title: 'Первая', date: '2026-09-16', pages: 14 },
    // ВАРИАНТ С РЕАЛЬНЫМИ СТРАНИЦАМИ:
    // { number: 2, title: 'Вторая', date: '2026-09-17',
    //   pages: ['https://…/page-1.jpg', 'https://…/page-2.jpg'] },
  ],
}
```

- `pages: number` → читалка показывает сгенерированные placeholder-страницы (SVG).
- `pages: [url, …]` → читалка показывает реальные изображения страниц.
- Обложка пока — CSS-градиент с типографикой (`color: [c1, c2]`). Подключение
  реальных обложек: добавить поле `cover` и подхватить его в `src/components/CoverArt.jsx`.

Избранное — localStorage, ключ `mangverse:favorites`.

## Сгенерированные ассеты (ровно 10 изображений)

- `public/images/icons/` — 8 UI-иконок на изумрудной плашке (логотип, поиск, книга,
  звезда, колокольчик, юзер, настройки, сетка жанров). Современный flat-3D стиль,
  без анимешности. Кроп и скругление углов — `tools/fix_icons2.py` (Pillow).
- `public/images/bg/hero.jpg` — фон главной (фиолетовые стеклянные волны + зелёная искра).
- `public/images/bg/catalog.jpg` — тёмный фон внутренних страниц.

## Структура

```
index.html            — шрифты Unbounded/Inter, favicon
public/images/        — 10 сгенерированных изображений
src/
  data/manga.js       ← сюда выгружаются манги
  lib/utils.js        — форматирование (просмотры, даты, плюралы)
  lib/storage.js      — избранное (localStorage)
  lib/pages.js        — генератор placeholder-страниц (SVG)
  components/         — Icon, CoverArt, MangaCard, FavButton, Navbar, Footer
  pages/              — Home, Catalog, MangaPage, Reader, SearchPage, Rankings, Favorites
  styles.css          — весь дизайн (токены в :root)
```
