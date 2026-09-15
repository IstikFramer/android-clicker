"""LIFE OS — хранилище пользовательских настроек (JSON в профиле пользователя)."""
from __future__ import annotations

import json
from typing import Any, Callable

from PySide6.QtCore import QTimer

from . import config as cfg

DEFAULTS: dict[str, Any] = {
    "accent": "cyan",
    "background": "bg_main.jpg",
    "glass_opacity": 55,      # % прозрачности панелей
    "glow_strength": 60,      # % силы свечения
    "anim_speed": 100,        # % скорости анимаций
    "corner_radius": 18,      # px радиус скруглений
    "ui_scale": 100,          # % масштаба интерфейса
    "fps_limit": 60,          # 30 / 60 / 120
    "animations": True,
    "power_saving": False,
    "heavy_effects": True,
    "autostart": False,
    "start_minimized": False,
    "close_to_tray": True,
    "tray_notifications": True,
    "language": "Русский",
    "eula_accepted": False,
    "eula_version": "",
}


class Settings:
    """Настройки с автосохранением и подпиской на изменения."""

    def __init__(self):
        self._data = dict(DEFAULTS)
        self._subs: list[Callable[[str, Any], None]] = []
        self._save_timer: QTimer | None = None
        self.load()

    def _save_later(self):
        """Запись на диск не чаще раза в 400 мс.

        Во время перетаскивания слайдера значение меняется десятки раз в
        секунду — писать файл на каждый пиксель незачем.
        """
        if self._save_timer is None:
            self._save_timer = QTimer()
            self._save_timer.setSingleShot(True)
            self._save_timer.timeout.connect(self.save)
        self._save_timer.start(400)

    # --------------------------------------------------------------- файл
    def load(self):
        try:
            if cfg.SETTINGS_FILE.exists():
                raw = json.loads(cfg.SETTINGS_FILE.read_text("utf-8"))
                for k, v in raw.items():
                    if k in DEFAULTS and isinstance(v, type(DEFAULTS[k])):
                        self._data[k] = v
        except (OSError, ValueError):
            pass  # битый файл — работаем на значениях по умолчанию

    def save(self):
        try:
            cfg.USER_DIR.mkdir(parents=True, exist_ok=True)
            cfg.SETTINGS_FILE.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2), "utf-8"
            )
        except OSError:
            pass

    def reset(self):
        self._data = dict(DEFAULTS)
        self.save()
        for key, val in self._data.items():
            self._emit(key, val)

    # -------------------------------------------------------------- доступ
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any, save: bool = True):
        if self._data.get(key) == value:
            return
        self._data[key] = value
        if save:
            self._save_later()
        self._emit(key, value)

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    # ------------------------------------------------------------ подписка
    def subscribe(self, fn: Callable[[str, Any], None]):
        self._subs.append(fn)

    def _emit(self, key: str, value: Any):
        for fn in list(self._subs):
            fn(key, value)

    # ------------------------------------------------- производные величины
    @property
    def glass_alpha(self) -> float:
        """Прозрачность стеклянных панелей 0.02…0.13."""
        return 0.02 + (self.get("glass_opacity") / 100.0) * 0.11

    @property
    def glow_alpha(self) -> float:
        """Множитель силы свечения 0…1.3."""
        return (self.get("glow_strength") / 100.0) * 1.3

    @property
    def speed(self) -> float:
        return self.get("anim_speed") / 100.0


settings = Settings()
