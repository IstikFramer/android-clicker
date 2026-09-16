"""LIFE OS — раздел «Инструменты».

Устроен как набор категорий: на первом экране крупные кнопки разделов
(Очистка диска, Автозагрузка, Процессы и так далее). По нажатию
открывается вложенная вкладка со стрелкой «назад» — разные инструменты
не смешиваются в одном списке.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QFrame, QHBoxLayout, QMessageBox, QPushButton,
    QScrollArea, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget,
)

from . import config as cfg
from .elevation import can_elevate, relaunch_as_admin
from .system_tools import (
    SystemWorker, TableResult, disable_startup, kill_process,
)
from .theme import current_accent
from .tools_engine import (
    ALL_TOOLS, CleanWorker, ScanItem, ScanResult, ScanWorker, Tool,
    disk_usage, human_count, human_size,
)
from .update_ui import ProgressBar
from .widgets import (
    GlassCard, HelpDot, IconButton, ImagePanel, OrbIcon, make_label,
    soft_shadow,
)


# =========================================================== описание разделов
class Category:
    """Раздел инструментов: заголовок, иконка, содержимое."""

    def __init__(self, key: str, name: str, subtitle: str, icon: str,
                 hint: str, kind: str = "cleanup"):
        self.key = key
        self.name = name
        self.subtitle = subtitle
        self.icon = icon
        self.hint = hint
        self.kind = kind          # cleanup | table


CATEGORIES = [
    Category(
        "cleanup", "Очистка диска",
        "Временные файлы, Корзина, кэш браузеров, дубликаты",
        "broom",
        "Шесть средств, освобождающих место на диске. Каждое сначала "
        "показывает, что нашло, и удаляет только после вашего подтверждения.",
        "cleanup"),
    Category(
        "startup", "Автозагрузка",
        "Что запускается вместе с Windows",
        "admin",
        "Список программ, стартующих при входе в систему. Лишние записи "
        "замедляют включение компьютера — их можно отключить. Записи "
        "драйверов и антивируса трогать не стоит.",
        "table"),
    Category(
        "processes", "Процессы",
        "Кто занимает оперативную память",
        "monitor",
        "Работающие программы, отсортированные по объёму занятой памяти. "
        "Помогает понять, из-за чего компьютер тормозит. Зависшую программу "
        "можно завершить.",
        "table"),
    Category(
        "disktree", "Анализ диска",
        "Что именно занимает место",
        "analyze",
        "Показывает содержимое домашней папки по убыванию размера: сразу "
        "видно, какая папка разрослась. Ничего не удаляет — только измеряет.",
        "table"),
    Category(
        "bigfiles", "Крупные файлы",
        "Файлы больше 100 МБ",
        "disk",
        "Ищет самые тяжёлые файлы в загрузках, документах и видео. Часто "
        "именно забытые архивы и видеозаписи съедают десятки гигабайт.",
        "table"),
    Category(
        "sysinfo", "Сведения о системе",
        "Оборудование, память, время работы",
        "tools",
        "Сводка о компьютере: версия Windows, процессор, объём памяти, "
        "свободное место и сколько система работает без перезагрузки.",
        "table"),
    Category(
        "network", "Сеть",
        "Соединение, адрес, отклик",
        "globe",
        "Проверяет доступность интернета, показывает локальный адрес, "
        "время отклика и работу DNS. Пригодится, когда сайты не открываются.",
        "table"),
    Category(
        "security", "Центр безопасности",
        "Защитник, брандмауэр, обновления и UAC",
        "security_center",
        "Безопасно читает состояние встроенной защиты Windows, брандмауэра, "
        "Secure Boot, обновлений и автозагрузки. Ничего не включает и не "
        "выключает без вашего участия.",
        "table"),
    Category(
        "health", "Центр состояния",
        "Быстрая проверка важных частей компьютера",
        "health_check",
        "Собирает в одном месте состояние диска, сети, автозагрузки и "
        "доступных ресурсов. Ничего не меняет и даёт понятные рекомендации.",
        "table"),
]


EMPTY_HINTS = {
    "startup": "Вместе с системой ничего лишнего не запускается — "
               "включение компьютера не будет замедляться.",
    "processes": "Список процессов получить не удалось. Попробуйте "
                 "перезапустить программу от имени администратора.",
    "bigfiles": "В загрузках, документах и видео нет файлов тяжелее 100 МБ.",
    "disktree": "Не удалось прочитать домашнюю папку — проверьте права "
                "доступа.",
}

ACTION_W = 132                     # ширина колонки с кнопкой действия
COLUMN_WIDTHS = {                  # 0 — тянущийся столбец, дальше фиксированные
    "startup":   [0, 210],
    "processes": [0, 110, 80],
    "disktree":  [0, 110, 90],
    "bigfiles":  [0, 110, 170],
    "sysinfo":   [0, 420],
    "network":   [0, 420],
    "health":    [0, 150, 360],
    "security":  [0, 165, 390],
}


# ================================================================ плитки
class CategoryCard(GlassCard):
    """Крупная кнопка раздела на главном экране инструментов."""

    opened = Signal(object)

    def __init__(self, cat: Category, parent=None):
        super().__init__(padding=20, spacing=12, hoverable=True, parent=parent)
        self._cat = cat
        self.setCursor(Qt.PointingHandCursor)

        top = QHBoxLayout()
        top.setSpacing(14)
        top.addWidget(OrbIcon(cat.icon, 52, hover=True), 0, Qt.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(4)
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(make_label(cat.name, "CardTitle"))
        title_row.addWidget(HelpDot(cat.hint), 0, Qt.AlignVCenter)
        title_row.addStretch(1)
        col.addLayout(title_row)
        sub = make_label(cat.subtitle, "CardBody")
        sub.setWordWrap(True)
        col.addWidget(sub)
        top.addLayout(col, 1)
        self.body.addLayout(top)

        row = QHBoxLayout()
        self.status = make_label(
            human_count(len(ALL_TOOLS),
                        ("средство", "средства", "средств")) + " очистки"
            if cat.kind == "cleanup" else "Открыть раздел", "Caption")
        row.addWidget(self.status, 1)
        self.btn = QPushButton("Открыть")
        self.btn.setObjectName("Ghost")
        self.btn.setFixedHeight(36)
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(lambda: self.opened.emit(self._cat))
        row.addWidget(self.btn)
        self.body.addLayout(row)

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.opened.emit(self._cat)
        super().mouseReleaseEvent(e)


class ToolCard(GlassCard):
    """Плитка одного средства очистки внутри раздела."""

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
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.addWidget(make_label(tool.name, "CardTitle"))
        if tool.hint:
            title_row.addWidget(HelpDot(tool.hint), 0, Qt.AlignVCenter)
        title_row.addStretch(1)
        col.addLayout(title_row)
        sub = make_label(tool.subtitle, "CardBody")
        sub.setWordWrap(True)
        col.addWidget(sub)
        top.addLayout(col, 1)
        self.body.addLayout(top)

        ok, why = tool.available()
        row = QHBoxLayout()
        self.status = make_label("Готов к проверке" if ok else why, "Caption")
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
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        col.addWidget(title)
        det = make_label(item.detail, "Caption")
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


class TableRow(QWidget):
    """Строка таблицы в инструментах анализа.

    Первый столбец тянется, остальные имеют фиксированную ширину —
    иначе длинные значения наезжают на соседние колонки.
    """

    action = Signal(int)

    def __init__(self, index: int, cells: list[str], widths: list[int],
                 action_text: str = "", header: bool = False,
                 icon_name: str | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("Transparent")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 9 if header else 8, 16, 7 if header else 8)
        lay.setSpacing(14)
        if icon_name is not None:
            if header or not icon_name:
                spacer = QWidget()
                spacer.setObjectName("Transparent")
                spacer.setFixedSize(36, 36)
                lay.addWidget(spacer)
            else:
                lay.addWidget(OrbIcon(icon_name, 36), 0, Qt.AlignVCenter)
        for n, text in enumerate(cells):
            if header:
                role = "CardKicker"
            else:
                role = "CardBody" if n == 0 else "Mono"
            lbl = make_label(text, role)
            if n == 0:
                lbl.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
                lay.addWidget(lbl, 1)
            else:
                w = widths[n] if n < len(widths) else 120
                lbl.setFixedWidth(w)
                right = header or len(text) * 7 < w
                lbl.setAlignment(
                    (Qt.AlignRight if right else Qt.AlignLeft)
                    | Qt.AlignVCenter)
                if not right and not header:
                    fm = lbl.fontMetrics()
                    lbl.setText(fm.elidedText(text, Qt.ElideMiddle, w - 4))
                    lbl.setToolTip(text)
                lay.addWidget(lbl, 0)
        if action_text:
            if header:
                spacer = QWidget()
                spacer.setObjectName("Transparent")
                spacer.setFixedWidth(ACTION_W)
                lay.addWidget(spacer)
            else:
                btn = QPushButton(action_text)
                btn.setObjectName("Ghost")
                btn.setFixedHeight(30)
                btn.setFixedWidth(ACTION_W)
                btn.setCursor(Qt.PointingHandCursor)
                btn.clicked.connect(lambda: self.action.emit(index))
                lay.addWidget(btn, 0, Qt.AlignVCenter)


# ========================================================= окно инструмента
class ToolWindow(QWidget):
    """Окно работы средства очистки: сканирование → список → подтверждение."""

    scanned = Signal(object)
    cleaned_up = Signal(int)

    def __init__(self, tool: Tool, parent=None):
        super().__init__(parent)
        self._tool = tool
        self._result: ScanResult | None = None
        self._rows: list[ResultRow] = []
        self._scan: ScanWorker | None = None
        self._clean: CleanWorker | None = None

        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(820, 660)
        self._drag = None

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

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
        if tool.hint:
            hl.addWidget(HelpDot(tool.hint, 22), 0, Qt.AlignTop)
        hl.addWidget(OrbIcon(tool.icon, 86), 0, Qt.AlignVCenter)
        root.addWidget(hero)

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

        self.prog_box = QWidget()
        self.prog_box.setObjectName("Transparent")
        pl = QVBoxLayout(self.prog_box)
        pl.setContentsMargins(26, 4, 26, 6)
        pl.setSpacing(7)
        row = QHBoxLayout()
        self.prog_label = make_label("Подготовка…", "CardBody")
        self.prog_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        row.addWidget(self.prog_label, 1)
        self.prog_pct = make_label("0%", "MonoAccent")
        row.addWidget(self.prog_pct)
        pl.addLayout(row)
        self.bar = ProgressBar()
        pl.addWidget(self.bar)
        root.addWidget(self.prog_box)

        foot = QWidget()
        foot.setObjectName("Transparent")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(26, 14, 26, 20)
        fl.setSpacing(11)
        self.summary = make_label("", "Caption")
        self.summary.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        fl.addWidget(self.summary, 1)

        self.btn_all = QPushButton("Снять выделение")
        self.btn_all.setObjectName("Link")
        self.btn_all.setCursor(Qt.PointingHandCursor)
        self.btn_all.clicked.connect(self._toggle_all)
        self.btn_all.setVisible(False)
        self.btn_all.setFixedWidth(132)
        fl.addWidget(self.btn_all)

        self.btn_close = QPushButton("Закрыть")
        self.btn_close.setObjectName("Ghost")
        self.btn_close.setFixedSize(96, 42)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.clicked.connect(self.close)
        fl.addWidget(self.btn_close)

        self.btn_go = QPushButton(tool.action)
        self.btn_go.setObjectName("Primary")
        self.btn_go.setFixedSize(180, 42)
        self.btn_go.setCursor(Qt.PointingHandCursor)
        self.btn_go.setEnabled(False)
        self.btn_go.clicked.connect(self._start_clean)
        fl.addWidget(self.btn_go)
        root.addWidget(foot)

        soft_shadow(self, 60, 200, 18)
        QTimer.singleShot(120, self._start_scan)

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
        scr = self.screen()
        if scr:
            g = scr.availableGeometry()
            self.move(g.center().x() - self.width() // 2,
                      g.center().y() - self.height() // 2)

    def _clear_list(self):
        while self.list_lay.count():
            it = self.list_lay.takeAt(0)
            if it.widget():
                it.widget().deleteLater()
        self._rows.clear()

    def _start_scan(self):
        # Полностью нормализуем нижнюю панель при каждом новом сканировании.
        # Иначе после состояния «готово» оставались старые подписи и кнопки.
        self.btn_all.setVisible(False)
        self.btn_close.setText("Закрыть")
        self.btn_go.setVisible(True)
        self.btn_go.setText(self._tool.action)
        self.btn_go.setEnabled(False)
        self.summary.clear()
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
        self._result = res
        self.prog_box.setVisible(False)
        self._clear_list()

        if not res.items:
            msg = make_label(res.note or "Ничего не найдено.", "CardBody")
            msg.setAlignment(Qt.AlignCenter)
            msg.setWordWrap(True)
            self.list_lay.addStretch(1)
            self.list_lay.addWidget(msg)
            self.list_lay.addStretch(1)
            self.summary.setText("Чисто — удалять нечего.")
            self.btn_all.setVisible(False)
            self.btn_go.setVisible(False)
            self.btn_close.setText("Закрыть")
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
        self.btn_close.setText("Закрыть")
        self.btn_go.setVisible(True)
        self.btn_go.setEnabled(True)
        self._refresh_summary()
        self.scanned.emit(res)

    def _admin_banner(self, locked: int) -> QWidget:
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
            "системного мусора не видна. Перезапустите с правами "
            "администратора, чтобы очистить всё.", "CardBody")
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
            "Откроется стандартный запрос Windows.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if ok == QMessageBox.Yes:
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
            self.summary.setText(f"Выбрано всё: {human_size(sel_size)}")
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

    def _start_clean(self):
        res = self._result
        if not res:
            return
        items = [i for i in res.items if i.checked]
        if not items:
            return
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
        self.prog_box.setVisible(False)
        self._clear_list()

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
        self.btn_all.setVisible(False)
        self.btn_close.setText("Закрыть")
        self.cleaned_up.emit(freed)

    def _rescan(self):
        self.btn_go.clicked.disconnect()
        self.btn_go.clicked.connect(self._start_clean)
        self._clear_list()
        self._start_scan()

    def _on_failed(self, msg: str):
        self.prog_box.setVisible(False)
        self._clear_list()
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


# ============================================================== вкладки
class SubPage(QScrollArea):
    """Вложенная вкладка со стрелкой «назад» в заголовке."""

    back = Signal()

    def __init__(self, cat: Category, parent=None):
        super().__init__(parent)
        self.cat = cat
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        host = QWidget()
        host.setObjectName("Transparent")
        self.body = QVBoxLayout(host)
        self.body.setContentsMargins(32, 22, 32, 32)
        self.body.setSpacing(18)
        self.setWidget(host)

        head = QWidget()
        head.setObjectName("Transparent")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(12)
        btn_back = IconButton("chevron_left", 38, 19, tooltip="Назад к инструментам")
        btn_back.clicked.connect(self.back.emit)
        hl.addWidget(btn_back, 0, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(3)
        title_row = QHBoxLayout()
        title_row.setSpacing(9)
        title_row.addWidget(make_label(cat.name, "PageTitle"))
        title_row.addWidget(HelpDot(cat.hint, 21), 0, Qt.AlignVCenter)
        title_row.addStretch(1)
        col.addLayout(title_row)
        col.addWidget(make_label(cat.subtitle, "PageSub"))
        hl.addLayout(col, 1)
        hl.addWidget(OrbIcon(cat.icon, 46), 0, Qt.AlignVCenter)
        self.body.addWidget(head)


class CleanupPage(SubPage):
    """Вкладка «Очистка диска»: шесть средств и сводка по дискам."""

    def __init__(self, parent=None):
        super().__init__(
            next(c for c in CATEGORIES if c.key == "cleanup"), parent)
        self._win: ToolWindow | None = None

        self._disk_slot = QVBoxLayout()
        self._disk_slot.setContentsMargins(0, 0, 0, 0)
        self._disk_card = None
        self.body.addLayout(self._disk_slot)
        self.refresh_disk()

        self.body.addWidget(make_label("СРЕДСТВА ОЧИСТКИ", "SectionLabel"))
        grid = QVBoxLayout()
        grid.setSpacing(14)
        pair = None
        self.cards: list[ToolCard] = []
        for n, tool in enumerate(ALL_TOOLS):
            if n % 2 == 0:
                pair = QHBoxLayout()
                pair.setSpacing(14)
                grid.addLayout(pair)
            card = ToolCard(tool)
            card.launched.connect(self.open_tool)
            pair.addWidget(card, 1)
            self.cards.append(card)
        if len(ALL_TOOLS) % 2:
            placeholder = QWidget()
            placeholder.setObjectName("Transparent")
            pair.addWidget(placeholder, 1)
        self.body.addLayout(grid)
        self.body.addStretch(1)

    def refresh_disk(self):
        if self._disk_card is not None:
            self._disk_card.setParent(None)
            self._disk_card.deleteLater()
            self._disk_card = None
        disks = disk_usage()
        if not disks:
            return
        card = GlassCard(padding=20, spacing=14, hoverable=False)
        top = QHBoxLayout()
        top.setSpacing(14)
        top.addWidget(OrbIcon("disk", 44), 0, Qt.AlignVCenter)
        c3 = QVBoxLayout()
        c3.setSpacing(2)
        c3.addWidget(make_label("МЕСТО НА ДИСКЕ", "CardKicker"))
        free_all = sum(t - u for _l, u, t in disks)
        c3.addWidget(make_label(f"Свободно {human_size(free_all)}", "CardTitle"))
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
            row.addWidget(make_label(f"{human_size(total - used)} свободно",
                                     "Mono"))
            card.body.addLayout(row)
        self._disk_slot.addWidget(card)
        self._disk_card = card

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


class TablePage(SubPage):
    """Вкладка инструмента анализа: таблица с данными."""

    def __init__(self, cat: Category, parent=None):
        super().__init__(cat, parent)
        self._worker: SystemWorker | None = None
        self._result: TableResult | None = None

        bar_row = QHBoxLayout()
        bar_row.setSpacing(12)
        self.summary = make_label("Загрузка данных…", "Caption")
        self.summary.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        bar_row.addWidget(self.summary, 1)
        self.btn_reload = QPushButton("Обновить")
        self.btn_reload.setObjectName("Ghost")
        self.btn_reload.setFixedHeight(36)
        self.btn_reload.setCursor(Qt.PointingHandCursor)
        self.btn_reload.clicked.connect(self.reload)
        bar_row.addWidget(self.btn_reload)
        self.body.addLayout(bar_row)

        self.bar = ProgressBar()
        self.bar.setFixedHeight(8)
        self.body.addWidget(self.bar)

        self._slot = QVBoxLayout()
        self._slot.setSpacing(12)
        self.body.addLayout(self._slot)
        self.body.addStretch(1)
        QTimer.singleShot(150, self.reload)

    def reload(self):
        if self._worker and self._worker.isRunning():
            return
        self.btn_reload.setEnabled(False)
        self.bar.setVisible(True)
        self.bar.setValue(0)
        self.summary.setText("Сбор данных…")
        self._worker = SystemWorker(self.cat.key, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.done.connect(self._on_done)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_progress(self, pct: int, text: str):
        self.bar.setValue(pct)
        self.summary.setText(text)

    def _clear(self):
        while self._slot.count():
            it = self._slot.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def _on_done(self, res: TableResult):
        self._result = res
        self.bar.setVisible(False)
        self.btn_reload.setEnabled(True)
        self._clear()
        self.summary.setText(res.note or f"Строк: {len(res.rows)}")

        if not res.rows:
            self.summary.setText("Проверка завершена")
            card = GlassCard(padding=26, spacing=12, hoverable=False)
            row = QHBoxLayout()
            row.setSpacing(16)
            row.addWidget(OrbIcon("done", 56), 0, Qt.AlignVCenter)
            col = QVBoxLayout()
            col.setSpacing(4)
            col.addWidget(make_label("ВСЁ ЧИСТО", "CardKicker"))
            col.addWidget(make_label(res.note or "Данных нет.", "CardTitle"))
            tail = make_label(EMPTY_HINTS.get(
                self.cat.key, "Ничего делать не нужно."), "CardBody")
            tail.setWordWrap(True)
            col.addWidget(tail)
            row.addLayout(col, 1)
            card.body.addLayout(row)
            self._slot.addWidget(card)
            return

        action = {"startup": "Отключить", "processes": "Завершить"}.get(
            self.cat.key, "")
        widths = COLUMN_WIDTHS.get(self.cat.key, [0, 130, 200])
        card = GlassCard(padding=6, spacing=0, hoverable=False)
        security_icons = {
            "Защитник Windows": "defender", "Базы угроз": "threat_scan",
            "Брандмауэр": "firewall", "Контроль учётных записей": "uac",
            "Безопасная загрузка": "secure_boot",
            "Центр обновления": "windows_update",
            "Автозагрузка": "startup_guard", "История угроз": "threat_scan",
            "Защита репутации": "privacy",
        }
        icon_slot = "" if self.cat.key == "security" else None
        card.body.addWidget(TableRow(
            -1, [h.upper() for h in res.headers], widths, action, header=True,
            icon_name=icon_slot))
        for i, cells in enumerate(res.rows):
            row = TableRow(i, cells, widths, action,
                           icon_name=(security_icons.get(cells[0], "shield")
                                      if self.cat.key == "security" else None))
            row.action.connect(self._row_action)
            card.body.addWidget(row)
        self._slot.addWidget(card)

    def _row_action(self, index: int):
        res = self._result
        if not res or index >= len(res.payload):
            return
        obj = res.payload[index]
        if self.cat.key == "startup":
            ok = QMessageBox.question(
                self, "Автозагрузка",
                f"Убрать «{obj.name}» из автозагрузки?\n\n"
                f"Программа перестанет запускаться вместе с системой. "
                f"Сам файл не удаляется.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ok != QMessageBox.Yes:
                return
            done, msg = disable_startup(obj)
        elif self.cat.key == "processes":
            ok = QMessageBox.question(
                self, "Завершение процесса",
                f"Завершить «{obj.name}» (PID {obj.pid})?\n\n"
                f"Несохранённые данные программы будут потеряны.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if ok != QMessageBox.Yes:
                return
            done, msg = kill_process(obj.pid)
        else:
            return
        QMessageBox.information(
            self, "Готово" if done else "Не получилось", msg)
        if done:
            self.reload()

    def _on_failed(self, msg: str):
        self.bar.setVisible(False)
        self.btn_reload.setEnabled(True)
        self.summary.setText(f"Не удалось получить данные: {msg}")

    def stop_worker(self):
        """Корректно завершить фоновый сбор данных перед закрытием."""
        w = self._worker
        if w is None:
            return
        if w.isRunning():
            w.requestInterruption()
            if not w.wait(3000):
                w.terminate()
                w.wait(1000)
        w.setParent(None)
        self._worker = None

    def closeEvent(self, e):
        self.stop_worker()
        super().closeEvent(e)


# ================================================================ страница
class ToolsPage(QStackedWidget):
    """Раздел «Инструменты»: список категорий и вложенные вкладки."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pages: dict[str, QWidget] = {}
        self.home = _ToolsHome()
        self.home.opened.connect(self.open_category)
        self.addWidget(self.home)
        # страница живёт внутри стека и closeEvent не получает,
        # поэтому потоки останавливаем при выходе из программы
        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.stop_all)

    def open_key(self, key: str):
        cat = next((item for item in CATEGORIES if item.key == key), None)
        if cat is not None:
            self.open_category(cat)

    def open_category(self, cat: Category):
        page = self._pages.get(cat.key)
        if page is None:
            page = CleanupPage() if cat.kind == "cleanup" else TablePage(cat)
            page.back.connect(self.go_home)
            self._pages[cat.key] = page
            self.addWidget(page)
        elif isinstance(page, TablePage):
            page.reload()
        self.setCurrentWidget(page)

    def go_home(self):
        self.setCurrentWidget(self.home)

    def refresh_disk(self):
        page = self._pages.get("cleanup")
        if isinstance(page, CleanupPage):
            page.refresh_disk()

    def stop_all(self):
        """Остановить фоновые задачи всех открытых вкладок."""
        for page in self._pages.values():
            if isinstance(page, TablePage):
                page.stop_worker()
            elif isinstance(page, CleanupPage) and page._win is not None:
                page._win.close()

    def closeEvent(self, e):
        self.stop_all()
        super().closeEvent(e)


