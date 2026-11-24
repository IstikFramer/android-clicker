# Контракты SPACE DIE

Все ID целей в нижнем регистре. Jupiter служит фоном и носителем ускорителя. Только активная цель имеет локальные физические координаты. Позиция измеряется в local units, длительность в sec, масса в game mass. Единичное направление безразмерно. Художественные величины не предназначены для прогноза реальных событий.

| weapon_id | target_id | power, целый процент |
| --- | --- | --- |
| railgun | mercury, venus, earth, mars, saturn | 10…100 |
| gungnir | mercury, venus, earth, mars, saturn | 100 |
| vera | те же цели и sun | 20…100 |

## Запрос и отчёт

ShotRequest наследует RefCounted. Поля включают уникальный за сеанс `shot_id: int`, `weapon_id: StringName`, `target_id: StringName`, `power: int`, конечный единичный `local_hit_dir: Vector3`, `country_id: String` и `seed: int`. Шаг мощности 1%. На Земле railgun требует двухбуквенный код страны/территории из каталога Godot или точную строку `Ocean`. На Земле для остальных оружий поле может быть пустым. На остальных целях требуется пустая строка. Невалидный запрос отклоняется. После fire вызывающая сторона рассматривает переданный запрос как неизменяемый.

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
