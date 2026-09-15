"""LIFE OS — раздел «Инструменты»: список средств обслуживания и окно работы."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from . import config as cfg
from .theme import current_accent
from .elevation import can_elevate, is_admin, relaunch_as_admin
from .tools_engine import (
    ALL_TOOLS, CleanWorker, ScanItem, ScanResult, ScanWorker, Tool,
    disk_usage, human_count, human_size,
)
from .update_ui import ProgressBar
from .widgets import GlassCard, ImagePanel, OrbIcon, make_label, soft_shadow


# =============================================================== карточка
class ToolCard(GlassCard):
    """Плитка одного инструмента в списке."""

    launched = Signal(object)

    def __init__(self, tool: Tool, parent=None):
        super().__init__(padding=20, spacing=12, hoverable=True, parent=parent)
        self._tool = tool
        self.setCursor(Qt.PointingHandCursor)

        top = QHBoxLayout()
        top.setSpacing(14)
        top.addWidget(OrbIcon(tool.icon, 52, hover=True), 0, Qt.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(4)
        col.addWidget(make_label(tool.name, "CardTitle"))
        sub = make_label(tool.subtitle, "CardBody")
        sub.setWordWrap(True)
        col.addWidget(sub)
        top.addLayout(col, 1)
        self.body.addLayout(top)

        ok, why = tool.available()
        row = QHBoxLayout()
        self.status = make_label(
            "Готов к проверке" if ok else why, "Caption")
        self.status.setWordWrap(True)
        row.addWidget(self.status, 1)
        self.btn = QPushButton("Проверить")
        self.btn.setObjectName("Ghost")
        self.btn.setFixedHeight(36)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.setEnabled(ok)
        self.btn.clicked.connect(lambda: self.launched.emit(self._tool))
        row.addWidget(self.btn)
        self.body.addLayout(row)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton and self.btn.isEnabled():
            self.launched.emit(self._tool)
        super().mouseReleaseEvent(e)

    def set_result(self, size: int, count: int):
        if count:
            self.status.setText(
                f"Найдено {human_size(size)} · "
                f"{human_count(count, ('объект', 'объекта', 'объектов'))}")
            self.btn.setText("Открыть")
        else:
            self.status.setText("Ничего лишнего не найдено")
            self.btn.setText("Проверить снова")

    def set_cleaned(self, freed: int):
        self.status.setText(f"Очищено · освобождено {human_size(freed)}")
        self.btn.setText("Проверить снова")


# ============================================================ строка списка
class ResultRow(QWidget):
    """Одна найденная группа с галочкой."""

    toggled = Signal()

    def __init__(self, item: ScanItem, parent=None):
        super().__init__(parent)
        self.item = item
        self.setObjectName("Transparent")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 9, 14, 9)
        lay.setSpacing(12)

        self.box = QCheckBox()
        self.box.setChecked(item.checked)
        self.box.setCursor(Qt.PointingHandCursor)
        self.box.stateChanged.connect(self._changed)
        lay.addWidget(self.box, 0, Qt.AlignVCenter)

        col = QVBoxLayout()
        col.setSpacing(2)
        title = make_label(item.title, "CardBody")
        title.setWordWrap(False)
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        col.addWidget(title)
        det = make_label(item.detail, "Caption")
        det.setWordWrap(False)
        det.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        col.addWidget(det)
        lay.addLayout(col, 1)

        if item.risky:
            warn = make_label("важное", "BadgeMuted")
            warn.setAlignment(Qt.AlignCenter)
            lay.addWidget(warn, 0, Qt.AlignVCenter)
        lay.addWidget(make_label(human_size(item.size), "Mono"),
                      0, Qt.AlignVCenter)

    def _changed(self, _):
        self.item.checked = self.box.isChecked()
        self.toggled.emit()


# ================================================================= окно
class ToolWindow(QWidget):
    """Окно работы инструмента: сканирование → список → подтверждение."""

    scanned = Signal(object)        # ScanResult
    cleaned_up = Signal(int)        # освобождено байт

    def __init__(self, tool: Tool, parent=None):
        super().__init__(parent)
        self._tool = tool
        self._result: ScanResult | None = None
        self._rows: list[ResultRow] = []
        self._scan: ScanWorker | None = None
        self._clean: CleanWorker | None = None
        self._busy = False

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(820, 660)
        self._drag = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # -------- шапка --------
        hero = ImagePanel(cfg.BACKGROUNDS / "tools_hero.jpg", overlay=0.64,
                          radius=18)
        hero.setFixedHeight(150)
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(28, 22, 26, 22)
        hl.setSpacing(18)
        col = QVBoxLayout()
        col.setSpacing(5)
        col.addStretch(1)
        col.addWidget(make_label("ИНСТРУМЕНТ", "CardKicker"))
        col.addWidget(make_label(tool.name, "HeroTitle"))
        col.addWidget(make_label(tool.subtitle, "CardBody"))
        col.addStretch(1)
        hl.addLayout(col, 1)
        hl.addWidget(OrbIcon(tool.icon, 86), 0, Qt.AlignVCenter)
        root.addWidget(hero)

        # -------- список --------
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget()
        host.setObjectName("Transparent")
        self.list_lay = QVBoxLayout(host)
        self.list_lay.setContentsMargins(24, 20, 24, 16)
        self.list_lay.setSpacing(10)
        self.scroll.setWidget(host)
        root.addWidget(self.scroll, 1)

        self.placeholder = make_label("Идёт проверка…", "CardBody")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.list_lay.addWidget(self.placeholder)
        self.list_lay.addStretch(1)

        # -------- прогресс --------
        self.prog_box = QWidget()
        self.prog_box.setObjectName("Transparent")
        pl = QVBoxLayout(self.prog_box)
        pl.setContentsMargins(26, 4, 26, 6)
        pl.setSpacing(7)
        row = QHBoxLayout()
        self.prog_label = make_label("Подготовка…", "CardBody")
        self.prog_label.setWordWrap(False)
        self.prog_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        row.addWidget(self.prog_label, 1)
        self.prog_pct = make_label("0%", "MonoAccent")
        row.addWidget(self.prog_pct)
        pl.addLayout(row)
        self.bar = ProgressBar()
        pl.addWidget(self.bar)
        root.addWidget(self.prog_box)

        # -------- низ --------
        foot = QWidget()
        foot.setObjectName("Transparent")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(26, 14, 26, 20)
        fl.setSpacing(11)
        self.summary = make_label("", "Caption")
        self.summary.setWordWrap(False)
        self.summary.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        fl.addWidget(self.summary, 1)

        self.btn_all = QPushButton("Снять выделение")
        self.btn_all.setObjectName("Link")
        self.btn_all.setCursor(Qt.PointingHandCursor)
        self.btn_all.clicked.connect(self._toggle_all)
        self.btn_all.setVisible(False)
        fl.addWidget(self.btn_all)

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.setObjectName("Ghost")
        self.btn_close.setFixedHeight(42)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close)
        fl.addWidget(self.btn_close)

        self.btn_go = QPushButton(tool.action)
        self.btn_go.setObjectName("Primary")
        self.btn_go.setFixedHeight(42)
        self.btn_go.setMinimumWidth(180)
        self.btn_go.setCursor(Qt.PointingHandCursor)
        self.btn_go.setEnabled(False)
        self.btn_go.clicked.connect(self._start_clean)
        fl.addWidget(self.btn_go)
        root.addWidget(foot)

        soft_shadow(self, 60, 200, 18)
        QTimer.singleShot(120, self._start_scan)

    # ------------------------------------------------------------ рисование
    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        path = QPainterPath()
        path.addRoundedRect(self.rect().adjusted(1, 1, -1, -1), 18, 18)
        p.fillPath(path, QColor(13, 15, 21, 252))
        pen_c = QColor(current_accent().primary)
        pen_c.setAlpha(46)
        p.setPen(pen_c)
        p.drawPath(path)
        p.end()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.position().y() < 150:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, _):
        self._drag = None

    def center_on_screen(self):
        scr = self.screen() or self.parent().screen()
        if scr:
            g = scr.availableGeometry()
            self.move(g.center().x() - self.width() // 2,
                      g.center().y() - self.height() // 2)

    # ------------------------------------------------------- сканирование
    def _start_scan(self):
        self._busy = True
        self.prog_box.setVisible(True)
        self.bar.setValue(0)
        self.prog_label.setText("Поиск…")
        self._scan = ScanWorker(self._tool, self)
        self._scan.progress.connect(self._on_progress)
        self._scan.done.connect(self._on_scanned)
        self._scan.failed.connect(self._on_failed)
        self._scan.start()

    def _on_progress(self, pct: int, text: str):
        self.bar.setValue(pct)
        self.prog_pct.setText(f"{pct}%")
        self.prog_label.setText(text)

    def _on_scanned(self, res: ScanResult):
        self._busy = False
        self._result = res
        self.prog_box.setVisible(False)
        while self.list_lay.count():
            it = self.list_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self._rows.clear()

        if not res.items:
            msg = make_label(res.note or "Ничего не найдено.", "CardBody")
            msg.setAlignment(Qt.AlignCenter)
            msg.setWordWrap(True)
            self.list_lay.addStretch(1)
            self.list_lay.addWidget(msg)
            self.list_lay.addStretch(1)
            self.summary.setText("Чисто — удалять нечего.")
            self.btn_go.setVisible(False)
            self.btn_close.setText("Готово")
            self.scanned.emit(res)
            return

        if res.locked_paths and can_elevate():
            self.list_lay.addWidget(self._admin_banner(res.locked_paths))

        if res.note:
            note = make_label(res.note, "Caption")
            note.setWordWrap(True)
            self.list_lay.addWidget(note)

        card = GlassCard(padding=6, spacing=0, hoverable=False)
        for item in res.items:
            row = ResultRow(item)
            row.toggled.connect(self._refresh_summary)
            card.body.addWidget(row)
            self._rows.append(row)
        self.list_lay.addWidget(card)
        self.list_lay.addStretch(1)

        self.btn_all.setVisible(True)
        self.btn_go.setEnabled(True)
        self._refresh_summary()
        self.scanned.emit(res)

    def _admin_banner(self, locked: int) -> QWidget:
        """Плашка: часть системных папок закрыта без прав администратора."""
        card = GlassCard(padding=18, spacing=12, hoverable=False)
        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(OrbIcon("admin", 44), 0, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(make_label("НУЖНЫ ПРАВА АДМИНИСТРАТОРА", "CardKicker"))
        col.addWidget(make_label(
            f"Недоступно системных папок: {locked}", "CardTitle"))
        txt = make_label(
            "Программа запущена от обычного пользователя, поэтому часть "
            "системного мусора не видна и не удаляется. Перезапустите "
            "с правами администратора, чтобы очистить всё.", "CardBody")
        txt.setWordWrap(True)
        col.addWidget(txt)
        row.addLayout(col, 1)
        btn = QPushButton("Перезапустить от админа")
        btn.setObjectName("Primary")
        btn.setFixedHeight(40)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._ask_elevate)
        row.addWidget(btn, 0, Qt.AlignVCenter)
        card.body.addLayout(row)
        return card

    def _ask_elevate(self):
        ok = QMessageBox.question(
            self, "Права администратора",
            "Перезапустить LIFE OS с правами администратора?\n\n"
            "Откроется стандартный запрос Windows. Текущее окно закроется, "
            "программа откроется заново.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ok != QMessageBox.Yes:
            return
        if relaunch_as_admin():
            QApplication.quit()
        else:
            QMessageBox.information(
                self, "Права администратора",
                "Запуск с повышением прав отменён или недоступен.")

    def _refresh_summary(self):
        res = self._result
        if not res:
            return
        sel_size, sel_count = res.selected_size, res.selected_count
        if sel_count == res.total_count:
            self.summary.setText(
                f"Выбрано всё: {human_size(sel_size)}")
        else:
            self.summary.setText(
                f"Из {human_size(res.total_size)} выбрано {human_size(sel_size)}")
        self.btn_go.setEnabled(sel_count > 0)
        any_on = any(r.item.checked for r in self._rows)
        self.btn_all.setText("Снять выделение" if any_on else "Выбрать всё")

    def _toggle_all(self):
        target = not any(r.item.checked for r in self._rows)
        for r in self._rows:
            r.box.setChecked(target)

    # ------------------------------------------------------------- очистка
    def _start_clean(self):
        res = self._result
        if not res:
            return
        items = [i for i in res.items if i.checked]
        if not items:
            return
        self._busy = True
        self.btn_go.setEnabled(False)
        self.btn_go.setText("Очистка…")
        self.btn_all.setVisible(False)
        self.prog_box.setVisible(True)
        self.bar.setValue(0)
        self._clean = CleanWorker(self._tool, items, self)
        self._clean.progress.connect(self._on_progress)
        self._clean.done.connect(self._on_cleaned)
        self._clean.failed.connect(self._on_failed)
        self._clean.start()

    def _on_cleaned(self, freed: int, skipped: int = 0):
        self._busy = False
        self.prog_box.setVisible(False)
        while self.list_lay.count():
            it = self.list_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self._rows.clear()

        done = GlassCard(padding=26, spacing=12, hoverable=False)
        row = QHBoxLayout()
        row.setSpacing(16)
        row.addWidget(OrbIcon("done", 64), 0, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(4)
        col.addWidget(make_label("ГОТОВО", "CardKicker"))
        col.addWidget(make_label(f"Освобождено {human_size(freed)}", "CardTitle"))
        if skipped:
            tail = make_label(
                f"Не удалось удалить файлов: {skipped}. Обычно это файлы, "
                f"занятые работающими программами" +
                (" — помогут права администратора."
                 if can_elevate() else ". Закройте их и повторите."),
                "CardBody")
            tail.setWordWrap(True)
            col.addWidget(tail)
        else:
            col.addWidget(make_label(
                "Можно закрыть окно или проверить ещё раз.", "CardBody"))
        row.addLayout(col, 1)
        done.body.addLayout(row)
        self.list_lay.addStretch(1)
        self.list_lay.addWidget(done)
        self.list_lay.addStretch(1)

        self.summary.setText(
            f"Освобождено {human_size(freed)}"
            + (f" · пропущено {skipped}" if skipped else ""))
        self.btn_go.setText("Проверить снова")
        self.btn_go.setEnabled(True)
        self.btn_go.clicked.disconnect()
        self.btn_go.clicked.connect(self._rescan)
        self.btn_close.setText("Готово")
        self.cleaned = freed
        self.cleaned_up.emit(freed)

    def _rescan(self):
        self.btn_go.clicked.disconnect()
        self.btn_go.clicked.connect(self._start_clean)
        self.btn_go.setText(self._tool.action)
        self.btn_go.setEnabled(False)
        while self.list_lay.count():
            it = self.list_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self._start_scan()

    def _on_failed(self, msg: str):
        self._busy = False
        self.prog_box.setVisible(False)
        while self.list_lay.count():
            it = self.list_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self._rows.clear()
        card = GlassCard(padding=26, spacing=12, hoverable=False)
        row = QHBoxLayout()
        row.setSpacing(16)
        row.addWidget(OrbIcon("warning", 60), 0, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(4)
        col.addWidget(make_label("НЕ ПОЛУЧИЛОСЬ", "CardKicker"))
        col.addWidget(make_label("Операция прервана", "CardTitle"))
        det = make_label(msg, "CardBody")
        det.setWordWrap(True)
        col.addWidget(det)
        row.addLayout(col, 1)
        card.body.addLayout(row)
        self.list_lay.addStretch(1)
        self.list_lay.addWidget(card)
        self.list_lay.addStretch(1)
        self.summary.setText("Проверьте права доступа и попробуйте снова.")
        self.btn_go.setEnabled(False)

    def closeEvent(self, e):
        # Дожидаемся фоновых потоков, иначе Qt ругается на уничтожение
        # работающего QThread.
        for w in (self._scan, self._clean):
            if w is None:
                continue
            if w.isRunning():
                w.requestInterruption()
                if not w.wait(3000):
                    w.terminate()
                    w.wait(1000)
            w.setParent(None)
        self._scan = self._clean = None
        super().closeEvent(e)


# ================================================================ страница
class ToolsPage(QScrollArea):
    """Список инструментов обслуживания системы."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        host = QWidget()
        host.setObjectName("Transparent")
        self.body = QVBoxLayout(host)
        self.body.setContentsMargins(32, 22, 32, 32)
        self.body.setSpacing(18)
        self.setWidget(host)

        self._win: ToolWindow | None = None

        head = QWidget()
        head.setObjectName("Transparent")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(0, 0, 0, 0)
        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(make_label("Инструменты", "PageTitle"))
        col.addWidget(make_label(
            "Наведение порядка на диске · ничего не удаляется без вашего согласия",
            "PageSub"))
        hl.addLayout(col)
        hl.addStretch(1)
        hl.addWidget(OrbIcon("tools", 46), 0, Qt.AlignVCenter)
        self.body.addWidget(head)

        hero = ImagePanel(cfg.BACKGROUNDS / "tools_hero.jpg", overlay=0.62)
        hero.setFixedHeight(170)
        ll = QHBoxLayout(hero)
        ll.setContentsMargins(30, 24, 30, 24)
        ll.setSpacing(18)
        c2 = QVBoxLayout()
        c2.setSpacing(6)
        c2.addWidget(make_label("ОБСЛУЖИВАНИЕ СИСТЕМЫ", "CardKicker"))
        c2.addWidget(make_label("Освободите место на диске", "HeroTitle"))
        sub = make_label(
            "Каждый инструмент сначала показывает, что нашёл, "
            "и только потом — по вашей команде — удаляет.", "CardBody")
        sub.setWordWrap(True)
        c2.addWidget(sub)
        ll.addLayout(c2, 1)
        ll.addWidget(OrbIcon("broom", 92), 0, Qt.AlignVCenter)
        self.body.addWidget(hero)

        self._disk_slot = QVBoxLayout()
        self._disk_slot.setContentsMargins(0, 0, 0, 0)
        self._disk_card = None
        self.body.addLayout(self._disk_slot)
        self.refresh_disk()

        self.body.addWidget(make_label("ДОСТУПНЫЕ ИНСТРУМЕНТЫ", "SectionLabel"))
        self._build_grid()
        self.body.addStretch(1)

    def refresh_disk(self):
        """Пересобирает карточку свободного места."""
        if self._disk_card is not None:
            self._disk_card.setParent(None)
            self._disk_card.deleteLater()
            self._disk_card = None
        disks = disk_usage()
        if disks:
            card = GlassCard(padding=20, spacing=14, hoverable=False)
            top = QHBoxLayout()
            top.setSpacing(14)
            top.addWidget(OrbIcon("disk", 44), 0, Qt.AlignVCenter)
            c3 = QVBoxLayout()
            c3.setSpacing(2)
            c3.addWidget(make_label("МЕСТО НА ДИСКЕ", "CardKicker"))
            free_all = sum(t - u for _l, u, t in disks)
            c3.addWidget(make_label(
                f"Свободно {human_size(free_all)}", "CardTitle"))
            top.addLayout(c3, 1)
            top.addWidget(OrbIcon("analyze", 38), 0, Qt.AlignVCenter)
            card.body.addLayout(top)
            for label, used, total in disks[:4]:
                row = QHBoxLayout()
                row.setSpacing(12)
                name = make_label(label, "CardBody")
                name.setMinimumWidth(130)
                row.addWidget(name)
                bar = ProgressBar()
                bar.setFixedHeight(8)
                bar.setValue(used / max(1, total) * 100)
                row.addWidget(bar, 1)
                row.addWidget(make_label(
                    f"{human_size(total - used)} свободно", "Mono"))
                card.body.addLayout(row)
            self._disk_slot.addWidget(card)
            self._disk_card = card

    def _build_grid(self):
        grid = QVBoxLayout()
        grid.setSpacing(14)
        pair: QHBoxLayout | None = None
        self.cards: list[ToolCard] = []
        for n, tool in enumerate(ALL_TOOLS):
            if n % 2 == 0:
                pair = QHBoxLayout()
                pair.setSpacing(14)
                grid.addLayout(pair)
            card = ToolCard(tool)
            card.launched.connect(self.open_tool)
            pair.addWidget(card)
            self.cards.append(card)
        if len(ALL_TOOLS) % 2:
            pair.addStretch(1)
        self.body.addLayout(grid)

    def open_tool(self, tool: Tool):
        if self._win is not None and self._win.isVisible():
            self._win.raise_()
            self._win.activateWindow()
            return
        card = next((c for c in self.cards if c._tool is tool), None)
        win = ToolWindow(tool)
        if card is not None:
            win.scanned.connect(
                lambda res, c=card: c.set_result(res.total_size, res.total_count))
            win.cleaned_up.connect(lambda freed, c=card: c.set_cleaned(freed))
            win.cleaned_up.connect(lambda _f: self.refresh_disk())
        win.center_on_screen()
        self._win = win
        win.show()
        win.raise_()
        win.activateWindow()
