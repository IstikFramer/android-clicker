# Арт-ассеты (pixel art: кот + ауры)

Финальные файлы:

```
assets/
├── icons/512/           # 5 иконок 512×512  ← основной деливерабл
├── icons/1024/          # те же иконки 1024×1024 (мастер)
├── covers/800x470/      # 5 обложек 800×470 ← основной деливерабл
├── covers/1920x1080/    # те же обложки 1920×1080 (мастер, 16:9)
├── alt/                 # вторые варианты каждого слота (512 / 800×470)
├── raw/                 # оригиналы генерации: заход 1
├── raw/v2/              # оригиналы генерации: заход 2
└── preview_final.jpg    # контактный лист финального набора
```

## Что выбрано

| Слот | Источник | Почему |
|---|---|---|
| icon_01 | заход 1 | пухлый кот, нимб, платформа — самая «иконочная» композиция |
| icon_02 | заход 1 | живее поза, ярче циан-аура |
| icon_03 | заход 1 (кроп) | у варианта 2 была белая рамка; здесь белые уголки срезаны кропом |
| icon_04 | заход 1 | честные чанки-пиксели силуэта |
| icon_05 | заход 2 | без декоративной рамки по краю |
| cover_06…10 | заход 2 | в заходе 1 модель дорисовала выдуманные заголовки, а в cover_09 — логотипы Nintendo Switch / Steam |

## Обработка

- Иконки: 1024 → 512 фильтром `box` (ровно 2×, пиксели не мылятся).
- Обложки: генерация 1376×768 → центр-кроп 1307×768 (ratio 800:470) → `lanczos` до 800×470.
  Мастер 1920×1080: центр-кроп 1365×768 → `point` (nearest) апскейл, чтобы края пикселей остались твёрдыми.

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

Во втором заходе к промптам обложек добавлялся только негатив
`no text, no letters, no logos, no watermark, no UI` — сама сцена не менялась.
