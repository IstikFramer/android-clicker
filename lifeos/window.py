"""LIFE OS — главное окно: титлбар, выдвижная боковая панель, страницы, трей."""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, QRect,
    QTimer, Qt,
)
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtWidgets import (
    QApplication, QGraphicsOpacityEffect, QHBoxLayout, QMenu, QPushButton,
    QSizeGrip, QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget,
)

from . import config as cfg
from . import icons
from .anim import driver
from .eula import EulaWindow
from .pages import AboutPage, HomePage, SettingsPage
from .settings import settings
from .theme import build_qss, current_accent
from .widgets import (
    BackgroundCanvas, Divider, IconButton, LogoOrb, NavButton, make_label,
)

NAV_ITEMS = [
    ("Главная", "home"),
    ("Настройки", "sliders"),
    ("О программе", "info"),
]


# ------------------------------------------------------------------ Titlebar
class TitleBar(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__(win)
        self.setObjectName("TitleBar")
        self.setFixedHeight(cfg.TITLEBAR_H)
        self._win = win
        self._drag: QPoint | None = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 8, 12, 8)
        lay.setSpacing(10)

        self.orb = LogoOrb(size=30, breathe=True, asset="logo_mini_256.png")
        lay.addWidget(self.orb)
        lay.addWidget(make_label(cfg.APP_NAME, "TitleText"))
        self.version = make_label(cfg.APP_VERSION, "TitleVersion")
        lay.addWidget(self.version, 0, Qt.AlignVCenter)
        lay.addSpacing(4)
        self.sub = make_label("· " + cfg.APP_TAGLINE, "TitleSub")
        lay.addWidget(self.sub)
        lay.addStretch(1)

        self.btn_min = IconButton("minus", 34, 17, tooltip="Свернуть")
        self.btn_max = IconButton("square", 34, 15, tooltip="Развернуть")
        self.btn_close = IconButton("close", 34, 16, danger=True, tooltip="Закрыть")
        self.btn_min.clicked.connect(win.showMinimized)
        self.btn_max.clicked.connect(win.toggle_max)
        self.btn_close.clicked.connect(win.close_action)
        for b in (self.btn_min, self.btn_max, self.btn_close):
            lay.addWidget(b)

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


# ------------------------------------------------------------------- Sidebar
class Sidebar(QWidget):
    def __init__(self, win: "MainWindow"):
        super().__init__(win)
        self.setObjectName("Sidebar")
        self.setFixedWidth(cfg.SIDEBAR_W)
        self._win = win
        self._collapsed = False

        lay = QVBoxLayout(self)
        lay.setContentsMargins(13, 16, 13, 16)
        lay.setSpacing(8)

        self.section = make_label("РАЗДЕЛЫ", "SidebarSection")
        lay.addWidget(self.section)

        self.buttons: list[NavButton] = []
        for i, (text, icon_name) in enumerate(NAV_ITEMS):
            b = NavButton(text, icon_name)
            b.clicked.connect(lambda _=False, idx=i: win.go(idx))
            lay.addWidget(b)
            self.buttons.append(b)
        self.buttons[0].setChecked(True)

        lay.addStretch(1)
        lay.addWidget(Divider())

        self.profile = QWidget()
        self.profile.setObjectName("Transparent")
        pl = QHBoxLayout(self.profile)
        pl.setContentsMargins(4, 6, 4, 6)
        pl.setSpacing(11)
        self.avatar = LogoOrb(size=34, breathe=False, asset="logo_mini_256.png")
        pl.addWidget(self.avatar)
        col = QVBoxLayout()
        col.setSpacing(1)
        self.user_name = make_label(cfg.DEV_NAME, "UserName")
        self.user_role = make_label(f"ВЕРСИЯ {cfg.APP_VERSION}", "UserRole")
        col.addWidget(self.user_name)
        col.addWidget(self.user_role)
        pl.addLayout(col)
        pl.addStretch(1)
        lay.addWidget(self.profile)

        self.toggle = QPushButton("  Свернуть панель")
        self.toggle.setObjectName("SidebarToggle")
        self.toggle.setFixedHeight(36)
        self.toggle.setCursor(Qt.PointingHandCursor)
        self.toggle.setIcon(icons.icon("chevron_left", 16, "#9DABC2"))
        self.toggle.clicked.connect(self.toggle_collapse)
        lay.addWidget(self.toggle)

        self._anim = QParallelAnimationGroup(self)
        for prop in (b"minimumWidth", b"maximumWidth"):
            a = QPropertyAnimation(self, prop, self)
            a.setEasingCurve(QEasingCurve.OutCubic)
            self._anim.addAnimation(a)

    def set_active(self, index: int):
        for i, b in enumerate(self.buttons):
            b.setChecked(i == index)

    def refresh_icons(self):
        self.toggle.setIcon(icons.icon(
            "chevron_right" if self._collapsed else "chevron_left", 16, "#9DABC2"))

    def toggle_collapse(self):
        self._collapsed = not self._collapsed
        target = cfg.SIDEBAR_W_COLLAPSED if self._collapsed else cfg.SIDEBAR_W
        dur = int(260 / max(0.2, settings.speed)) if settings.get("animations") else 0
        self._anim.stop()
        for i in range(self._anim.animationCount()):
            a = self._anim.animationAt(i)
            a.setDuration(dur)
            a.setStartValue(self.width())
            a.setEndValue(target)
        self._anim.start()

        for b in self.buttons:
            b.set_collapsed(self._collapsed)
        self.section.setVisible(not self._collapsed)
        self.user_name.setVisible(not self._collapsed)
        self.user_role.setVisible(not self._collapsed)
        self.profile.setVisible(not self._collapsed)
        self.toggle.setText("" if self._collapsed else "  Свернуть панель")
        self.refresh_icons()


