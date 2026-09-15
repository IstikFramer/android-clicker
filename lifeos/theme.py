"""LIFE OS — тема оформления: палитры акцентов и генерация QSS.

Стиль: тёмный glassmorphism + неоновое свечение.
Акценты заготовлены все (cyan/electric/violet/green/amber), активные по умолчанию —
cyan и electric blue, остальные включатся в следующих версиях.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Accent:
    key: str
    title: str
    primary: str      # основной неон
    secondary: str    # второй цвет градиента
    glow: str         # цвет свечения (rgba-строка формируется отдельно)
    available: bool = True

    @property
    def rgb(self) -> tuple[int, int, int]:
        h = self.primary.lstrip("#")
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

    def rgba(self, alpha: float) -> str:
        r, g, b = self.rgb
        return f"rgba({r}, {g}, {b}, {alpha:.3f})"


ACCENTS: dict[str, Accent] = {
    "cyan": Accent("cyan", "Cyan / Циан", "#00E5FF", "#2D7FF9", "#00E5FF", True),
    "electric": Accent("electric", "Electric Blue", "#2D7FF9", "#6EA8FF", "#2D7FF9", True),
    "violet": Accent("violet", "Violet / Neon Pink", "#7C3AED", "#EC4899", "#A855F7", False),
    "emerald": Accent("emerald", "Emerald / Matrix", "#00FF9C", "#00B87C", "#00FF9C", False),
    "amber": Accent("amber", "Amber / Solar", "#FF8A00", "#FFC53D", "#FF8A00", False),
}

DEFAULT_ACCENT = "cyan"

# --- базовая тёмная палитра -------------------------------------------------
BASE = {
    "bg":            "#05070D",
    "bg_soft":       "#080B14",
    "surface":       "rgba(255, 255, 255, 0.045)",
    "surface_hi":    "rgba(255, 255, 255, 0.075)",
    "surface_press": "rgba(255, 255, 255, 0.11)",
    "stroke":        "rgba(255, 255, 255, 0.09)",
    "stroke_hi":     "rgba(255, 255, 255, 0.16)",
    "text":          "#EAF2FF",
    "text_dim":      "#9AA8BF",
    "text_mute":     "#6B7A94",
    "danger":        "#FF5C6C",
    "ok":            "#38E8A0",
    "warn":          "#FFC53D",
}

FONT_STACK = '"Inter", "Segoe UI Variable Display", "Segoe UI", "SF Pro Display", "Roboto", sans-serif'
MONO_STACK = '"JetBrains Mono", "Cascadia Mono", "Consolas", "SF Mono", monospace'


def build_qss(accent_key: str = DEFAULT_ACCENT) -> str:
    a = ACCENTS.get(accent_key, ACCENTS[DEFAULT_ACCENT])
    c = dict(BASE)
    c["accent"] = a.primary
    c["accent2"] = a.secondary
    c["accent_08"] = a.rgba(0.08)
    c["accent_14"] = a.rgba(0.14)
    c["accent_22"] = a.rgba(0.22)
    c["accent_35"] = a.rgba(0.35)
    c["accent_60"] = a.rgba(0.60)
    c["font"] = FONT_STACK
    c["mono"] = MONO_STACK

    return f"""
/* ============================ LIFE OS · QSS ============================ */
* {{
    font-family: {c['font']};
    color: {c['text']};
    outline: none;
}}

QWidget#RootFrame {{
    background: transparent;
}}

/* ------------------------------- Titlebar ------------------------------ */
QWidget#TitleBar {{
    background: transparent;
}}
QLabel#TitleText {{
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 3px;
    color: {c['text']};
}}
QLabel#TitleVersion {{
    font-family: {c['mono']};
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1px;
    color: {c['accent']};
    background: {c['accent_14']};
    border: 1px solid {c['accent_35']};
    border-radius: 7px;
    padding: 2px 8px;
}}
QLabel#TitleSub {{
    font-size: 11px;
    color: {c['text_mute']};
    letter-spacing: .4px;
}}

QPushButton#WinBtn {{
    background: transparent;
    border: none;
    border-radius: 9px;
    color: {c['text_dim']};
    font-size: 15px;
    font-family: {c['mono']};
}}
QPushButton#WinBtn:hover {{
    background: {c['surface_hi']};
    color: {c['text']};
}}
QPushButton#WinBtn:pressed {{ background: {c['surface_press']}; }}
QPushButton#WinBtnClose {{
    background: transparent;
    border: none;
    border-radius: 9px;
    color: {c['text_dim']};
    font-size: 15px;
    font-family: {c['mono']};
}}
QPushButton#WinBtnClose:hover {{
    background: rgba(255, 92, 108, 0.20);
    color: {c['danger']};
}}
QPushButton#WinBtnClose:pressed {{ background: rgba(255, 92, 108, 0.32); }}

