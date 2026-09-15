"""LIFE OS — безрамочное главное окно: титлбар, сайдбар, страницы, трей."""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve, QEvent, QPoint, QPropertyAnimation, QRect, QSize, Qt, QTimer,
)
from PySide6.QtGui import QAction, QColor, QCursor, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QSizeGrip,
    QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from . import config as cfg
from .pages import AboutPage, DashboardPage, SettingsPage, ToolsPage
from .theme import ACCENTS, DEFAULT_ACCENT, build_qss
from .widgets import Divider, LogoBadge, NavButton, BackgroundCanvas, make_label


# ---------------------------------------------------------------- Titlebar
class TitleBar(QWidget):
    def __init__(self, parent: "MainWindow"):
        super().__init__(parent)
        self.setObjectName("TitleBar")
        self.setFixedHeight(cfg.TITLEBAR_H)
        self._win = parent
        self._drag: QPoint | None = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 6, 10, 6)
        lay.setSpacing(10)

        self.badge = LogoBadge(size=32, accent=ACCENTS[DEFAULT_ACCENT].primary,
                               pixmap_name="logo_mini_256.png")
        lay.addWidget(self.badge)

        title = make_label("LIFE OS", "TitleText")
        lay.addWidget(title)
        self.version = make_label("v" + cfg.APP_VERSION, "TitleVersion")
        lay.addWidget(self.version, 0, Qt.AlignVCenter)
        lay.addSpacing(6)
        lay.addWidget(make_label("·  " + cfg.APP_TAGLINE, "TitleSub"))
        lay.addStretch(1)

        self.btn_min = self._win_btn("‒", "Свернуть")
        self.btn_max = self._win_btn("□", "Развернуть")
        self.btn_close = self._win_btn("✕", "Закрыть", close=True)
        self.btn_min.clicked.connect(parent.showMinimized)
        self.btn_max.clicked.connect(parent.toggle_max)
        self.btn_close.clicked.connect(parent.hide_to_tray)
        for b in (self.btn_min, self.btn_max, self.btn_close):
            lay.addWidget(b)

    def _win_btn(self, glyph: str, tip: str, close: bool = False) -> QPushButton:
        b = QPushButton(glyph)
        b.setObjectName("WinBtnClose" if close else "WinBtn")
        if close:
            b.setProperty("class", "close")
        b.setFixedSize(38, 32)
        b.setCursor(Qt.PointingHandCursor)
        b.setToolTip(tip)
        b.setStyleSheet("" if not close else "")
        return b

    # перетаскивание окна
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._drag = e.globalPosition().toPoint() - self._win.frameGeometry().topLeft()
            e.accept()

    def mouseMoveEvent(self, e):
        if self._drag and e.buttons() & Qt.LeftButton:
            if self._win.isMaximized():
                self._win.toggle_max()
                self._drag = QPoint(int(self._win.width() * 0.5), 26)
            self._win.move(e.globalPosition().toPoint() - self._drag)
            e.accept()

    def mouseReleaseEvent(self, e):
        self._drag = None

    def mouseDoubleClickEvent(self, e):
        self._win.toggle_max()


