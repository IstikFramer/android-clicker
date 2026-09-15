"""LIFE OS — векторные иконки.

Иконки описаны как SVG-строки и рендерятся в QIcon любого размера и цвета
через QSvgRenderer. Никаких растровых артефактов, идеальная чёткость
на любом DPI, цвет подстраивается под акцент темы.
"""
from __future__ import annotations

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

# Штрих-иконки 24x24, стиль Lucide: тонкие линии, скруглённые концы.
_SVG: dict[str, str] = {
    "home": """
        <path d="M3 10.2 12 3l9 7.2V20a1.5 1.5 0 0 1-1.5 1.5h-4.2v-6.3H9.7v6.3H5.5A1.5 1.5 0 0 1 4 20z"/>
    """,
    "sliders": """
        <path d="M4 7h10M18 7h2M4 12h3M11 12h9M4 17h7M15 17h5"/>
        <circle cx="16" cy="7" r="2.1"/><circle cx="9" cy="12" r="2.1"/><circle cx="13" cy="17" r="2.1"/>
    """,
    "info": """
        <circle cx="12" cy="12" r="9"/>
        <path d="M12 11v5.5M12 7.7v.6"/>
    """,
    "sparkles": """
        <path d="M12 3.5 13.7 9l5.5 1.7-5.5 1.7L12 18l-1.7-5.6L4.8 10.7 10.3 9z"/>
        <path d="M18.5 3.5v3M20 5h-3M6 17v2.6M7.3 18.3H4.7"/>
    """,
    "shield": """
        <path d="M12 3.2 5 6v5.4c0 4.2 2.9 8.1 7 9.4 4.1-1.3 7-5.2 7-9.4V6z"/>
        <path d="m9.2 12 2 2 3.6-3.8"/>
    """,
    "mail": """
        <rect x="3" y="5.5" width="18" height="13" rx="2.2"/>
        <path d="m3.8 7 7.1 5.3a2 2 0 0 0 2.4 0L20.3 7"/>
    """,
    "palette": """
        <path d="M12 3.2a8.8 8.8 0 0 0 0 17.6c1.2 0 1.9-.8 1.9-1.8 0-.5-.2-.9-.5-1.2-.3-.4-.5-.7-.5-1.2 0-1 .8-1.8 1.8-1.8h1.6a4.5 4.5 0 0 0 4.5-4.5c0-3.9-3.9-7.1-8.8-7.1z"/>
        <circle cx="7.6" cy="11.4" r="1.15"/><circle cx="10.4" cy="7.4" r="1.15"/>
        <circle cx="15.3" cy="7.9" r="1.15"/>
    """,
    "gauge": """
        <path d="M4.2 17a9 9 0 1 1 15.6 0"/>
        <path d="m14.6 10.6-3 3.4"/><circle cx="12" cy="15" r="1.4"/>
    """,
    "monitor": """
        <rect x="3" y="4.5" width="18" height="12.5" rx="2.2"/>
        <path d="M9 20.5h6M12 17v3.5"/>
    """,
    "power": """
        <path d="M12 3.5v8"/>
        <path d="M17.6 6.9a8 8 0 1 1-11.2 0"/>
    """,
    "wrench": """
        <path d="M14.8 6.3a3.9 3.9 0 0 0 5 5l-8.4 8.4a2.2 2.2 0 0 1-3.1-3.1z"/>
        <path d="M14.8 6.3 17.6 3.5"/>
    """,
    "minus": """<path d="M5 12h14"/>""",
    "square": """<rect x="5.5" y="5.5" width="13" height="13" rx="2.6"/>""",
    "restore": """
        <rect x="4.5" y="7.5" width="11" height="11" rx="2.4"/>
        <path d="M8.5 7.5v-1a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-1"/>
    """,
    "close": """<path d="M6.5 6.5 17.5 17.5M17.5 6.5 6.5 17.5"/>""",
    "chevron_left": """<path d="m14.5 6.5-5.5 5.5 5.5 5.5"/>""",
    "chevron_right": """<path d="m9.5 6.5 5.5 5.5-5.5 5.5"/>""",
    "check": """<path d="m5.5 12.5 4.2 4.2 8.8-9.4"/>""",
    "copy": """
        <rect x="8.5" y="8.5" width="11" height="11" rx="2.2"/>
        <path d="M15.5 8.5v-2a2 2 0 0 0-2-2h-7a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h2"/>
    """,
    "external": """
        <path d="M13.5 4.5H19.5V10.5"/><path d="M19.5 4.5 11 13"/>
        <path d="M18 14.5v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8.5a2 2 0 0 1 2-2h4"/>
    """,
    "refresh": """
        <path d="M20 12a8 8 0 1 1-2.6-5.9"/><path d="M20.2 4.5v4.2H16"/>
    """,
    "bell": """
        <path d="M18 9.5a6 6 0 1 0-12 0c0 5-2 6.5-2 6.5h16s-2-1.5-2-6.5z"/>
        <path d="M13.8 19.5a2 2 0 0 1-3.6 0"/>
    """,
    "tray": """
        <path d="M3.5 13.5h4.2l1.6 3h5.4l1.6-3h4.2"/>
        <path d="M5.4 6.2 3.5 13.5v3.8a1.7 1.7 0 0 0 1.7 1.7h13.6a1.7 1.7 0 0 0 1.7-1.7v-3.8l-1.9-7.3a1.7 1.7 0 0 0-1.6-1.2H7a1.7 1.7 0 0 0-1.6 1.2z"/>
    """,
    "globe": """
        <circle cx="12" cy="12" r="9"/><path d="M3.2 12h17.6"/>
        <path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z"/>
    """,
    "cpu": """
        <rect x="7" y="7" width="10" height="10" rx="2"/>
        <path d="M10 3.5v3M14 3.5v3M10 17.5v3M14 17.5v3M3.5 10h3M3.5 14h3M17.5 10h3M17.5 14h3"/>
    """,
    "layers": """
        <path d="m12 3.5 8.5 4.4L12 12.3 3.5 7.9z"/>
        <path d="m3.5 12.4 8.5 4.4 8.5-4.4"/><path d="m3.5 16.6 8.5 4.4 8.5-4.4"/>
    """,
}

_cache: dict[tuple, QIcon] = {}


def svg_markup(name: str, color: str, width: float = 1.7) -> str:
    body = _SVG.get(name, _SVG["info"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
        f'fill="none" stroke="{color}" stroke-width="{width}" '
        f'stroke-linecap="round" stroke-linejoin="round">{body}</svg>'
    )


def pixmap(name: str, size: int = 24, color: str = "#EAF2FF",
           width: float = 1.7, dpr: float = 2.0) -> QPixmap:
    r = QSvgRenderer(QByteArray(svg_markup(name, color, width).encode()))
    pm = QPixmap(int(size * dpr), int(size * dpr))
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    # рисуем в физических пикселях, DPR выставляем уже после — иначе
    # QPainter применит масштаб повторно и иконка обрежется
    r.render(p, QRectF(0, 0, size * dpr, size * dpr))
    p.end()
    pm.setDevicePixelRatio(dpr)
    return pm


def icon(name: str, size: int = 24, color: str = "#EAF2FF", width: float = 1.7) -> QIcon:
    key = (name, size, color, width)
    if key not in _cache:
        _cache[key] = QIcon(pixmap(name, size, color, width))
    return _cache[key]


def clear_cache():
    _cache.clear()
