"""Centralized visual language for the Shell application."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont


class Colors:
    """Application color palette."""

    BACKGROUND_PRIMARY = "#1a1a2e"
    BACKGROUND_SECONDARY = "#16213e"
    BACKGROUND_TERTIARY = "#0f3460"
    TEXT_PRIMARY = "#e0e0e0"
    TEXT_SECONDARY = "#8a8a8a"
    ACCENT = "#00adb5"
    ACCENT_HOVER = "#00cfd8"
    ERROR = "#e74c3c"
    SUCCESS = "#2ecc71"
    WARNING = "#f39c12"
    BORDER = "#2a2a4a"
    WHITE = "#ffffff"
    INPUT_BACKGROUND = "#111a32"
    SHADOW = "#000000"


class Fonts:
    """Font families and point sizes used by the interface."""

    FAMILY = "Segoe UI"
    HEADING_FAMILY = "Segoe UI Semibold"
    MONO_FAMILY = "Cascadia Code"
    MONO_FALLBACK = "Consolas"
    BODY_SIZE = 10
    SMALL_SIZE = 9
    LABEL_SIZE = 11
    TITLE_SIZE = 22
    SECTION_SIZE = 14


class Sizes:
    """Shared geometry values."""

    TITLE_BAR_HEIGHT = 40
    STATUS_BAR_HEIGHT = 28
    SIDEBAR_EXPANDED = 220
    SIDEBAR_COLLAPSED = 60
    SIDEBAR_ITEM_HEIGHT = 44
    CARD_RADIUS = 8
    LARGE_CARD_RADIUS = 12
    BUTTON_RADIUS = 6
    INPUT_RADIUS = 4
    CONTENT_MARGIN = 28
    CONTENT_SPACING = 18
    STANDARD_MARGIN = 16


def application_font() -> QFont:
    """Return the default application font."""
    font = QFont(Fonts.FAMILY, Fonts.BODY_SIZE)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    return font


def mono_font() -> QFont:
    """Return the monospace font used for technical values."""
    font = QFont(f"{Fonts.MONO_FAMILY}, {Fonts.MONO_FALLBACK}", Fonts.SMALL_SIZE)
    font.setStyleHint(QFont.StyleHint.TypeWriter)
    return font


def generate_stylesheet() -> str:
    """Build and return the complete application stylesheet.

    Returns:
        A QSS string that is applied once to the QApplication instance.
    """
    c = Colors
    s = Sizes
    return f"""
    * {{
        font-family: "{Fonts.FAMILY}";
        font-size: {Fonts.BODY_SIZE}pt;
        color: {c.TEXT_PRIMARY};
    }}
    QMainWindow, QDialog, QWidget {{
        background-color: {c.BACKGROUND_PRIMARY};
        color: {c.TEXT_PRIMARY};
    }}
    QToolTip {{
        background-color: {c.BACKGROUND_SECONDARY};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        padding: 6px 9px;
        border-radius: {s.INPUT_RADIUS}px;
    }}
    QFrame[frameRole="card"] {{
        background-color: {c.BACKGROUND_SECONDARY};
        border: 1px solid {c.BORDER};
        border-radius: {s.CARD_RADIUS}px;
    }}
    QFrame[frameRole="large-card"] {{
        background-color: {c.BACKGROUND_SECONDARY};
        border: 1px solid {c.BORDER};
        border-radius: {s.LARGE_CARD_RADIUS}px;
    }}
    QFrame#windowFrame {{
        background-color: {c.BACKGROUND_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: {s.CARD_RADIUS}px;
    }}
    QWidget#titleBar {{
        background-color: {c.BACKGROUND_PRIMARY};
        border-top-left-radius: {s.CARD_RADIUS}px;
        border-top-right-radius: {s.CARD_RADIUS}px;
    }}
    QWidget#sidebar {{
        background-color: {c.BACKGROUND_SECONDARY};
        border-bottom-left-radius: {s.CARD_RADIUS}px;
    }}
    QFrame#userPanel {{
        background-color: {c.BACKGROUND_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: {s.CARD_RADIUS}px;
    }}
    QLabel#avatarLabel {{
        background-color: {c.ACCENT};
        color: {c.WHITE};
        border-radius: 20px;
        font-size: 14pt;
        font-weight: 600;
    }}
    QLabel#userNameLabel {{
        color: {c.TEXT_PRIMARY};
        font-weight: 600;
    }}
    QFrame#sidebarDivider {{
        background-color: {c.BORDER};
        border: none;
    }}
    QLabel#sidebarVersion {{
        color: {c.TEXT_SECONDARY};
        font-size: {Fonts.SMALL_SIZE}pt;
    }}
    QLabel#windowTitle {{
        color: {c.TEXT_PRIMARY};
        font-family: "{Fonts.HEADING_FAMILY}";
        font-size: 11pt;
        font-weight: 600;
    }}
    QLabel {{
        background-color: transparent;
    }}
    QLabel[role="page-title"] {{
        font-family: "{Fonts.HEADING_FAMILY}";
        font-size: {Fonts.TITLE_SIZE}pt;
        font-weight: 600;
        color: {c.TEXT_PRIMARY};
    }}
    QLabel[role="section-title"] {{
        font-family: "{Fonts.HEADING_FAMILY}";
        font-size: {Fonts.SECTION_SIZE}pt;
        font-weight: 600;
        color: {c.TEXT_PRIMARY};
    }}
    QLabel[role="card-title"] {{
        font-family: "{Fonts.HEADING_FAMILY}";
        font-size: 12pt;
        font-weight: 600;
        color: {c.TEXT_PRIMARY};
    }}
    QLabel[role="welcome-title"] {{
        font-family: "{Fonts.HEADING_FAMILY}";
        font-size: {Fonts.TITLE_SIZE}pt;
        font-weight: 600;
        color: {c.TEXT_PRIMARY};
    }}
    QLabel[role="update-text"] {{
        color: {c.TEXT_PRIMARY};
        line-height: 160%;
    }}
    QLabel[role="stat-value"] {{
        color: {c.TEXT_PRIMARY};
        font-family: "{Fonts.HEADING_FAMILY}";
        font-size: 11pt;
        font-weight: 600;
    }}
    QLabel[role="muted"] {{
        color: {c.TEXT_SECONDARY};
    }}
    QLabel[role="mono"] {{
        font-family: "{Fonts.MONO_FAMILY}";
        font-size: {Fonts.SMALL_SIZE}pt;
        color: {c.TEXT_PRIMARY};
    }}
    QPushButton {{
        background-color: transparent;
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: {s.BUTTON_RADIUS}px;
        padding: 8px 16px;
        min-height: 18px;
    }}
    QPushButton:hover {{
        background-color: {c.BACKGROUND_TERTIARY};
        border-color: {c.ACCENT};
    }}
    QPushButton:pressed {{
        background-color: {c.BACKGROUND_PRIMARY};
    }}
    QPushButton:disabled {{
        color: {c.TEXT_SECONDARY};
        border-color: {c.BORDER};
    }}
    QPushButton[variant="primary"] {{
        background-color: {c.ACCENT};
        color: {c.WHITE};
        border-color: {c.ACCENT};
    }}
    QPushButton[variant="primary"]:hover {{
        background-color: {c.ACCENT_HOVER};
        border-color: {c.ACCENT_HOVER};
    }}
    QPushButton[variant="primary"]:pressed {{
        background-color: {c.BACKGROUND_TERTIARY};
        border-color: {c.BACKGROUND_TERTIARY};
    }}
    QPushButton[variant="danger"] {{
        color: {c.ERROR};
        border-color: {c.ERROR};
    }}
    QPushButton[variant="danger"]:hover {{
        background-color: {c.ERROR};
        color: {c.WHITE};
    }}
    QPushButton[role="title-button"] {{
        border: none;
        border-radius: 0px;
        padding: 0px;
        min-width: 46px;
        min-height: {s.TITLE_BAR_HEIGHT}px;
        max-height: {s.TITLE_BAR_HEIGHT}px;
        background-color: transparent;
    }}
    QPushButton[role="title-button"]:hover {{
        background-color: {c.BACKGROUND_TERTIARY};
    }}
    QPushButton[role="close-button"] {{
        border: none;
        border-radius: 0px;
        padding: 0px;
        min-width: 46px;
        min-height: {s.TITLE_BAR_HEIGHT}px;
        max-height: {s.TITLE_BAR_HEIGHT}px;
        background-color: transparent;
    }}
    QPushButton[role="close-button"]:hover {{
        background-color: {c.ERROR};
    }}
    QPushButton[role="sidebar-toggle"] {{
        border: none;
        padding: 0px;
        min-height: {s.SIDEBAR_ITEM_HEIGHT}px;
        max-height: {s.SIDEBAR_ITEM_HEIGHT}px;
    }}
    QPushButton[role="sidebar-item"] {{
        border: none;
        border-left: 3px solid transparent;
        border-radius: {s.BUTTON_RADIUS}px;
        padding: 0px 12px;
        text-align: left;
        min-height: {s.SIDEBAR_ITEM_HEIGHT}px;
        max-height: {s.SIDEBAR_ITEM_HEIGHT}px;
    }}
    QPushButton[role="sidebar-item"]:hover {{
        background-color: {c.BACKGROUND_TERTIARY};
    }}
    QPushButton[role="sidebar-item"][active="true"] {{
        background-color: {c.BACKGROUND_TERTIARY};
        border-left-color: {c.ACCENT};
        color: {c.ACCENT};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {c.INPUT_BACKGROUND};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: {s.INPUT_RADIUS}px;
        padding: 6px 12px;
        selection-background-color: {c.ACCENT};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {c.ACCENT};
    }}
    QScrollArea {{
        background-color: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 8px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: {c.BORDER};
        border-radius: 4px;
        min-height: 32px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {c.ACCENT};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        height: 0px;
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 8px;
    }}
    QScrollBar::handle:horizontal {{
        background: {c.BORDER};
        border-radius: 4px;
        min-width: 32px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {c.ACCENT};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        width: 0px;
        background: transparent;
    }}
    QHeaderView::section {{
        background-color: {c.BACKGROUND_SECONDARY};
        color: {c.TEXT_SECONDARY};
        border: none;
        border-bottom: 1px solid {c.BORDER};
        padding: 8px;
    }}
    QTableWidget {{
        background-color: {c.BACKGROUND_SECONDARY};
        alternate-background-color: {c.BACKGROUND_PRIMARY};
        gridline-color: {c.BORDER};
        border: 1px solid {c.BORDER};
        border-radius: {s.CARD_RADIUS}px;
    }}
    QMenu {{
        background-color: {c.BACKGROUND_SECONDARY};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        padding: 5px;
    }}
    QMenu::item {{
        padding: 7px 22px 7px 12px;
        border-radius: {s.INPUT_RADIUS}px;
    }}
    QMenu::item:selected {{
        background-color: {c.BACKGROUND_TERTIARY};
        color: {c.ACCENT};
    }}
    QCheckBox {{
        spacing: 9px;
        color: {c.TEXT_PRIMARY};
        padding: 4px 0px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {c.BORDER};
        border-radius: 4px;
        background-color: transparent;
    }}
    QCheckBox::indicator:hover {{
        border-color: {c.ACCENT};
    }}
    QCheckBox::indicator:checked {{
        background-color: {c.ACCENT};
        border-color: {c.ACCENT};
    }}
    QComboBox {{
        background-color: {c.INPUT_BACKGROUND};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: {s.INPUT_RADIUS}px;
        padding: 7px 12px;
        min-width: 130px;
    }}
    QComboBox:hover, QComboBox:focus {{
        border-color: {c.ACCENT};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 26px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {c.BACKGROUND_SECONDARY};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER};
        selection-background-color: {c.BACKGROUND_TERTIARY};
        selection-color: {c.ACCENT};
        padding: 4px;
    }}
    QProgressBar {{
        background-color: {c.BACKGROUND_PRIMARY};
        border: 1px solid {c.BORDER};
        border-radius: 4px;
        text-align: center;
        color: {c.TEXT_PRIMARY};
        min-height: 8px;
    }}
    QProgressBar::chunk {{
        background-color: {c.ACCENT};
        border-radius: 3px;
    }}
    QTabWidget::pane {{
        border: 1px solid {c.BORDER};
        background-color: {c.BACKGROUND_SECONDARY};
    }}
    QTabBar::tab {{
        background-color: transparent;
        color: {c.TEXT_SECONDARY};
        border-bottom: 2px solid transparent;
        padding: 9px 15px;
    }}
    QTabBar::tab:hover {{
        color: {c.TEXT_PRIMARY};
    }}
    QTabBar::tab:selected {{
        color: {c.ACCENT};
        border-bottom-color: {c.ACCENT};
    }}
    QStatusBar {{
        background-color: {c.BACKGROUND_SECONDARY};
        color: {c.TEXT_SECONDARY};
        border-top: 1px solid {c.BORDER};
    }}
    QStatusBar::item {{
        border: none;
    }}
    QSplitter::handle {{
        background-color: {c.BORDER};
    }}
    """


def shadow_color() -> QColor:
    """Return the color used by card drop shadows."""
    color = QColor(Colors.SHADOW)
    color.setAlpha(80)
    return color