# ------------------------------------------------------------------ Sidebar
class Sidebar(QWidget):
    def __init__(self, parent: "MainWindow"):
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(cfg.SIDEBAR_W)
        self._win = parent
        self._collapsed = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 16, 14, 16)
        lay.setSpacing(10)

        self.section_nav = make_label("НАВИГАЦИЯ", "SidebarSection")
        lay.addWidget(self.section_nav)

        acc = ACCENTS[DEFAULT_ACCENT].primary
        self.buttons: list[NavButton] = []
        items = [
            ("Панель управления", cfg.ICONS / "dashboard_glyph_128.png"),
            ("Инструменты", cfg.ICONS / "tools_glyph_128.png"),
            ("Настройки", cfg.ICONS / "settings_glyph_128.png"),
            ("О программе", cfg.ICONS / "about_glyph_128.png"),
        ]
        for i, (text, icon) in enumerate(items):
            b = NavButton(text, icon, accent=acc)
            b.clicked.connect(lambda _=False, idx=i: self._win.go(idx))
            lay.addWidget(b)
            self.buttons.append(b)
        self.buttons[0].setChecked(True)

        lay.addStretch(1)
        lay.addWidget(Divider())

        # мини-профиль
        self.profile = QWidget()
        pl = QHBoxLayout(self.profile)
        pl.setContentsMargins(4, 6, 4, 6)
        pl.setSpacing(10)
        self.avatar = LogoBadge(size=36, accent=acc, pixmap_name="logo_tray_256.png", spin=False)
        pl.addWidget(self.avatar)
        col = QVBoxLayout()
        col.setSpacing(1)
        self.user_name = make_label("Локальный профиль", "UserName")
        self.user_role = make_label("OFFLINE MODE", "UserRole")
        col.addWidget(self.user_name)
        col.addWidget(self.user_role)
        pl.addLayout(col)
        pl.addStretch(1)
        lay.addWidget(self.profile)

        self.toggle = QPushButton("⟨  Свернуть панель")
        self.toggle.setObjectName("SidebarToggle")
        self.toggle.setFixedHeight(36)
        self.toggle.setCursor(Qt.PointingHandCursor)
        self.toggle.clicked.connect(self.toggle_collapse)
        lay.addWidget(self.toggle)

        self._anim = QPropertyAnimation(self, b"minimumWidth", self)
        self._anim2 = QPropertyAnimation(self, b"maximumWidth", self)

    def set_active(self, index: int):
        for i, b in enumerate(self.buttons):
            b.setChecked(i == index)

    def set_accent(self, key: str):
        acc = ACCENTS[key].primary
        for b in self.buttons:
            b.set_accent(acc)
        self.avatar.set_accent(acc)

    def toggle_collapse(self):
        self._collapsed = not self._collapsed
        target = cfg.SIDEBAR_W_COLLAPSED if self._collapsed else cfg.SIDEBAR_W
        for anim, prop in ((self._anim, b"minimumWidth"), (self._anim2, b"maximumWidth")):
            anim.stop()
            anim.setDuration(240)
            anim.setEasingCurve(QEasingCurve.OutCubic)
            anim.setStartValue(self.width())
            anim.setEndValue(target)
            anim.start()
        for b in self.buttons:
            b.set_collapsed(self._collapsed)
        self.section_nav.setVisible(not self._collapsed)
        self.user_name.setVisible(not self._collapsed)
        self.user_role.setVisible(not self._collapsed)
        self.toggle.setText("⟩" if self._collapsed else "⟨  Свернуть панель")


