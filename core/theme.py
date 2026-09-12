"""Centralized Fluent and glass visual language for the Shell application."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont


class Colors:
    """Updated dark Fluent palette with glass surface colors."""

    BACKGROUND_WINDOW = "transparent"
    BACKGROUND_SURFACE = "rgba(30, 30, 50, 0.65)"
    BACKGROUND_CARD = "rgba(255, 255, 255, 0.05)"
    BACKGROUND_CARD_HOVER = "rgba(255, 255, 255, 0.08)"
    BORDER_SUBTLE = "rgba(255, 255, 255, 0.08)"
    BORDER_DEFAULT = "rgba(255, 255, 255, 0.12)"
    BORDER_FOCUS = "#00adb5"
    TEXT_PRIMARY = "#e8e8e8"
    TEXT_SECONDARY = "#9a9a9a"
    ACCENT = "#00adb5"
    ACCENT_LIGHT = "#00cfd8"
    ERROR = "#e74c3c"
    SUCCESS = "#2ecc71"
    WARNING = "#f39c12"
    WHITE = "#ffffff"
    SHADOW = "#000000"

    # Compatibility names retained for future plugins built against v0.1.
    BACKGROUND_PRIMARY = "#1a1a2e"
    BACKGROUND_SECONDARY = BACKGROUND_SURFACE
    BACKGROUND_TERTIARY = "rgba(255, 255, 255, 0.08)"
    ACCENT_HOVER = ACCENT_LIGHT
    BORDER = BORDER_DEFAULT
    INPUT_BACKGROUND = "rgba(255, 255, 255, 0.05)"


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


def _surface_color(panel_opacity: int) -> str:
    """Convert the panel setting to a stable translucent surface color."""
    value = max(50, min(100, int(panel_opacity)))
    alpha = 0.38 + ((value - 50) / 50) * 0.27
    return f"rgba(30, 30, 50, {alpha:.2f})"


def generate_stylesheet(panel_opacity: int = 80) -> str:
    """Build and return the complete Fluent glass QSS stylesheet.

    Args:
        panel_opacity: User-selected surface opacity in the range 50 to 100.

    Returns:
        A QSS string applied globally to the QApplication instance.
    """
    c = Colors
    s = Sizes
    surface = _surface_color(panel_opacity)
    return f"""
    * {{
        font-family: "{Fonts.FAMILY}";
        font-size: {Fonts.BODY_SIZE}pt;
        color: {c.TEXT_PRIMARY};
    }}
    QMainWindow, QDialog, QWidget {{
        background-color: {c.BACKGROUND_WINDOW};
        color: {c.TEXT_PRIMARY};
    }}
    QMainWindow[windowEffect="qss"], QMainWindow[windowEffect="none"],
    QDialog[windowEffect="qss"], QDialog[windowEffect="none"] {{
        background-color: {c.BACKGROUND_PRIMARY};
    }}
    QToolTip {{
        background-color: rgba(30, 30, 50, 0.94);
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER_DEFAULT};
        padding: 6px 9px;
        border-radius: {s.INPUT_RADIUS}px;
    }}
    QFrame[frameRole="card"], QFrame[frameRole="large-card"] {{
        background-color: {c.BACKGROUND_CARD};
        border: 1px solid {c.BORDER_DEFAULT};
        border-radius: {s.CARD_RADIUS}px;
    }}
    QFrame[frameRole="card"]:hover, QFrame[frameRole="large-card"]:hover {{
        background-color: {c.BACKGROUND_CARD_HOVER};
        border-color: rgba(255, 255, 255, 0.15);
    }}
    QFrame[frameRole="large-card"] {{
        border-radius: {s.LARGE_CARD_RADIUS}px;
    }}
    QFrame#windowFrame {{
        background-color: {surface};
        border: 1px solid {c.BORDER_SUBTLE};
        border-radius: {s.CARD_RADIUS}px;
    }}
    QFrame#windowFrame[windowEffect="none"], QFrame#windowFrame[windowEffect="qss"] {{
        background-color: {c.BACKGROUND_PRIMARY};
    }}
    QWidget#titleBar {{
        background-color: rgba(30, 30, 50, 0.50);
        border-top-left-radius: {s.CARD_RADIUS}px;
        border-top-right-radius: {s.CARD_RADIUS}px;
    }}
    QWidget#sidebar {{
        background-color: {surface};
        border-right: 1px solid {c.BORDER_SUBTLE};
        border-bottom-left-radius: {s.CARD_RADIUS}px;
    }}
    QFrame#userPanel {{
        background-color: {c.BACKGROUND_CARD};
        border: 1px solid {c.BORDER_SUBTLE};
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
        background-color: {c.BORDER_SUBTLE};
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
    QLabel[role="page-title"], QLabel[role="welcome-title"] {{
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
    QLabel[role="mono"], QLabel[role="about-value"] {{
        font-family: "{Fonts.MONO_FAMILY}";
        font-size: {Fonts.SMALL_SIZE}pt;
        color: {c.TEXT_PRIMARY};
    }}
    QLabel[role="setting-label"] {{
        color: {c.TEXT_PRIMARY};
    }}
    #updateAccentBar {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {c.ACCENT}, stop:0.7 rgba(0, 173, 181, 0.18), stop:1 transparent);
        border: none;
        border-radius: 1px;
    }}
    QPushButton, PushButton, PrimaryPushButton, TransparentPushButton, ToggleButton {{
        background-color: transparent;
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER_SUBTLE};
        border-radius: {s.BUTTON_RADIUS}px;
        padding: 8px 16px;
        min-height: 18px;
    }}
    QPushButton:hover, PushButton:hover, TransparentPushButton:hover, ToggleButton:hover {{
        background-color: {c.BACKGROUND_CARD_HOVER};
        border-color: {c.BORDER_DEFAULT};
    }}
    QPushButton:pressed, PushButton:pressed, TransparentPushButton:pressed, ToggleButton:pressed {{
        background-color: rgba(0, 173, 181, 0.16);
    }}
    QPushButton:disabled, PushButton:disabled, PrimaryPushButton:disabled {{
        color: {c.TEXT_SECONDARY};
        border-color: {c.BORDER_SUBTLE};
    }}
    QPushButton[variant="primary"], PrimaryPushButton {{
        background-color: {c.ACCENT};
        color: {c.WHITE};
        border-color: {c.ACCENT};
    }}
    QPushButton[variant="primary"]:hover, PrimaryPushButton:hover {{
        background-color: {c.ACCENT_LIGHT};
        border-color: {c.ACCENT_LIGHT};
    }}
    QPushButton[variant="primary"]:pressed, PrimaryPushButton:pressed {{
        background-color: #008e95;
        border-color: #008e95;
    }}
    QPushButton[variant="danger"] {{
        color: {c.ERROR};
        border-color: rgba(231, 76, 60, 0.5);
    }}
    QPushButton[variant="danger"]:hover {{
        background-color: rgba(231, 76, 60, 0.16);
        border-color: {c.ERROR};
    }}
    QPushButton[role="title-button"], QPushButton[role="close-button"] {{
        border: none;
        border-radius: 0px;
        padding: 0px;
        min-width: 46px;
        min-height: {s.TITLE_BAR_HEIGHT}px;
        max-height: {s.TITLE_BAR_HEIGHT}px;
        background-color: transparent;
    }}
    QPushButton[role="title-button"]:hover {{
        background-color: rgba(255, 255, 255, 0.08);
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
        background-color: {c.BACKGROUND_CARD_HOVER};
    }}
    QPushButton[role="sidebar-item"][active="true"] {{
        background-color: rgba(0, 173, 181, 0.12);
        border-left-color: {c.ACCENT};
        color: {c.ACCENT_LIGHT};
    }}
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {c.BACKGROUND_CARD};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER_SUBTLE};
        border-bottom: 2px solid {c.BORDER_DEFAULT};
        border-radius: {s.INPUT_RADIUS}px;
        padding: 6px 12px;
        selection-background-color: {c.ACCENT};
    }}
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border-color: {c.BORDER_FOCUS};
        border-bottom-color: {c.BORDER_FOCUS};
    }}
    QScrollArea, SmoothScrollArea {{
        background-color: transparent;
        border: none;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background: rgba(255, 255, 255, 0.18);
        border-radius: 3px;
        min-height: 28px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: rgba(0, 173, 181, 0.72);
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        height: 0px;
        background: transparent;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
    }}
    QScrollBar::handle:horizontal {{
        background: rgba(255, 255, 255, 0.18);
        border-radius: 3px;
        min-width: 28px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: rgba(0, 173, 181, 0.72);
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        width: 0px;
        background: transparent;
    }}
    QHeaderView::section {{
        background-color: {c.BACKGROUND_CARD};
        color: {c.TEXT_SECONDARY};
        border: none;
        border-bottom: 1px solid {c.BORDER_SUBTLE};
        padding: 8px;
    }}
    QTableWidget {{
        background-color: {c.BACKGROUND_CARD};
        alternate-background-color: rgba(255, 255, 255, 0.025);
        gridline-color: {c.BORDER_SUBTLE};
        border: 1px solid {c.BORDER_SUBTLE};
        border-radius: {s.CARD_RADIUS}px;
    }}
    QMenu {{
        background-color: rgba(30, 30, 50, 0.96);
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER_DEFAULT};
        padding: 5px;
    }}
    QMenu::item {{
        padding: 7px 22px 7px 12px;
        border-radius: {s.INPUT_RADIUS}px;
    }}
    QMenu::item:selected {{
        background-color: rgba(0, 173, 181, 0.16);
        color: {c.ACCENT_LIGHT};
    }}
    QMessageBox {{
        background-color: rgba(30, 30, 50, 0.96);
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER_DEFAULT};
    }}
    QMessageBox QLabel {{
        color: {c.TEXT_PRIMARY};
        min-width: 260px;
    }}
    QMessageBox QPushButton {{
        min-width: 82px;
    }}
    QCheckBox, CheckBox {{
        spacing: 9px;
        color: {c.TEXT_PRIMARY};
        padding: 4px 0px;
    }}
    QCheckBox::indicator, CheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 1px solid {c.BORDER_DEFAULT};
        border-radius: 4px;
        background-color: {c.BACKGROUND_CARD};
    }}
    QCheckBox::indicator:hover, CheckBox::indicator:hover {{
        border-color: {c.ACCENT};
    }}
    QCheckBox::indicator:checked, CheckBox::indicator:checked {{
        background-color: {c.ACCENT};
        border-color: {c.ACCENT};
    }}
    QComboBox, ComboBox {{
        background-color: {c.BACKGROUND_CARD};
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER_SUBTLE};
        border-bottom: 2px solid {c.BORDER_DEFAULT};
        border-radius: {s.INPUT_RADIUS}px;
        padding: 7px 12px;
        min-width: 130px;
    }}
    QComboBox:hover, QComboBox:focus, ComboBox:hover, ComboBox:focus {{
        border-color: {c.BORDER_FOCUS};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 26px;
    }}
    QComboBox QAbstractItemView {{
        background-color: rgba(30, 30, 50, 0.96);
        color: {c.TEXT_PRIMARY};
        border: 1px solid {c.BORDER_DEFAULT};
        selection-background-color: rgba(0, 173, 181, 0.16);
        selection-color: {c.ACCENT_LIGHT};
        padding: 4px;
    }}
    QSlider::groove:horizontal {{
        height: 4px;
        background: rgba(255, 255, 255, 0.16);
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {c.ACCENT};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        width: 16px;
        margin: -6px 0px;
        border-radius: 8px;
        background: {c.ACCENT_LIGHT};
    }}
    QProgressBar {{
        background-color: rgba(255, 255, 255, 0.08);
        border: 1px solid {c.BORDER_SUBTLE};
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
        border: 1px solid {c.BORDER_SUBTLE};
        background-color: {c.BACKGROUND_CARD};
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
        color: {c.ACCENT_LIGHT};
        border-bottom-color: {c.ACCENT};
    }}
    QStatusBar {{
        background-color: rgba(30, 30, 50, 0.65);
        color: {c.TEXT_SECONDARY};
        border-top: 1px solid {c.BORDER_SUBTLE};
    }}
    QStatusBar::item {{
        border: none;
    }}
    QSplitter::handle {{
        background-color: {c.BORDER_SUBTLE};
    }}
    """


def shadow_color() -> QColor:
    """Return the color used by card drop shadows."""
    color = QColor(Colors.SHADOW)
    color.setAlpha(76)
    return color
