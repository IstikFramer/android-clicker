# SPACE DIE · v0.1.0

Одиночная офлайн-песочница кинематографического разрушения планет. **Этап 01 из 08** реализует меню, настройки, демонстрационную орбиту и нативный интерфейс. В демосцене можно вращать камеру вокруг процедурной сферы, менять масштаб и восстанавливать начальный вид. Оружие, разрушение и новости относятся к следующим этапам.

## Запуск на Linux x86_64

Нужны Bash, Python 3, системный C-линкер, curl, unzip и sha256sum. Первый setup использует сеть. Из корня репозитория выполните

```bash
tools/setup_linux.sh
export PATH="$PWD/.tools/bin:${CARGO_HOME:-$HOME/.cargo}/bin:$PATH"
tools/build_native.sh debug
tools/smoke_linux.sh
godot --path godot
```

Для headless-машины достаточно smoke. В редакторе запускайте Main клавишей F6 из открытой главной сцены или F5 из проекта. В демонстрации ПКМ вращает камеру, колесо меняет масштаб, Esc ставит на паузу, R восстанавливает вид, M переключает звук. Кнопка «В меню» завершает демонстрацию. Настройки сохраняются в `user://settings.cfg`. Русский язык выбран по умолчанию, English доступен в настройках.

## Разработка на Windows x64

Используйте PowerShell, Python 3, Rustup и Visual Studio Build Tools с workload C++ для MSVC x64. Из корня проекта

```powershell
./tools/setup_windows.ps1
./tools/build_native.ps1 debug
python tools/check_godot.py --godot .tools/bin/Godot_v4.7.2-stable_win64_console.exe
& ./.tools/bin/Godot_v4.7.2-stable_win64.exe --path godot
```

Windows-сборка для игрока будет распространяться в ZIP с EXE, PCK и нативными библиотеками. Порядок пробной упаковки и проверки описан в [release_checklist.md](docs/release_checklist.md).

## Структура

- `godot/` содержит приложение, демонстрационные сцены, процедурные материалы и проверки контракта.
- `rust/` содержит workspace для чистого ядра, GDExtension и CLI. Для примера `printf '[0,1,0]\n' | (cd rust && cargo run --locked -q -p bake_cli)` проверяет локальное направление из JSON.
- `tools/` и `.github/workflows/` содержат воспроизводимый setup, нативную сборку и CI.

Версии, результаты запусков и открытые проверки приведены в [журнале этапа](docs/stage_status.md). Границы подсистем и форматы данных описаны в [архитектуре](docs/architecture.md) и [контрактах](docs/contracts.md).
