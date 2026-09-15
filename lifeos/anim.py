"""LIFE OS — общий движок анимаций.

Вместо десятка независимых QTimer'ов с разной частотой (главная причина
рваных ~10 FPS в 0.1) здесь один тактовый генератор на всё приложение.
Виджеты подписываются на кадр, и если подписчиков нет — таймер спит.

Дополнительно:
  * реальный предел FPS (30 / 60 / 120) из настроек;
  * глобальный множитель скорости анимаций;
  * тумблер «без анимаций» — подписчики просто перестают получать кадры;
  * dt в секундах, поэтому скорость движения не зависит от частоты кадров;
  * Spring/Tween — лёгкие интерполяторы для плавных значений.
"""
from __future__ import annotations

import time
from typing import Callable

from PySide6.QtCore import QObject, Qt, QTimer


class AnimationDriver(QObject):
    """Единый тактовый генератор кадров (singleton)."""

    _inst: "AnimationDriver | None" = None

    def __init__(self):
        super().__init__()
        self._subs: dict[int, Callable[[float], None]] = {}
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.PreciseTimer)
        self._timer.timeout.connect(self._tick)
        self._last = time.perf_counter()
        self._fps = 60
        self._speed = 1.0
        self._enabled = True
        self._frames = 0
        self._fps_real = 0.0
        self._fps_mark = self._last

    # ------------------------------------------------------------- доступ
    @classmethod
    def instance(cls) -> "AnimationDriver":
        if cls._inst is None:
            cls._inst = AnimationDriver()
        return cls._inst

    # ---------------------------------------------------------- параметры
    @property
    def fps(self) -> int:
        return self._fps

    def set_fps(self, fps: int):
        self._fps = max(15, min(240, int(fps)))
        if self._timer.isActive():
            self._timer.start(max(1, round(1000 / self._fps)))

    @property
    def speed(self) -> float:
        return self._speed

    def set_speed(self, mult: float):
        self._speed = max(0.0, min(3.0, float(mult)))

    @property
    def enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, on: bool):
        self._enabled = bool(on)
        self._sync()

    @property
    def real_fps(self) -> float:
        return self._fps_real

    # -------------------------------------------------------------- такт
    def subscribe(self, owner: QObject, fn: Callable[[float], None]):
        self._subs[id(owner)] = fn
        owner.destroyed.connect(lambda *_, k=id(owner): self._subs.pop(k, None))
        self._sync()

    def unsubscribe(self, owner: QObject):
        self._subs.pop(id(owner), None)
        self._sync()

    def _sync(self):
        need = bool(self._subs) and self._enabled
        if need and not self._timer.isActive():
            self._last = time.perf_counter()
            self._timer.start(max(1, round(1000 / self._fps)))
        elif not need and self._timer.isActive():
            self._timer.stop()

    def _tick(self):
        now = time.perf_counter()
        dt = min(0.1, now - self._last)   # защита от скачка после фриза
        self._last = now

        self._frames += 1
        if now - self._fps_mark >= 0.5:
            self._fps_real = self._frames / (now - self._fps_mark)
            self._frames = 0
            self._fps_mark = now

        step = dt * self._speed
        for fn in list(self._subs.values()):
            fn(step)


driver = AnimationDriver.instance


# --------------------------------------------------------------- значения
class Spring:
    """Пружинное сглаживание значения — основа «живого» UI без рывков."""

    def __init__(self, value: float = 0.0, stiffness: float = 12.0):
        self.value = float(value)
        self.target = float(value)
        self.k = stiffness

    def set(self, target: float):
        self.target = float(target)

    def snap(self, value: float):
        self.value = self.target = float(value)

    @property
    def done(self) -> bool:
        return abs(self.target - self.value) < 1e-3

    def step(self, dt: float) -> float:
        # экспоненциальное приближение, независимое от частоты кадров
        t = 1.0 - pow(2.718281828, -self.k * dt)
        self.value += (self.target - self.value) * t
        if abs(self.target - self.value) < 1e-3:
            self.value = self.target
        return self.value


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - pow(1.0 - t, 3)


def ease_in_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t
