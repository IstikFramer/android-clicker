/* ============================================================
   MANGVERSE — данные манги
   ============================================================
   Как добавить: см. README.md. Коротко:

   {
     id: 'slug', title: 'Название', author: 'Автор', year: 2026,
     status: 'ongoing', rating: 9.0, views: 0,
     color: ['#8b5cf6', '#120b24'],
     genres: ['романтика'],
     description: '…',
     chapters: [
       // pages: number      → placeholder-страницы (SVG)
       // pages: [url, …]    → реальные изображения страниц
       ch(1, 'Первая', ['/images/manga/slug/page-01.jpg', '…'], '2026-09-16'),
     ],
   }
   ============================================================ */

const ch = (number, title, pages, date) => ({ number, title, pages, date })

export const manga = [
  {
    id: 'moon-mail',
    title: 'Лунная почта',
    author: 'Юлия Сорокина',
    artist: 'Вера Миронова',
    year: 2026,
    status: 'ongoing',
    rating: 9.2,
    views: 1207,
    color: ['#8b5cf6', '#120b24'],
    cover: '/images/manga/moon-mail/cover.jpg',
    genres: ['романтика', 'драма'],
    description:
      'Токио. Старшая школа. И таинственный почтовый ящик на крыше, который «пишет» только в полнолуние. Аой получает анонимные письма уже месяц, и почерк в последнем — её собственный. Рэн — единственный, кто знает про «Лунную почту», — может держать ключ ко всему. Но какую цену он за это просит? Тёмная романтика с элементами мистики.',
    chapters: [
      ch(
        1,
        'Первое письмо',
        [
          '/images/manga/moon-mail/page-01.jpg',
          '/images/manga/moon-mail/page-02.jpg',
          '/images/manga/moon-mail/page-03.jpg',
          '/images/manga/moon-mail/page-04.jpg',
          '/images/manga/moon-mail/page-05.jpg',
          '/images/manga/moon-mail/page-06.jpg',
          '/images/manga/moon-mail/page-07.jpg',
          '/images/manga/moon-mail/page-08.jpg',
          '/images/manga/moon-mail/page-09.jpg',
        ],
        '2026-09-16',
      ),
    ],
  },
]

/* ---------- Вспомогательное ---------- */

export const GENRES = [...new Set(manga.flatMap((m) => m.genres))]

export const totalChapters = manga.reduce((sum, m) => sum + m.chapters.length, 0)

export const totalViews = manga.reduce((sum, m) => sum + m.views, 0)

export function getManga(id) {
  return manga.find((m) => m.id === id)
}