/* -------------------------------- Sidebar ------------------------------ */
QWidget#Sidebar {{
    background: rgba(255, 255, 255, 0.028);
    border-right: 1px solid {c['stroke']};
}}
QLabel#SidebarSection {{
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    color: {c['text_mute']};
    padding: 0 14px;
}}

QPushButton#NavItem {{
    text-align: left;
    padding: 0 14px;
    border: 1px solid transparent;
    border-radius: 13px;
    background: transparent;
    font-size: 13.5px;
    font-weight: 600;
    color: {c['text_dim']};
}}
QPushButton#NavItem:hover {{
    background: {c['surface']};
    border: 1px solid {c['stroke']};
    color: {c['text']};
}}
QPushButton#NavItem:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c['accent_22']}, stop:1 rgba(255,255,255,0.02));
    border: 1px solid {c['accent_35']};
    color: {c['text']};
}}

QPushButton#SidebarToggle {{
    background: {c['surface']};
    border: 1px solid {c['stroke']};
    border-radius: 11px;
    color: {c['text_dim']};
    font-family: {c['mono']};
    font-size: 13px;
}}
QPushButton#SidebarToggle:hover {{
    background: {c['surface_hi']};
    color: {c['accent']};
    border: 1px solid {c['accent_35']};
}}

QFrame#SidebarDivider {{
    background: {c['stroke']};
    max-height: 1px;
    border: none;
}}

QLabel#UserName  {{ font-size: 12.5px; font-weight: 700; color: {c['text']}; }}
QLabel#UserRole  {{ font-size: 10.5px; color: {c['text_mute']}; letter-spacing: .6px; }}

/* --------------------------------- Cards ------------------------------- */
QFrame#GlassCard {{
    background: rgba(255, 255, 255, 0.042);
    border: 1px solid {c['stroke']};
    border-radius: 18px;
}}
QFrame#GlassCard[hoverable="true"]:hover {{
    background: rgba(255, 255, 255, 0.062);
    border: 1px solid {c['accent_35']};
}}
QFrame#HeroCard {{
    border: 1px solid {c['stroke_hi']};
    border-radius: 22px;
    background: transparent;
}}

QLabel#CardTitle  {{ font-size: 13px; font-weight: 700; letter-spacing: .3px; color: {c['text']}; }}
QLabel#CardKicker {{
    font-family: {c['mono']};
    font-size: 9.5px; font-weight: 700; letter-spacing: 2px;
    color: {c['accent']};
}}
QLabel#CardBody   {{ font-size: 12px; color: {c['text_dim']}; }}
QLabel#StatValue  {{ font-size: 30px; font-weight: 800; letter-spacing: -.5px; color: {c['text']}; }}
QLabel#StatUnit   {{ font-size: 12px; font-weight: 600; color: {c['text_mute']}; }}
QLabel#StatCaption{{ font-size: 11px; color: {c['text_mute']}; }}

QLabel#PageTitle  {{ font-size: 26px; font-weight: 800; letter-spacing: -.4px; }}
QLabel#PageSub    {{ font-size: 12.5px; color: {c['text_mute']}; }}
QLabel#HeroTitle  {{ font-size: 32px; font-weight: 800; letter-spacing: -.8px; }}
QLabel#HeroBody   {{ font-size: 13px; color: {c['text_dim']}; }}
QLabel#Mono       {{ font-family: {c['mono']}; font-size: 11px; color: {c['text_mute']}; }}

QLabel#Badge {{
    font-family: {c['mono']};
    font-size: 9.5px; font-weight: 700; letter-spacing: 1.4px;
    color: {c['accent']};
    background: {c['accent_14']};
    border: 1px solid {c['accent_35']};
    border-radius: 8px;
    padding: 3px 9px;
}}
QLabel#BadgeMuted {{
    font-family: {c['mono']};
    font-size: 9.5px; font-weight: 700; letter-spacing: 1.4px;
    color: {c['text_mute']};
    background: {c['surface']};
    border: 1px solid {c['stroke']};
    border-radius: 8px;
    padding: 3px 9px;
}}

