"""LIFE OS — тема оформления: палитры акцентов и генерация QSS.

Стиль: тёмный glassmorphism + мягкое свечение.
Параметры (прозрачность стекла, радиус углов, масштаб) берутся из настроек,
поэтому слайдеры в разделе «Настройки» меняют вид приложения мгновенно.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import config as cfg
from .settings import settings


@dataclass(frozen=True)
class Accent:
    key: str
    title: str
    primary: str
    secondary: str
    available: bool = True

    @property
    def rgb(self) -> tuple[int, int, int]:
        h = self.primary.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def rgba(self, alpha: float) -> str:
        r, g, b = self.rgb
        return f"rgba({r}, {g}, {b}, {max(0.0, min(1.0, alpha)):.3f})"


ACCENTS: dict[str, Accent] = {
    "cyan":     Accent("cyan", "Cyan", "#00E5FF", "#2D7FF9", True),
    "electric": Accent("electric", "Electric", "#2D7FF9", "#7AA8FF", True),
    "violet":   Accent("violet", "Violet", "#8B5CF6", "#EC4899", True),
    "emerald":  Accent("emerald", "Emerald", "#00E39A", "#0FB981", True),
    "amber":    Accent("amber", "Amber", "#FFA51F", "#FFD166", True),
}

DEFAULT_ACCENT = "cyan"

BASE = {
    "bg": "#04060C",
    "text": "#EDF3FF",
    "text_dim": "#9DABC2",
    "text_mute": "#6B7A94",
    "danger": "#FF5C6C",
    "ok": "#38E8A0",
}

FONT_STACK = '"Inter", "Segoe UI Variable Text", "Segoe UI", "SF Pro Text", "Roboto", sans-serif'
MONO_STACK = '"JetBrains Mono", "Cascadia Mono", "Consolas", "SF Mono", monospace'


def current_accent() -> Accent:
    return ACCENTS.get(settings.get("accent"), ACCENTS[DEFAULT_ACCENT])


def scaled(px: float) -> float:
    return px * settings.get("ui_scale") / 100.0


def _check_png() -> str:
    """Готовит белую галочку для чекбоксов и возвращает путь к ней."""
    out = cfg.ICONS / "checkmark.png"
    if not out.exists():
        from PySide6.QtCore import QRectF, Qt
        from PySide6.QtGui import QColor, QImage, QPainter, QPen
        img = QImage(36, 36, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor("#0B0E14"), 4.6)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        p.setPen(pen)
        p.drawPolyline([QRectF(9, 18, 0, 0).topLeft(),
                        QRectF(15.5, 24.5, 0, 0).topLeft(),
                        QRectF(27, 11.5, 0, 0).topLeft()])
        p.end()
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(str(out))
    return out.as_posix()


def build_qss(accent_key: str | None = None) -> str:
    a = ACCENTS.get(accent_key or settings.get("accent"), ACCENTS[DEFAULT_ACCENT])
    g = settings.glass_alpha
    rad = settings.get("corner_radius")
    s = settings.get("ui_scale") / 100.0
    c = dict(BASE)

    c.update({
        "accent": a.primary,
        "accent2": a.secondary,
        "a08": a.rgba(0.08), "a14": a.rgba(0.14), "a22": a.rgba(0.22),
        "a38": a.rgba(0.38), "a60": a.rgba(0.60),
        "surface": f"rgba(255,255,255,{g:.3f})",
        "surface_hi": f"rgba(255,255,255,{g + 0.035:.3f})",
        "surface_press": f"rgba(255,255,255,{g + 0.06:.3f})",
        "check_png": _check_png(),
        "stroke": f"rgba(255,255,255,{0.06 + g * 0.35:.3f})",
        "stroke_hi": f"rgba(255,255,255,{0.12 + g * 0.4:.3f})",
        "font": FONT_STACK, "mono": MONO_STACK,
        "r_card": f"{rad}px", "r_ctl": f"{max(8, int(rad * 0.66))}px",
        "r_pill": f"{max(6, int(rad * 0.5))}px",
        "fs_xs": f"{10 * s:.1f}px", "fs_sm": f"{11.5 * s:.1f}px",
        "fs_md": f"{12.5 * s:.1f}px", "fs_lg": f"{14 * s:.1f}px",
        "fs_title": f"{27 * s:.1f}px", "fs_hero": f"{34 * s:.1f}px",
        "fs_card": f"{13.5 * s:.1f}px",
    })

    return f"""
/* ========================= LIFE OS · QSS ========================= */
* {{ font-family: {c['font']}; color: {c['text']}; outline: none; }}

QWidget#Transparent, QWidget#RootFrame {{ background: transparent; }}

