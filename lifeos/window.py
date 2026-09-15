"""LIFE OS — главное окно: титлбар, выдвижная боковая панель, страницы, трей."""
from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve, QParallelAnimationGroup, QPoint, QPropertyAnimation, QRect,
    QTimer, Qt, Signal,
)
from PySide6.QtGui import QAction, QColor, QIcon
from PySide6.QtWidgets import (
    QMessageBox,
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
from .elevation import can_elevate, is_admin, relaunch_as_admin
from .tools_page import ToolsPage
from .update_ui import UpdateWindow
from .updater import CheckWorker, UpdateInfo
from .widgets import (
    BackgroundCanvas, Divider, GlowAware, IconButton, LogoOrb, NavButton,
    make_label,
)

CHECK_INTERVAL_MS = 60 * 60 * 1000   # раз в час

NAV_ITEMS = [
    ("Главная", "home"),
    ("Инструменты", "wrench"),
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

        self.btn_update = IconButton("download", 34, 17,
                                     tooltip="Доступно обновление")
        self.btn_update.setVisible(False)
        self.btn_update.clicked.connect(win.open_update_window)
        lay.addWidget(self.btn_update)

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
    update_state_changed = Signal(object)
    update_check_started = Signal()

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
        self._update_info: UpdateInfo | None = None
        self._update_win: UpdateWindow | None = None
        self._check_worker: CheckWorker | None = None
        self._notified_version = ""

        # Перегенерация QSS стоит ~60 мс, поэтому при быстром изменении
        # настроек (перетаскивание слайдера) запросы копятся и применяются
        # одним разом — интерфейс остаётся отзывчивым.
        self._restyle_timer = QTimer(self)
        self._restyle_timer.setSingleShot(True)
        self._restyle_timer.timeout.connect(self._do_restyle)
        self._restyle_pending = False

        # Полный обход дерева виджетов тоже недёшев, поэтому перерисовка
        # по изменению «силы свечения» так же копится и выполняется пакетом.
        self._repaint_timer = QTimer(self)
        self._repaint_timer.setSingleShot(True)
        self._repaint_timer.timeout.connect(self._do_repaint_all)

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

        # Проверка обновлений: первый раз через 4 секунды после старта
        # (чтобы не тормозить запуск), далее раз в час.
        self._check_timer = QTimer(self)
        self._check_timer.timeout.connect(lambda: self.check_updates(silent=True))
        self._apply_check_interval()
        QTimer.singleShot(4000, self._first_check)
        QTimer.singleShot(1200, self._show_whats_new_if_updated)
        QTimer.singleShot(2200, self._offer_admin)

    # -------------------------------------------------------------- страницы
    def _build_pages(self):
        current = self.stack.currentIndex() if self.stack.count() else 0
        while self.stack.count():
            w = self.stack.widget(0)
            self.stack.removeWidget(w)
            driver().unsubscribe(w)
            w.deleteLater()
        self.pages = [
            HomePage(self.open_update_window),
            ToolsPage(),
            SettingsPage(self.restyle, self.bg.reload),
            AboutPage(self.show_eula, self.check_updates,
                      self.open_update_window, self.elevate),
        ]
        for pg in self.pages:
            if hasattr(pg, "on_update_state"):
                self.update_state_changed.connect(pg.on_update_state)
            if hasattr(pg, "on_check_started"):
                self.update_check_started.connect(pg.on_check_started)
        if self._update_info is not None:
            self.update_state_changed.emit(self._update_info)
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
        if key == "glow_strength":
            # Свечение рисуется вручную в paintEvent виджетов: ни QSS,
            # ни кэш фона от него не зависят — достаточно перерисовки.
            # Фон входит в GlowAware, поэтому обновится вместе со всеми.
            self._repaint_all()
        elif key in ("accent", "glass_opacity", "corner_radius", "ui_scale"):
            self.restyle()
        elif key in ("fps_limit", "anim_speed", "animations", "power_saving"):
            self._apply_runtime()
        elif key == "heavy_effects":
            self.restyle()
        elif key == "background":
            self.bg.reload()
        elif key in ("auto_update_check", "update_interval_h"):
            self._apply_check_interval()

    def _repaint_all(self):
        if not self._repaint_timer.isActive():
            self._repaint_timer.start(60)

    def _do_repaint_all(self):
        for w in self.findChildren(GlowAware):
            w.update()

    def _apply_runtime(self):
        fps = settings.get("fps_limit")
        if settings.get("power_saving"):
            fps = min(fps, 30)
        driver().set_fps(fps)
        driver().set_speed(settings.speed)
        driver().set_enabled(settings.get("animations"))
        self.update()

    def restyle(self, rebuild: bool = False):
        """Запрашивает перестройку оформления (применится одним пакетом)."""
        self._restyle_pending = True
        if rebuild:
            self._restyle_rebuild = True
        if not self._restyle_timer.isActive():
            self._restyle_timer.start(60)

    def _do_restyle(self):
        if not self._restyle_pending:
            return
        self._restyle_pending = False
        rebuild = getattr(self, "_restyle_rebuild", False)
        self._restyle_rebuild = False
        icons.clear_cache()
        QApplication.instance().setStyleSheet(build_qss())
        self._update_tray_icon()
        self.sidebar.refresh_icons()
        if rebuild:
            self._build_pages()
            self.sidebar.set_active(self.stack.currentIndex())
        self.bg.invalidate()
        self._do_repaint_all()

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

    # -------------------------------------------------------------- права
    def _offer_admin(self):
        """Один раз предлагает перезапуск от администратора."""
        if not can_elevate() or settings.get("admin_prompt_shown"):
            return
        settings.set("admin_prompt_shown", True)
        box = QMessageBox(self)
        box.setWindowTitle("Права администратора")
        box.setIcon(QMessageBox.Information)
        box.setText("LIFE OS запущена от обычного пользователя.")
        box.setInformativeText(
            "Без прав администратора часть системного мусора "
            "(Windows\\Temp, Prefetch, дампы памяти) не удаляется.\n\n"
            "Перезапустить с правами администратора?")
        yes = box.addButton("Да, перезапустить", QMessageBox.AcceptRole)
        box.addButton("Не сейчас", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is yes:
            self.elevate()

    def elevate(self):
        """Перезапуск через UAC."""
        if relaunch_as_admin():
            QApplication.quit()
        else:
            QMessageBox.information(
                self, "Права администратора",
                "Запуск с повышением прав отменён или недоступен.")

    # ---------------------------------------------------------- обновления
    def _apply_check_interval(self):
        """Включает или выключает автопроверку согласно настройкам."""
        if settings.get("auto_update_check"):
            hours = max(1, int(settings.get("update_interval_h") or 1))
            self._check_timer.start(hours * 60 * 60 * 1000)
        else:
            self._check_timer.stop()

    def _first_check(self):
        if settings.get("auto_update_check"):
            self.check_updates(silent=True)

    def _show_whats_new_if_updated(self):
        """После установки новой версии один раз показывает список изменений."""
        seen = settings.get("last_seen_version") or ""
        if seen == cfg.APP_VERSION:
            return
        settings.set("last_seen_version", cfg.APP_VERSION)
        if not seen:
            return          # первый запуск — здороваться списком изменений не нужно
        self.go(0)
        if self.tray.isSystemTrayAvailable() and settings.get("tray_notifications"):
            self.tray.showMessage(
                f"{cfg.APP_NAME} обновлён до {cfg.APP_VERSION}",
                "Список изменений открыт на главной странице.",
                QIcon(str(cfg.ORBS / "done_128.png")), 5000)

    def check_updates(self, silent: bool = False):
        """Фоновая проверка новой версии."""
        if self._check_worker and self._check_worker.isRunning():
            return
        self._silent_check = silent
        self._check_worker = CheckWorker(self)
        self._check_worker.done.connect(self._on_check_done)
        self._check_worker.start()
        if not silent:
            self.update_check_started.emit()

    def _on_check_done(self, info: UpdateInfo):
        self._update_info = info
        silent = getattr(self, "_silent_check", True)
        self.titlebar.btn_update.setVisible(bool(info.available))
        self.update_state_changed.emit(info)

        if info.available and info.version != self._notified_version:
            self._notified_version = info.version
            if self.tray.isSystemTrayAvailable():
                self.tray.showMessage(
                    f"{cfg.APP_NAME} · доступно обновление",
                    f"Вышла версия {info.version}. Нажмите, чтобы установить.",
                    QIcon(str(cfg.ORBS / "update_128.png")), 6000)
            self.tray.setToolTip(
                f"{cfg.APP_NAME} {cfg.APP_VERSION} · доступна версия {info.version}")
        elif not info.available and not silent:
            if self.tray.isSystemTrayAvailable():
                self.tray.showMessage(
                    cfg.APP_NAME, "Установлена последняя версия.",
                    QIcon(str(cfg.ORBS / "done_128.png")), 3000)

    def open_update_window(self):
        info = self._update_info
        if not info or not info.available:
            self.check_updates(silent=False)
            return
        if self._update_win is not None and self._update_win.isVisible():
            self._update_win.raise_()
            self._update_win.activateWindow()
            return
        try:
            win = UpdateWindow(info)
        except Exception as exc:                    # noqa: BLE001
            # Окно не должно ронять программу из-за неожиданного манифеста:
            # сообщаем и предлагаем скачать обновление вручную.
            import traceback
            traceback.print_exc()
            QMessageBox.warning(
                self, "Обновление",
                f"Не удалось показать окно обновления.\n\n{exc}\n\n"
                f"Скачать новую версию можно на странице проекта:\n{info.page}")
            return
        win.center_on_screen()
        self._update_win = win
        win.show()
        win.raise_()
        win.activateWindow()

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
        act_set.triggered.connect(lambda: (self.restore_from_tray(), self.go(2)))
        act_upd = QAction("Проверить обновления", self)
        act_upd.triggered.connect(lambda: self.check_updates(silent=False))
        act_quit = QAction("Выход", self)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_show)
        menu.addSeparator()
        menu.addAction(act_home)
        menu.addAction(act_set)
        menu.addSeparator()
        menu.addAction(act_upd)
        menu.addAction(act_quit)
        self.tray.setContextMenu(menu)
        self.tray.messageClicked.connect(self.open_update_window)
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