# -------------------------------------------------------------- MainWindow
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.accent_key = DEFAULT_ACCENT
        self.setWindowTitle(f"{cfg.APP_NAME} {cfg.APP_VERSION}")
        self.setWindowIcon(QIcon(str(cfg.LOGO / "logo_256.png")))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumSize(cfg.WINDOW_MIN_W, cfg.WINDOW_MIN_H)
        self.resize(cfg.WINDOW_DEF_W, cfg.WINDOW_DEF_H)
        self.setMouseTracking(True)

        self._resizing = False
        self._resize_edge = ""
        self._press_geo = QRect()
        self._press_pos = QPoint()
        self._normal_geo: QRect | None = None

        # фон
        self.bg = BackgroundCanvas(self, "bg_main.jpg", self.accent_key)
        self.bg.setGeometry(self.rect())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.titlebar = TitleBar(self)
        root.addWidget(self.titlebar)

        mid = QWidget()
        mid.setObjectName("RootFrame")
        ml = QHBoxLayout(mid)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)
        self.sidebar = Sidebar(self)
        ml.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("RootFrame")
        ml.addWidget(self.stack, 1)
        root.addWidget(mid, 1)

        self._build_pages()
        self._build_tray()
        self.apply_accent(self.accent_key, first=True)

        grip = QSizeGrip(self)
        grip.setFixedSize(16, 16)
        self._grip = grip

    # ------------------------------------------------------------ страницы
    def _build_pages(self):
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            w.deleteLater()
        self.pages = [
            DashboardPage(self.accent_key),
            ToolsPage(self.accent_key),
            SettingsPage(self.accent_key, self.apply_accent, self.set_background),
            AboutPage(self.accent_key),
        ]
        for p in self.pages:
            self.stack.addWidget(p)

    def go(self, index: int):
        self.sidebar.set_active(index)
        self.stack.setCurrentIndex(index)

    # ---------------------------------------------------------------- тема
    def apply_accent(self, key: str, first: bool = False):
        if key not in ACCENTS or not ACCENTS[key].available:
            return
        keep = self.stack.currentIndex() if not first else 0
        self.accent_key = key
        QApplication.instance().setStyleSheet(build_qss(key))
        self.bg.set_accent(key)
        self.titlebar.badge.set_accent(ACCENTS[key].primary)
        self.sidebar.set_accent(key)
        if not first:
            self._build_pages()
            self.go(keep)
        self._update_tray_icon()

    def set_background(self, file_name: str):
        self.bg.set_image(file_name)

    # ---------------------------------------------------------------- трей
    def _build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self._update_tray_icon()
        self.tray.setToolTip(f"{cfg.APP_NAME} {cfg.APP_VERSION} — {cfg.APP_TAGLINE}")

        menu = QMenu()
        act_show = QAction("Открыть LIFE OS", self)
        act_show.triggered.connect(self.restore_from_tray)
        act_dash = QAction("Панель управления", self)
        act_dash.triggered.connect(lambda: (self.restore_from_tray(), self.go(0)))
        act_set = QAction("Настройки", self)
        act_set.triggered.connect(lambda: (self.restore_from_tray(), self.go(2)))
        act_quit = QAction("Выход", self)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_show)
        menu.addSeparator()
        menu.addAction(act_dash)
        menu.addAction(act_set)
        menu.addSeparator()
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _update_tray_icon(self):
        path = cfg.LOGO / "logo_tray_256.png"
        self.tray.setIcon(QIcon(str(path)))

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.restore_from_tray()

    def hide_to_tray(self):
        self.hide()
        if self.tray.isSystemTrayAvailable():
            self.tray.showMessage(
                cfg.APP_NAME,
                "Оболочка свёрнута в трей. Двойной клик по значку — вернуть окно.",
                QIcon(str(cfg.LOGO / "logo_tray_256.png")), 2600,
            )

    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------- окно/геометрия
    def toggle_max(self):
        if self.isMaximized():
            self.showNormal()
            self.titlebar.btn_max.setText("□")
        else:
            self.showMaximized()
            self.titlebar.btn_max.setText("❐")

    def resizeEvent(self, e):
        self.bg.setGeometry(self.rect())
        self.bg.lower()
        if hasattr(self, "_grip"):
            self._grip.move(self.width() - 20, self.height() - 20)
        super().resizeEvent(e)

    # ----- ресайз за края безрамочного окна
    def _edge_at(self, pos: QPoint) -> str:
        m = cfg.RESIZE_MARGIN
        w, h = self.width(), self.height()
        edge = ""
        if pos.y() <= m:
            edge += "t"
        elif pos.y() >= h - m:
            edge += "b"
        if pos.x() <= m:
            edge += "l"
        elif pos.x() >= w - m:
            edge += "r"
        return edge

    @staticmethod
    def _cursor_for(edge: str):
        return {
            "t": Qt.SizeVerCursor, "b": Qt.SizeVerCursor,
            "l": Qt.SizeHorCursor, "r": Qt.SizeHorCursor,
            "tl": Qt.SizeFDiagCursor, "br": Qt.SizeFDiagCursor,
            "tr": Qt.SizeBDiagCursor, "bl": Qt.SizeBDiagCursor,
        }.get(edge, Qt.ArrowCursor)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and not self.isMaximized():
            edge = self._edge_at(e.position().toPoint())
            if edge:
                self._resizing = True
                self._resize_edge = edge
                self._press_geo = self.geometry()
                self._press_pos = e.globalPosition().toPoint()
                e.accept()
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        pos = e.position().toPoint()
        if self._resizing:
            d = e.globalPosition().toPoint() - self._press_pos
            g = QRect(self._press_geo)
            if "l" in self._resize_edge:
                g.setLeft(g.left() + d.x())
            if "r" in self._resize_edge:
                g.setRight(g.right() + d.x())
            if "t" in self._resize_edge:
                g.setTop(g.top() + d.y())
            if "b" in self._resize_edge:
                g.setBottom(g.bottom() + d.y())
            if g.width() >= self.minimumWidth() and g.height() >= self.minimumHeight():
                self.setGeometry(g)
            e.accept()
            return
        self.setCursor(self._cursor_for(self._edge_at(pos)) if not self.isMaximized()
                       else Qt.ArrowCursor)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._resizing = False
        self._resize_edge = ""
        super().mouseReleaseEvent(e)

    def leaveEvent(self, e):
        self.unsetCursor()
        super().leaveEvent(e)