/* --------------------------------- Titlebar --------------------- */
QWidget#TitleBar {{ background: transparent; }}
QLabel#TitleText {{
    font-size: {13.5 * s:.1f}px; font-weight: 800; letter-spacing: 3.4px;
}}
QLabel#TitleVersion {{
    font-family: {c['mono']}; font-size: {c['fs_xs']}; font-weight: 700;
    letter-spacing: .8px; color: {c['accent']};
    background: {c['a14']}; border: 1px solid {c['a38']};
    border-radius: {c['r_pill']}; padding: 2px 8px;
}}
QLabel#TitleSub {{ font-size: {c['fs_sm']}; color: {c['text_mute']}; }}

QPushButton#WinBtn, QPushButton#WinBtnClose {{
    background: transparent; border: none; border-radius: {c['r_pill']};
}}
QPushButton#WinBtn:hover {{ background: {c['surface_hi']}; }}
QPushButton#WinBtn:pressed {{ background: {c['surface_press']}; }}
QPushButton#WinBtnClose:hover {{ background: rgba(255,92,108,0.22); }}
QPushButton#WinBtnClose:pressed {{ background: rgba(255,92,108,0.34); }}

/* ---------------------------------- Sidebar --------------------- */
QWidget#Sidebar {{
    background: rgba(255,255,255,{max(0.012, g * 0.5):.3f});
    border-right: 1px solid {c['stroke']};
}}
QLabel#SidebarSection {{
    font-size: {c['fs_xs']}; font-weight: 800; letter-spacing: 2.2px;
    color: {c['text_mute']}; padding: 0 14px;
}}
QPushButton#NavItem {{
    text-align: left; padding: 0 14px; background: transparent;
    border: 1px solid transparent; border-radius: {c['r_ctl']};
    font-size: {c['fs_card']}; font-weight: 600; color: {c['text_dim']};
}}
QPushButton#NavItem:hover {{ color: {c['text']}; }}
QPushButton#NavItem:checked {{ color: {c['text']}; }}

QPushButton#SidebarToggle {{
    background: {c['surface']}; border: 1px solid {c['stroke']};
    border-radius: {c['r_ctl']}; color: {c['text_dim']};
}}
QPushButton#SidebarToggle:hover {{
    background: {c['surface_hi']}; border: 1px solid {c['a38']}; color: {c['accent']};
}}
QFrame#Divider {{ background: {c['stroke']}; max-height: 1px; border: none; }}
QLabel#UserName {{ font-size: {c['fs_md']}; font-weight: 700; }}
QLabel#UserRole {{ font-size: {c['fs_xs']}; color: {c['text_mute']}; letter-spacing: .7px; }}

/* ----------------------------------- Cards ---------------------- */
QFrame#GlassCard {{
    background: {c['surface']}; border: 1px solid {c['stroke']};
    border-radius: {c['r_card']};
}}
QFrame#HeroCard {{ border: none; border-radius: {c['r_card']}; background: transparent; }}

QLabel#CardTitle  {{ font-size: {c['fs_card']}; font-weight: 700; }}
QLabel#CardKicker {{
    font-family: {c['mono']}; font-size: {9.5 * s:.1f}px; font-weight: 700;
    letter-spacing: 2px; color: {c['accent']};
}}
QLabel#CardBody   {{ font-size: {c['fs_md']}; color: {c['text_dim']}; }}
QLabel#SectionLabel {{
    font-family: {c['mono']}; font-size: {9.5 * s:.1f}px; font-weight: 700;
    letter-spacing: 2px; color: {c['text_mute']};
}}
QCheckBox {{ spacing: 0px; }}
QCheckBox::indicator {{
    width: 19px; height: 19px; border-radius: 6px;
    border: 1.6px solid {c['stroke_hi']};
    background: {c['surface']};
}}
QCheckBox::indicator:hover {{ border-color: {c['accent']}; }}
QCheckBox::indicator:checked {{
    background: {c['accent']}; border-color: {c['accent']};
    image: url("{c['check_png']}");
}}
QLabel#Caption    {{ font-size: {c['fs_sm']}; color: {c['text_mute']}; }}
QLabel#PageTitle  {{ font-size: {c['fs_title']}; font-weight: 800; letter-spacing: -.5px; }}
QLabel#PageSub    {{ font-size: {c['fs_md']}; color: {c['text_mute']}; }}
QLabel#HeroTitle  {{ font-size: {c['fs_hero']}; font-weight: 800; letter-spacing: -1px; }}
QLabel#HeroBody   {{ font-size: {c['fs_lg']}; color: {c['text_dim']}; }}
QLabel#Mono       {{ font-family: {c['mono']}; font-size: {c['fs_sm']}; color: {c['text_mute']}; }}
QLabel#MonoAccent {{
    font-family: {c['mono']}; font-size: {c['fs_sm']}; font-weight: 700; color: {c['accent']};
}}
QLabel#Legal      {{ font-size: {c['fs_md']}; color: {c['text_dim']}; line-height: 165%; }}
QLabel#LegalTitle {{ font-size: {c['fs_card']}; font-weight: 700; color: {c['text']}; }}

