// База данных MangaHub. Ведётся вручную (без генератора).
// Чтобы добавить тайтл — скопируйте объект в manga[], обложка и страницы —
// обычные файлы в assets/img/<slug>/. Пути в pages[] — относительно корня сайта.
window.MANGA_DB = {
  "meta": {
    "today": "2026-09-16",
    "note": "Первый реальный тайтл каталога: цветная обложка, чёрно-белые страницы, пузыри на русском."
  },
  "genres": [
    { "name": "Романтика", "slug": "romance" },
    { "name": "Школа", "slug": "school" },
    { "name": "Повседневность", "slug": "slice-of-life" },
    { "name": "Драма", "slug": "drama" },
    { "name": "Экшен", "slug": "action" },
    { "name": "Приключения", "slug": "adventure" },
    { "name": "Комедия", "slug": "comedy" },
    { "name": "Фэнтези", "slug": "fantasy" },
    { "name": "Ужасы", "slug": "horror" },
    { "name": "Детектив", "slug": "detective" },
    { "name": "Психология", "slug": "psychological" },
    { "name": "Боевые искусства", "slug": "martial-arts" },
    { "name": "Сверхъестественное", "slug": "supernatural" },
    { "name": "Мистика", "slug": "mystery" },
    { "name": "История", "slug": "historical" },
    { "name": "Вампиры", "slug": "vampires" },
    { "name": "Постапокалипсис", "slug": "post-apocalyptic" },
    { "name": "Путешествие во времени", "slug": "time-travel" },
    { "name": "Трагедия", "slug": "tragedy" },
    { "name": "Триллер", "slug": "thriller" },
    { "name": "Спорт", "slug": "sports" },
    { "name": "Космос", "slug": "space" },
    { "name": "Меха", "slug": "mecha" },
    { "name": "Гарем", "slug": "harem" },
    { "name": "Игры", "slug": "games" },
    { "name": "Выживание", "slug": "survival" },
    { "name": "Реинкарнация", "slug": "reincarnation" },
    { "name": "Кулинария", "slug": "cooking" },
    { "name": "Музыка", "slug": "music" },
    { "name": "Сверхспособности", "slug": "superpowers" }
  ],
  "statuses": [
    { "key": "ongoing", "name": "Выпускается" },
    { "key": "completed", "name": "Завершено" },
    { "key": "anons", "name": "Анонс" },
    { "key": "frozen", "name": "Заморожено" },
    { "key": "dropped", "name": "Покинуто" }
  ],
  "types": [
    { "key": "manga", "name": "Манга" },
    { "key": "manhwa", "name": "Манхва" },
    { "key": "manhua", "name": "Маньхуа" },
    { "key": "comic", "name": "Комикс" }
  ],
  "publishers": ["Kodansha", "Shueisha", "Kadokawa", "Naver Webtoon", "Kakao Page", "Tencent Animation", "Image Comics", "Dark Horse", "Indie"],
  "translators": ["Sakura Scans RU"],
  "manga": [
    {
      "slug": "poezd-v-742",
      "title": "Поезд в 7:42",
      "altTitle": "7時42分の電車 (7-ji 42-fun no Densha)",
      "type": "manga",
      "typeName": "Манга",
      "year": 2026,
      "status": "ongoing",
      "statusName": "Выпускается",
      "age": "16+",
      "country": "Япония",
      "publisher": "Kodansha (KCデザート)",
      "translator": "Sakura Scans RU",
      "authors": ["Аяцуки Канамэ"],
      "artists": ["Аяцуки Канамэ"],
      "genres": ["Романтика", "Школа", "Повседневность", "Драма"],
      "description": "Мио Аясэ никогда не опаздывает. Но с той весной она ездит в школу только поездом в 7:42 — тем самым, который её дедушка, начальник станции Сибуя, провожал каждое утро сорок лет подряд. На платформе всё напоминает о нём: стёртая метка на столбе, где он стоял, старые часы в её комнате, спешащие на три минуты, которых она принципиально не чинит.\n\nВ том же вагоне, в одном и том же месте, каждое утро стоит молчаливый переводной ученик Харуто Кано и рисует в скетчбуке поезда. Однажды в толчее Мио роняет ламинированный проездной 1987 года — последний билет дедушки — и Харуто поднимает его раньше, чем она успевает вдохнуть. Он узнаёт билет с одного взгляда: зелёная серия 205. Потому что дед Харуто был машинистом того самого поезда в 7:42.\n\nДве семьи, один поезд и сорок лет расписаний, которые пересеклись на платформе Сибуи. История о том, как время, которое мы теряем, возвращается к нам людьми, которых мы встречаем.",
      "rating": 9.4,
      "votes": 214,
      "views": 18400,
      "favorites": 1260,
      "subscribers": 890,
      "cover": "assets/img/train-742/cover.jpg",
      "chaptersCount": 1,
      "lastChapter": "1",
      "lastChapterDate": "2026-09-16",
      "updated": "2026-09-16",
      "chapters": [
        {
          "number": "1",
          "title": "Поезд в 7:42",
          "volume": 1,
          "date": "2026-09-16",
          "views": 3120,
          "kind": "chapter",
          "pages": [
            "assets/img/train-742/ch1/p01.jpg",
            "assets/img/train-742/ch1/p02.jpg",
            "assets/img/train-742/ch1/p03.jpg",
            "assets/img/train-742/ch1/p04.jpg",
            "assets/img/train-742/ch1/p05.jpg",
            "assets/img/train-742/ch1/p06.jpg",
            "assets/img/train-742/ch1/p07.jpg",
            "assets/img/train-742/ch1/p08.jpg",
            "assets/img/train-742/ch1/p09.jpg"
          ]
        }
      ],
      "comments": [
        { "author": "SakuraTears", "text": "Плакала на сцене с билетом. «Мой дед водил этот поезд» — мурашки.", "date": "2026-09-16", "likes": 84, "avatar": 0 },
        { "author": "НочнойЧитатель", "text": "Часы, спешащие на три минуты, — деталь, которая выстрелит позже, я уверен.", "date": "2026-09-16", "likes": 61, "avatar": 1 },
        { "author": "RinNoHana", "text": "Перевод пузырей аккуратный, шрифты читаются, фон честно японский. Респект команде.", "date": "2026-09-16", "likes": 47, "avatar": 2 },
        { "author": "ДедИнсайд", "text": "Как же нарисован дождь в финале… и «до встречи в 7:42». Жду вторую главу как поезд.", "date": "2026-09-16", "likes": 39, "avatar": 3 },
        { "author": "mizuki_fan", "text": "Брелок-мишка появляется в каждом эпизоде, это теперь мой любимый пасхальный тег.", "date": "2026-09-16", "likes": 28, "avatar": 4 },
        { "author": "ArtemScans", "text": "Скринтоны, ракурсы, темп — уровень печатного тома. Первая глава зашла целиком за минуту.", "date": "2026-09-16", "likes": 22, "avatar": 5 }
      ],
      "reviews": [
        { "author": "ЛунаБезОблаков", "title": "Тихая драма о времени и людях", "score": 5, "text": "Редкий случай, когда романтика начинается не с «упала в объятия», а с проездного 1987 года. Мелочи продуманы: часы, метка на столбе, скетчбук.", "date": "2026-09-16" },
        { "author": "KuroNeko", "title": "Перевод и леттеринг образцовые", "score": 5, "text": "Пузыри на русском читаются как родные, весь фон и ономатопея — японские, никаких артефактов. Так надо переводить.", "date": "2026-09-16" },
        { "author": "Гость404", "title": "Хочется больше глав", "score": 4, "text": "Одна глава — мало. Но как финальный кадр с зонтом и отражениями в лужах — это надо видеть.", "date": "2026-09-16" }
      ]
    }
  ]
};
