# SPACE DIE · v0.1.0

**Этап 04 из 08.** В Windows распакуйте весь архив и откройте **SPACE-DIE.exe**. Нажмите **«Начать»**, выберите планету, щёлкните по поверхности, задайте мощность и нажмите **«Огонь»**. Для быстрого знакомства **Impact-Demo.cmd** сразу запускает обычный выстрел по Земле при 50%. [Скачать для Windows x64](https://github.com/IstikFramer/android-clicker/releases/download/v0.1.0-stage04/SPACE-DIE-0.1.0-win64.zip)

ПКМ вращает орбиту, колесо приближает камеру. На Земле можно выбрать страну из списка или указать точку в океане. При смене цели установка проходит варп. После удара появляются отчёт и сообщение местной сети. Для следующего выстрела выберите точку на уцелевшей цели. Кнопка «Восстановить» возвращает выбранную планету, R сбрасывает весь сеанс. Esc приостанавливает сцену, Enter пропускает текущую последовательность.

В **«Настройки»** отдельно задаются размер окна, масштаб 3D от 50 до 125% и резкость изображения. Надписи сохраняют разрешение окна. При 100% сцена рисуется в родном разрешении, при 125% — с запасом пикселей для сглаживания. Низкий и высокий пресеты меняют детализацию облаков, рельеф, атмосферный край, блики и количество физических осколков. [Низкое](docs/screenshots/stage04-low.jpg) · [Высокое](docs/screenshots/stage04-orbit.jpg) · [Удар](docs/screenshots/stage04-impact.jpg) · [Рассеивание](docs/screenshots/stage04-dispersal.jpg)

## Запуск на Linux x86_64

Нужны Bash, Python 3, системный C-линкер, curl, unzip и sha256sum. Первый setup использует сеть. Из корня репозитория выполните

```bash
tools/setup_linux.sh
export PATH="$PWD/.tools/bin:${CARGO_HOME:-$HOME/.cargo}/bin:$PATH"
tools/build_native.sh debug
tools/smoke_linux.sh
godot --path godot
godot --path godot -- --railgun-demo
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