QLabel#Badge {{
    font-family: {c['mono']}; font-size: {9.5 * s:.1f}px; font-weight: 700;
    letter-spacing: 1.4px; color: {c['accent']}; background: {c['a14']};
    border: 1px solid {c['a38']}; border-radius: {c['r_pill']}; padding: 3px 9px;
}}
QLabel#BadgeMuted {{
    font-family: {c['mono']}; font-size: {9.5 * s:.1f}px; font-weight: 700;
    letter-spacing: 1.4px; color: {c['text_mute']}; background: {c['surface']};
    border: 1px solid {c['stroke']}; border-radius: {c['r_pill']}; padding: 3px 9px;
}}

/* ---------------------------------- Buttons --------------------- */
QPushButton#Primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {c['accent']}, stop:1 {c['accent2']});
    border: none; border-radius: {c['r_ctl']}; color: #04121A;
    font-size: {c['fs_md']}; font-weight: 800; padding: 0 22px;
}}
QPushButton#Primary:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {c['accent2']}, stop:1 {c['accent']});
}}
QPushButton#Primary:disabled {{
    background: rgba(255,255,255,0.07); color: {c['text_mute']};
}}
QPushButton#Ghost {{
    background: {c['surface']}; border: 1px solid {c['stroke_hi']};
    border-radius: {c['r_ctl']}; color: {c['text']};
    font-size: {c['fs_md']}; font-weight: 600; padding: 0 20px;
}}
QPushButton#Ghost:hover {{
    background: {c['surface_hi']}; border: 1px solid {c['a38']}; color: {c['accent']};
}}
QPushButton#Ghost:pressed {{ background: {c['surface_press']}; }}
QPushButton#Link {{
    background: transparent; border: none; color: {c['accent']};
    font-size: {c['fs_md']}; font-weight: 600; text-align: left; padding: 0;
}}
QPushButton#Link:hover {{ color: {c['text']}; }}

QPushButton#Segment {{
    background: transparent; border: none; border-radius: {c['r_pill']};
    color: {c['text_dim']}; font-size: {c['fs_sm']}; font-weight: 700; padding: 0 16px;
}}
QPushButton#Segment:hover {{ color: {c['text']}; }}
QPushButton#Segment:checked {{ color: #04121A; }}

/* ----------------------------------- Inputs --------------------- */
QComboBox#Select {{
    background: {c['surface']}; border: 1px solid {c['stroke']};
    border-radius: {c['r_ctl']}; padding: 7px 14px;
    font-size: {c['fs_md']}; min-width: 150px;
}}
QComboBox#Select:hover {{ border: 1px solid {c['a38']}; }}
QComboBox#Select::drop-down {{ border: none; width: 26px; }}
QComboBox#Select QAbstractItemView {{
    background: #0A0E18; border: 1px solid {c['stroke_hi']};
    border-radius: {c['r_ctl']}; padding: 6px; outline: none;
    selection-background-color: {c['a22']};
}}

/* ---------------------------------- Scrollbar ------------------- */
QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 11px; margin: 6px 3px 6px 0; }}
QScrollBar::handle:vertical {{
    background: rgba(255,255,255,0.14); border-radius: 4px; min-height: 44px;
}}
QScrollBar::handle:vertical:hover {{ background: {c['a60']}; }}
QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {{
    background: none; border: none; height: 0; width: 0;
}}
QScrollBar:horizontal {{ background: transparent; height: 11px; margin: 0 6px 3px 6px; }}
QScrollBar::handle:horizontal {{
    background: rgba(255,255,255,0.14); border-radius: 4px; min-width: 44px;
}}

/* ------------------------------------ Menu ---------------------- */
QMenu {{
    background: #080C15; border: 1px solid {c['stroke_hi']};
    border-radius: {c['r_ctl']}; padding: 8px;
}}
QMenu::item {{
    padding: 9px 20px; border-radius: {c['r_pill']};
    font-size: {c['fs_md']}; color: {c['text_dim']};
}}
QMenu::item:selected {{ background: {c['a22']}; color: {c['text']}; }}
QMenu::separator {{ height: 1px; background: {c['stroke']}; margin: 6px 8px; }}

QToolTip {{
    background: #080C15; color: {c['text']}; border: 1px solid {c['a38']};
    border-radius: {c['r_pill']}; padding: 6px 10px; font-size: {c['fs_sm']};
}}
"""