class _ToolsHome(QScrollArea):
    """Первый экран раздела: крупные кнопки категорий."""

    opened = Signal(object)

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

        head = QWidget()
        head.setObjectName("Transparent")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(0, 0, 0, 0)
        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(make_label("Инструменты", "PageTitle"))
        col.addWidget(make_label(
            "Обслуживание и диагностика · наведите на «?» для пояснения",
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
        c2.addWidget(make_label("Порядок на компьютере", "HeroTitle"))
        sub = make_label(
            "Освободите место, посмотрите, что тормозит запуск, "
            "и проверьте состояние системы.", "CardBody")
        sub.setWordWrap(True)
        c2.addWidget(sub)
        ll.addLayout(c2, 1)
        ll.addWidget(OrbIcon("broom", 92), 0, Qt.AlignVCenter)
        self.body.addWidget(hero)

        self.body.addWidget(make_label("РАЗДЕЛЫ", "SectionLabel"))
        grid = QVBoxLayout()
        grid.setSpacing(14)
        pair = None
        for n, cat in enumerate(CATEGORIES):
            if n % 2 == 0:
                pair = QHBoxLayout()
                pair.setSpacing(14)
                grid.addLayout(pair)
            card = CategoryCard(cat)
            card.opened.connect(self.opened.emit)
            pair.addWidget(card, 1)
        if len(CATEGORIES) % 2:
            # Пустая половина сохраняет одинаковую ширину последней карточки.
            # addStretch() оставлял «Сеть» шириной по sizeHint.
            placeholder = QWidget()
            placeholder.setObjectName("Transparent")
            pair.addWidget(placeholder, 1)
        self.body.addLayout(grid)
        self.body.addStretch(1)
