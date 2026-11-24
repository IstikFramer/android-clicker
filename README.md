# SPACE DIE · v0.1.0

В **этапе 03 из 08** можно посмотреть удар по планете. В Windows распакуйте весь ZIP и дважды нажмите **Impact-Demo.cmd**. Через секунду Земля расколется при мощности 50%. Для обычного атласа и настроек откройте **SPACE-DIE.exe**. [Скачать демо для Windows x64](https://github.com/IstikFramer/android-clicker/releases/download/v0.1.0-stage03/SPACE-DIE-0.1.0-win64.zip)

В настройках качества «Низкое» оставляет один упрощённый слой облаков и до 48 физических осколков. «Высокое» добавляет облачные тени, блики воды, детальный рельеф и до 160 физических осколков. «Ультра» позволяет физически моделировать все 480 ячеек Земли. [Низкое](docs/screenshots/stage03-low.jpg) · [Высокое](docs/screenshots/stage03-high.jpg) · [Удар](docs/screenshots/stage03-fracture.jpg)

В атласе ЛКМ выбирает точку, ПКМ вращает камеру, колесо меняет расстояние. В демонстрации после первого удара можно выбрать следующую точку и нажать пробел. Enter пропускает эффекты, Esc ставит сцену на паузу, R восстанавливает тело. Цифры населения и масштабы повреждения игровые.

## Запуск на Linux x86_64

Нужны Bash, Python 3, системный C-линкер, curl, unzip и sha256sum. Первый setup использует сеть. Из корня репозитория выполните

```bash
tools/setup_linux.sh
export PATH="$PWD/.tools/bin:${CARGO_HOME:-$HOME/.cargo}/bin:$PATH"
tools/build_native.sh debug
tools/smoke_linux.sh
godot --path godot
godot --path godot -- --test-impact earth 50
```

Для headless-машины достаточно smoke. В редакторе запускайте Main клавишей F6 из открытой главной сцены или F5 из проекта. M переключает звук. Кнопка «В меню» закрывает атлас. Настройки сохраняются в `user://settings.cfg`. Русский язык выбран по умолчанию, English доступен в настройках.

## Разработка на Windows x64

Используйте PowerShell, Python 3, Rustup и Visual Studio Build Tools с workload C++ для MSVC x64. Из корня проекта

```powershell
./tools/setup_windows.ps1
./tools/build_native.ps1 debug
python tools/check_godot.py --godot .tools/bin/Godot_v4.7.2-stable_win64_console.exe
& ./.tools/bin/Godot_v4.7.2-stable_win64.exe --path godot
```

Для запуска другой демонстрации из каталога распакованной игры выполните, например, `.\SPACE-DIE.exe -- --test-impact saturn 100 gungnir`. Параметры принимают ID цели, мощность и необязательный ID установки. Порядок пробной упаковки и проверки описан в [release_checklist.md](docs/release_checklist.md).

## Пересборка ресурсов

Карты и GLB включены в репозиторий. Для воспроизведения ресурсов используйте Python 3.12, зависимости из tools/requirements-assets.txt и Blender 4.3.2.

```bash
python3 -m venv .tools/art-env
.tools/art-env/bin/pip install -r tools/requirements-assets.txt
.tools/art-env/bin/python tools/fetch_assets.py
.tools/art-env/bin/python tools/bake_assets.py
python3 tools/bake_fractures.py --check
blender -b --python-exit-code 1 --python tools/bake_models.py
.tools/art-env/bin/python tools/verify_assets.py
```

Состав данных, точность маски и авторство описаны в [asset_credits.md](docs/asset_credits.md). После импорта Godot можно сохранить кадры сцен при наличии дисплея командой `godot --path godot --script res://tests/render_atlas.gd -- /tmp/atlas-frames`.

## Структура

- `godot/` содержит приложение, демонстрационные сцены, процедурные материалы и проверки контракта.
- `rust/` содержит workspace для чистого ядра, GDExtension и CLI. Для примера `printf '[0,1,0]\n' | (cd rust && cargo run --locked -q -p bake_cli)` проверяет локальное направление из JSON.
- `tools/` и `.github/workflows/` содержат воспроизводимый setup, нативную сборку и CI.

Версии, результаты запусков и открытые проверки приведены в [журнале этапа](docs/stage_status.md). Границы подсистем и форматы данных описаны в [архитектуре](docs/architecture.md) и [контрактах](docs/contracts.md).
