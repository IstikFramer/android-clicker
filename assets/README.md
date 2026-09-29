# Арт-ассеты (pixel art, кот + ауры)

Структура:

```
assets/
├── raw/                 # оригиналы генерации (иконки 1024×1024, обложки 1376×768)
├── icons/
│   ├── 1024/            # иконки 1024×1024 (1:1) — мастер
│   └── 512/             # иконки 512×512 — готово под Play Store / launcher
├── covers/
│   ├── 1920x1080/       # обложки 1920×1080 (16:9) — мастер
│   └── 800x470/         # обложки 800×470 — готовая обрезка
└── preview_all.jpg      # контактный лист со всеми вариантами
```

Обработка: иконки даунскейлятся 1024→512 фильтром `box` (ровно 2×, пиксели не мылятся).
Обложки: центр-кроп до 16:9 → апскейл `point` (nearest) до 1920×1080 → центр-кроп 1838×1080 → 800×470.

## Промпты

| Файл | Промпт |
|---|---|
| icon_01 | pixel art game icon, cute chubby orange cat with glowing headphones, sitting on a dark purple cosmic platform, golden halo ring above head, glowing violet aura circle around cat, small gold sparkles, deep dark blue night sky background, chunky pixels, crisp retro style, centered composition |
| icon_02 | pixel art icon, adorable orange tabby cat wearing a glowing golden collar, floating pink pixels around, huge cyan aura orb behind the cat, dark navy space background with tiny stars, 16-bit retro game style, vibrant, high contrast |
| icon_03 | pixel art game icon, sleepy orange cat levitating with closed eyes, rainbow-colored aura ring, floating mage, dark purple galaxy background, golden cross sparkles, chunky retro pixels, mystic atmosphere |
| icon_04 | pixel art icon, orange cat silhouette filled with galaxy stars, bright pink and cyan aura glow outline, dark background, tiny floating squares, retro 32x32 style enlarged, game app icon, centered |
| icon_05 | pixel art icon, cute angry orange cat with electric blue lightning aura, cracked ground below, golden crown, dark red and purple sky, dramatic glow, chunky pixels, bold game icon |
| cover_06 | pixel art game cover, wide landscape, cute orange cat with glowing headphones sitting in the center of a dark cosmic field, giant glowing aura ring, golden orbit particles, aurora borealis in the night sky, stars and nebula, title space on the left, 16-bit retro style |
| cover_07 | pixel art game cover, epic scene: tiny orange cat levitating above a floating island, massive multicolored aura explosion behind it, dark galaxy with constellations, falling golden leaves, chunky pixels, cinematic lighting, 16:9 |
| cover_08 | pixel art wide game cover, night city rooftop, orange pixel cat wearing glowing headphones looking at a giant aura portal in the sky, purple and cyan glow, stars, retro game key art, 16:9 |
| cover_09 | pixel art game cover, split screen of 6 different glowing aura orbs (grey, blue, purple, gold, pink, rainbow) orbiting a central orange pixel cat, dark cosmic background, grid of rarities, vibrant retro style, 16:9 |
| cover_10 | pixel art game cover, orange cat meditating on a mountain top under a giant golden halo, rainbow aurora sky, floating runes and sparkles, epic mystical atmosphere, chunky retro pixels, 16:9 |

## Известные проблемы

- `cover_07`, `cover_08`, `cover_09`, `cover_10` — модель дорисовала выдуманные заголовки
  («PIXEL CAT ODYSSEY» и т.п.), а в `cover_09` ещё и логотипы Nintendo Switch / Steam.
  Их нужно перегенерировать с явным `no text, no logos` (см. следующую итерацию).
- `cover_06` — чистая (без текста), слева есть место под заголовок, но виден шов
  между «пустым» левым блоком и основной сценой.