# ---------------------------------------------------------------- MainWindow
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{cfg.APP_NAME} {cfg.APP_VERSION}")
        self.setWindowIcon(QIcon(str(cfg.LOGO / "logo_256.png")))
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setMinimumSize(cfg.WINDOW_MIN_W, cfg.WINDOW_MIN_H)
        self.resize(cfg.WINDOW_DEF_W, cfg.WINDOW_DEF_H)
        self.setMouseTracking(True)

        self._resizing = False
        self._edge = ""
        self._press_geo = QRect()
        self._press_pos = QPoint()
        self._eula_win: EulaWindow | None = None
        self._page_anim: QPropertyAnimation | None = None

        self.bg = BackgroundCanvas(self)
        self.bg.setGeometry(self.rect())

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.titlebar = TitleBar(self)
        root.addWidget(self.titlebar)

        mid = QWidget()
        mid.setObjectName("Transparent")
        ml = QHBoxLayout(mid)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)
        self.sidebar = Sidebar(self)
        ml.addWidget(self.sidebar)
        self.stack = QStackedWidget()
        self.stack.setObjectName("Transparent")
        ml.addWidget(self.stack, 1)
        root.addWidget(mid, 1)

        self._build_pages()
        self._build_tray()

        settings.subscribe(self._on_setting)
        self._apply_runtime()

        self._grip = QSizeGrip(self)
        self._grip.setFixedSize(16, 16)

    # -------------------------------------------------------------- страницы
    def _build_pages(self):
        current = self.stack.currentIndex() if self.stack.count() else 0
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            driver().unsubscribe(w)
            w.deleteLater()
        self.pages = [
            HomePage(),
            SettingsPage(self.restyle, self.bg.reload),
            AboutPage(self.show_eula),
        ]
        for p in self.pages:
            self.stack.addWidget(p)
        self.stack.setCurrentIndex(min(current, len(self.pages) - 1))

    def go(self, index: int):
        if index == self.stack.currentIndex():
            self.sidebar.set_active(index)
            return
        self.sidebar.set_active(index)
        self.stack.setCurrentIndex(index)
        page = self.stack.currentWidget()
        if not settings.get("animations"):
            return
        eff = QGraphicsOpacityEffect(page)
        page.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", page)
        anim.setDuration(int(230 / max(0.2, settings.speed)))
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda p=page: p.setGraphicsEffect(None))
        self._page_anim = anim
        anim.start()

    # ------------------------------------------------------------ настройки
    def _on_setting(self, key: str, value):
        if key in ("accent", "glass_opacity", "glow_strength", "corner_radius", "ui_scale"):
            self.restyle(rebuild=key in ("ui_scale", "corner_radius"))
        elif key in ("fps_limit", "anim_speed", "animations", "power_saving"):
            self._apply_runtime()
        elif key == "heavy_effects":
            self.restyle(rebuild=True)
        elif key == "background":
            self.bg.reload()

    def _apply_runtime(self):
        fps = settings.get("fps_limit")
        if settings.get("power_saving"):
            fps = min(fps, 30)
        driver().set_fps(fps)
        driver().set_speed(settings.speed)
        driver().set_enabled(settings.get("animations"))
        self.update()

    def restyle(self, rebuild: bool = False):
        icons.clear_cache()
        QApplication.instance().setStyleSheet(build_qss())
        self._update_tray_icon()
        self.sidebar.refresh_icons()
        if rebuild:
            self._build_pages()
            self.sidebar.set_active(self.stack.currentIndex())
        self.bg.invalidate()
        self.update()

    # ---------------------------------------------------------------- соглашение
    def show_eula(self, first_run: bool = False):
        win = EulaWindow(first_run=first_run, parent=None)
        win.center_on_screen()
        self._eula_win = win
        if first_run:
            win.declined.connect(QApplication.instance().quit)
            win.accepted.connect(self.show)
        win.show()
        win.raise_()
        win.activateWindow()
        return win

    # --------------------------------------------------------------------- трей
    def _build_tray(self):
        self.tray = QSystemTrayIcon(self)
        self._update_tray_icon()
        self.tray.setToolTip(f"{cfg.APP_NAME} {cfg.APP_VERSION}")
        menu = QMenu()
        act_show = QAction("Открыть", self)
        act_show.triggered.connect(self.restore_from_tray)
        act_home = QAction("Главная", self)
        act_home.triggered.connect(lambda: (self.restore_from_tray(), self.go(0)))
        act_set = QAction("Настройки", self)
        act_set.triggered.connect(lambda: (self.restore_from_tray(), self.go(1)))
        act_quit = QAction("Выход", self)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_show)
        menu.addSeparator()
        menu.addAction(act_home)
        menu.addAction(act_set)
        menu.addSeparator()
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _update_tray_icon(self):
        self.tray.setIcon(QIcon(str(cfg.LOGO / "logo_tray_256.png")))

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.restore_from_tray()

    def close_action(self):
        if settings.get("close_to_tray"):
            self.hide_to_tray()
        else:
            QApplication.instance().quit()

    def hide_to_tray(self):
        self.hide()
        if settings.get("tray_notifications") and self.tray.isSystemTrayAvailable():
            self.tray.showMessage(
                cfg.APP_NAME,
                "Программа свёрнута в область уведомлений.",
                QIcon(str(cfg.LOGO / "logo_tray_256.png")), 2400)

    def restore_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    # ---------------------------------------------------------------- окно
    def toggle_max(self):
        if self.isMaximized():
            self.showNormal()
            self.titlebar.btn_max.set_icon_name("square")
        else:
            self.showMaximized()
            self.titlebar.btn_max.set_icon_name("restore")

    def resizeEvent(self, e):
        self.bg.setGeometry(self.rect())
        self.bg.lower()
        if hasattr(self, "_grip"):
            self._grip.move(self.width() - 20, self.height() - 20)
        super().resizeEvent(e)

    def _edge_at(self, pos: QPoint) -> str:
        m = cfg.RESIZE_MARGIN
        edge = ""
        if pos.y() <= m:
            edge += "t"
        elif pos.y() >= self.height() - m:
            edge += "b"
        if pos.x() <= m:
            edge += "l"
        elif pos.x() >= self.width() - m:
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
                self._edge = edge
                self._press_geo = self.geometry()
                self._press_pos = e.globalPosition().toPoint()
                e.accept()
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._resizing:
            d = e.globalPosition().toPoint() - self._press_pos
            g = QRect(self._press_geo)
            if "l" in self._edge:
                g.setLeft(g.left() + d.x())
            if "r" in self._edge:
                g.setRight(g.right() + d.x())
            if "t" in self._edge:
                g.setTop(g.top() + d.y())
            if "b" in self._edge:
                g.setBottom(g.bottom() + d.y())
            if g.width() >= self.minimumWidth() and g.height() >= self.minimumHeight():
                self.setGeometry(g)
            e.accept()
            return
        self.setCursor(self._cursor_for(self._edge_at(e.position().toPoint()))
                       if not self.isMaximized() else Qt.ArrowCursor)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._resizing = False
        self._edge = ""
        super().mouseReleaseEvent(e)

    def leaveEvent(self, e):
        self.unsetCursor()
        super().leaveEvent(e)