/* -------------------------------- Buttons ------------------------------ */
QPushButton#Primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {c['accent']}, stop:1 {c['accent2']});
    border: none;
    border-radius: 13px;
    color: #04121A;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: .3px;
    padding: 0 22px;
}}
QPushButton#Primary:hover  {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                              stop:0 {c['accent2']}, stop:1 {c['accent']}); }}
QPushButton#Primary:pressed{{ padding-top: 1px; }}

QPushButton#Ghost {{
    background: {c['surface']};
    border: 1px solid {c['stroke_hi']};
    border-radius: 13px;
    color: {c['text']};
    font-size: 13px;
    font-weight: 600;
    padding: 0 20px;
}}
QPushButton#Ghost:hover   {{ background: {c['surface_hi']}; border: 1px solid {c['accent_35']}; color: {c['accent']}; }}
QPushButton#Ghost:pressed {{ background: {c['surface_press']}; }}

QPushButton#Chip {{
    background: {c['surface']};
    border: 1px solid {c['stroke']};
    border-radius: 11px;
    color: {c['text_dim']};
    font-size: 11.5px;
    font-weight: 600;
    padding: 0 14px;
}}
QPushButton#Chip:hover   {{ border: 1px solid {c['accent_35']}; color: {c['accent']}; }}
QPushButton#Chip:checked {{
    background: {c['accent_22']};
    border: 1px solid {c['accent_60']};
    color: {c['text']};
}}

/* -------------------------------- Inputs ------------------------------- */
QLineEdit#Search {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid {c['stroke']};
    border-radius: 13px;
    padding: 0 14px 0 38px;
    font-size: 12.5px;
    color: {c['text']};
    selection-background-color: {c['accent_60']};
}}
QLineEdit#Search:focus {{
    border: 1px solid {c['accent_60']};
    background: rgba(255, 255, 255, 0.075);
}}

QComboBox#Select {{
    background: {c['surface']};
    border: 1px solid {c['stroke']};
    border-radius: 11px;
    padding: 6px 12px;
    font-size: 12px;
    color: {c['text']};
    min-width: 160px;
}}
QComboBox#Select:hover {{ border: 1px solid {c['accent_35']}; }}
QComboBox#Select::drop-down {{ border: none; width: 24px; }}
QComboBox#Select QAbstractItemView {{
    background: #0B0F1A;
    border: 1px solid {c['stroke_hi']};
    border-radius: 10px;
    padding: 6px;
    selection-background-color: {c['accent_22']};
    outline: none;
}}

/* -------------------------------- Switch ------------------------------- */
QCheckBox#Switch {{ spacing: 0; }}
QCheckBox#Switch::indicator {{
    width: 44px; height: 24px;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.09);
    border: 1px solid {c['stroke_hi']};
}}
QCheckBox#Switch::indicator:checked {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c['accent']}, stop:1 {c['accent2']});
    border: 1px solid {c['accent_60']};
}}

/* ------------------------------ Scrollbars ----------------------------- */
QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; border: none; }}
QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 4px 2px 4px 0;
}}
QScrollBar::handle:vertical {{
    background: rgba(255, 255, 255, 0.13);
    border-radius: 4px; min-height: 40px;
}}
QScrollBar::handle:vertical:hover {{ background: {c['accent_60']}; }}
QScrollBar::add-line, QScrollBar::sub-line,
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; border: none; height: 0; width: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0 4px 2px 4px; }}
QScrollBar::handle:horizontal {{ background: rgba(255,255,255,0.13); border-radius: 4px; min-width: 40px; }}

/* ------------------------------- Progress ------------------------------ */
QProgressBar#Thin {{
    background: rgba(255, 255, 255, 0.07);
    border: none; border-radius: 4px; height: 8px; text-align: center; color: transparent;
}}
QProgressBar#Thin::chunk {{
    border-radius: 4px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c['accent']}, stop:1 {c['accent2']});
}}

/* --------------------------------- Menu -------------------------------- */
QMenu {{
    background: #0A0E18;
    border: 1px solid {c['stroke_hi']};
    border-radius: 12px;
    padding: 8px;
}}
QMenu::item {{
    padding: 8px 18px; border-radius: 8px; font-size: 12.5px; color: {c['text_dim']};
}}
QMenu::item:selected {{ background: {c['accent_22']}; color: {c['text']}; }}
QMenu::separator {{ height: 1px; background: {c['stroke']}; margin: 6px 8px; }}

QToolTip {{
    background: #0A0E18;
    color: {c['text']};
    border: 1px solid {c['accent_35']};
    border-radius: 8px;
    padding: 6px 10px;
    font-size: 11.5px;
}}
"""
