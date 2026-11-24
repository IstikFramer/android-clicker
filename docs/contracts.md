# Контракты SPACE DIE

Все ID целей в нижнем регистре. Jupiter служит фоном и носителем ускорителя. Только активная цель имеет локальные физические координаты. Позиция измеряется в local units, длительность в sec, масса в game mass. Единичное направление безразмерно. Художественные величины не предназначены для прогноза реальных событий.

| weapon_id | target_id | power, целый процент |
| --- | --- | --- |
| railgun | mercury, venus, earth, mars, saturn | 10…100 |
| gungnir | mercury, venus, earth, mars, saturn | 100 |
| vera | те же цели и sun | 20…100 |

## Запрос и отчёт

ShotRequest наследует RefCounted. Поля включают уникальный за сеанс `shot_id: int`, `weapon_id: StringName`, `target_id: StringName`, `power: int`, конечный единичный `local_hit_dir: Vector3`, `country_id: String` и `seed: int`. Шаг мощности 1%. На Земле railgun требует код записи countries.json (обычно ISO alpha-2; при коллизиях и отсутствии ISO используется ADM0_A3 Natural Earth) или точную строку `Ocean`. На Земле для остальных оружий поле может быть пустым. На остальных целях требуется пустая строка. Невалидный запрос отклоняется. После fire вызывающая сторона рассматривает переданный запрос как неизменяемый.

ImpactReport наследует RefCounted. Идентификаторы и мощность соответствуют активному запросу. Поля `damage_fraction`, `integrity` и `atmosphere_fraction` — доли в [0,1]. `crater_radius_game_km` — художественный радиус в игровых км, ноль при неприменимости. `simulated_population_loss: int` ограничен диапазоном 0…population. `energy_index` — конечный неотрицательный игровой индекс. `destroyed: bool`, `status_key: StringName` и `activated_fragment_count: int` описывают исход и число активированных фрагментов. Статусы твёрдых тел — solid_impact / solid_destroyed, Сатурна — gas_impact / gas_dispersed, Солнца — solar_impact / supernova. После публикации отчёт неизменяем по соглашению.

## События и жизненный цикл

EventBus на главном потоке предоставляет следующие сигналы

```text
target_selected(target_id)          weapon_selected(weapon_id)
shot_started(request)               phase_changed(shot_id, phase, progress)
impact_committed(report)            news_event(shot_id, target_id, event_key)
shot_finished(shot_id)              world_reset(reset_id)
settings_changed()
```

Цепочка допустимых переходов проходит через MENU → LOADING → IDLE → TRAVEL → AIM → CHARGING → FIRING → IMPACT → AFTERMATH → IDLE. Вход в CHARGING требует принятого запроса из AIM. Commit требует совпадения поколения, состояния, полей активного выстрела и валидного отчёта. Повторный commit отклоняется. Выход из IMPACT требует commit. PAUSED сохраняет предыдущую фазу. Reset через RESETTING восстанавливает IDLE. Возврат в меню вызывает abort. Оба действия увеличивают generation и восстанавливают масштаб времени. Отложенные операции передают свой исходный token. Идентификаторы принятых выстрелов не переиспользуются в рамках сеанса.

## Нативный API

На этапе 01 единственная опубликованная операция — `FractureBridge.get_api_version() -> int`, результат 1. В тестах экземпляр создаётся через ClassDB. Контракт этапа 03 предусматривает

```text
plan_impact(fragments: Array[Dictionary], params: Dictionary) -> Dictionary
gravity_step(positions: PackedVector3Array, masses: PackedFloat32Array, params: Dictionary) -> PackedVector3Array
```

Планирование не меняет сцену. Результат gravity_step — ускорения в local units/sec². До реализации требуются схемы словарей, единицы параметров и представление ошибок/несовместимой длины входов. После этапа 03 схемы стабилизируются. На границе gdext ошибки данных обрабатываются без panic.


## Атлас и прицел этапа 02

PlanetDefinition хранит id, name_key, type, visual_radius в единицах сцены, reference_radius_km, условный distance_game_km, population (int64), probes, ключ атмосферы, карты, tint/accent, rotation_rate в рад/с, fracture_count, damage_resistance и news_channel. У Юпитера и Солнца сопротивление −1 обозначает неприменимость, news_channel пуст. У газовых тел и звезды fracture_count равен нулю.

Нулевой меридиан направлен по +X, восточная долгота 90° по +Z, север по +Y. Геометрия печётся вокруг центра. Для сферы нормируем локальную вершину и вычисляем UV в шейдере, независимо от развёртки SphereMesh. Долгота равна atan2(z,x), широта равна asin(y). Горизонтальная координата равна fract(lon/TAU+0.5), вертикальная — 0.5-lat/PI. У полюсов долгота условна. Ограничение вертикального индекса последней строкой защищает южный полюс.

FractureBridge v1 дополнен тремя методами исследования поверхности. globe_uv(local_direction) возвращает Vector2 либо (-1,-1) для неверного направления. globe_direction(uv) возвращает единичный Vector3. pick_globe(origin, ray, radius) принимает локальные scene units, выбирает ближайший положительный корень и возвращает нормализованное направление. Нулевой вектор означает промах или неверный ввод. Hit пересчитывается в мировую точку через SpinPivot.to_global(local_hit_dir * visual_radius) в момент использования. Нажатие «Зафиксировать» сохраняет ShotRequest с полной тестовой мощностью и уникальным ID сеанса.

ID маски — R + 256×G. Код 0 соответствует Ocean. ID суши получается из трёх букв ADM0_A3 как 1+676a+26b+c при A=0. Географический поиск читает CPU Image без sRGB, mipmaps и интерполяции. AimArea использует бит 2, для будущих осколков зарезервирован физический слой 3. Оболочки, станции и декорации коллизий не имеют.

| Материал | Входы и пространство |
| --- | --- |
| planet_surface | day_map, normal_map, has_normal, tint, roughness, geology; локальная нормаль и освещение DirectionalLight3D |
| earth_surface | day_map, night_map (цвет), ocean_mask, damage_mask (линейные), damage_strength, sun_dir_local |
| clouds | cloud_map.a, density, cover, tint, sun_dir_local, u_time, damage_mask, damage_strength |
| atmosphere | tint, sun_dir_local; Fresnel и освещённый край |
| gas_giant | tint, belt, storm, u_time; широтные полосы, локальное пятно |
| saturn_rings | tint; UV.x от внутреннего до внешнего радиуса, UV.y вдоль кольца |
| sun_surface, solar_corona | u_time в секундах сцены; эмиссия и край короны |
| stars | направление EYEDIR; разреженные звёзды и пылевая полоса |

sun_dir_local направлен от центра к источнику света. Для каждого экземпляра используется обратный базис его SpinPivot и ось +Z локального DirectionalLight3D. damage_strength по умолчанию равна нулю. Повреждение подготовлено как вход материала для следующих этапов.
