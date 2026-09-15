"""LIFE OS — интерфейс обновления: окно релиза, прогресс загрузки, плашка."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QDesktopServices, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QSizePolicy,
    QApplication, QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from . import config as cfg
from . import icons
from .anim import Spring, driver
from .settings import settings
from .theme import current_accent
from .updater import InstallWorker, UpdateInfo, restart_app
from .widgets import (
    Divider, GlassCard, GlowAware, ImagePanel, OrbIcon, make_label, soft_shadow,
)

TYPE_TITLES = {
    "added": "Добавлено",
    "improved": "Улучшено",
    "fixed": "Исправлено",
}


class ProgressBar(GlowAware, QWidget):
    """Полоса загрузки с плавным подтягиванием значения."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(8)
        self._v = Spring(0.0, 10.0)
        self._indeterminate = False
        self._phase = 0.0
        driver().subscribe(self, self._tick)

    def setValue(self, v: float):
        self._indeterminate = False
        self._v.set(max(0.0, min(100.0, v)))

    def setIndeterminate(self, on: bool):
        self._indeterminate = on

    def _tick(self, dt: float):
        moved = not self._v.done
        if moved:
            self._v.step(dt)
        if self._indeterminate:
            self._phase = (self._phase + dt * 0.8) % 1.0
            moved = True
        if moved:
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        acc = current_accent()
        r = QRectF(0, 1, self.width(), self.height() - 2)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 255, 26))
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)

        from PySide6.QtGui import QLinearGradient
        if self._indeterminate:
            w = r.width() * 0.3
            x = (r.width() + w) * self._phase - w
            fill = QRectF(max(0, x), r.top(), min(w, r.width() - max(0, x)), r.height())
        else:
            fill = QRectF(r)
            fill.setWidth(max(0.0, r.width() * self._v.value / 100.0))
        if fill.width() <= 0.5:
            p.end()
            return
        g = QLinearGradient(fill.left(), 0, fill.right(), 0)
        g.setColorAt(0.0, QColor(acc.primary))
        g.setColorAt(1.0, QColor(acc.secondary))
        if settings.glow_alpha > 0.05:
            halo = QColor(acc.primary)
            halo.setAlphaF(min(0.4, 0.3 * settings.glow_alpha))
            p.setBrush(halo)
            p.drawRoundedRect(fill.adjusted(-1, -2.5, 1, 2.5), 6, 6)
        p.setBrush(g)
        p.drawRoundedRect(fill, fill.height() / 2, fill.height() / 2)
        p.end()


# ===========================================================================
class UpdateWindow(QWidget):
    """Окно новой версии: описание релиза, загрузка, установка."""

    installed = Signal()

    def __init__(self, info: UpdateInfo, parent=None):
        super().__init__(parent)
        self._info = info
        self._worker: InstallWorker | None = None
        self._drag = None
        self._backup = ""

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(780, 640)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # -------- шапка с артом --------
        hero = ImagePanel(cfg.BACKGROUNDS / "update_hero.jpg", overlay=0.62,
                          radius=settings.get("corner_radius") + 4)
        hero.setFixedHeight(168)
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(30, 22, 26, 22)
        hl.setSpacing(20)
        col = QVBoxLayout()
        col.setSpacing(6)
        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(make_label("ДОСТУПНО ОБНОВЛЕНИЕ", "CardKicker"))
        top.addStretch(1)
        col.addLayout(top)
        col.addWidget(make_label(info.title or f"Версия {info.version}", "HeroTitle"))
        col.addWidget(make_label(
            f"Установлена {cfg.APP_VERSION}   →   Новая {info.version}", "Mono"))
        col.addStretch(1)
        hl.addLayout(col, 1)
        hl.addWidget(OrbIcon("update", 86), 0, Qt.AlignVCenter)
        root.addWidget(hero)

        # -------- содержимое --------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget()
        host.setObjectName("Transparent")
        body = QVBoxLayout(host)
        body.setContentsMargins(28, 20, 28, 20)
        body.setSpacing(14)

        if info.notes and not info.changes:
            body.addWidget(make_label("Что изменилось", "CardTitle"))
            body.addWidget(make_label(info.notes, "CardBody", wrap=True))
        else:
            grouped: dict[str, list[str]] = {}
            for c in info.changes:
                grouped.setdefault(c.get("type", "added"), []).append(c.get("text", ""))
            for key in ("added", "improved", "fixed"):
                items = grouped.get(key)
                if not items:
                    continue
                card = GlassCard(padding=16, spacing=8, hoverable=False)
                head = QHBoxLayout()
                head.setSpacing(9)
                head.addWidget(make_label(TYPE_TITLES[key].upper(), "CardKicker"))
                head.addStretch(1)
                head.addWidget(make_label(str(len(items)), "BadgeMuted"))
                card.body.addLayout(head)
                for text in items:
                    row = QHBoxLayout()
                    row.setSpacing(9)
                    dot = QLabel("•")
                    dot.setObjectName("MonoAccent")
                    dot.setFixedWidth(9)
                    row.addWidget(dot, 0, Qt.AlignTop)
                    row.addWidget(make_label(text, "CardBody", wrap=True), 1)
                    card.body.addLayout(row)
                body.addWidget(card)

        info_row = QHBoxLayout()
        info_row.setSpacing(16)
        src = "Релиз GitHub" if info.source == "release" else "Ветка репозитория"
        for k, v in (("Источник", src), ("Дата", info.published or "—"),
                     ("Размер", f"{info.size / 1048576:.1f} МБ" if info.size else "—")):
            c = QVBoxLayout()
            c.setSpacing(1)
            c.addWidget(make_label(k, "Caption"))
            c.addWidget(make_label(v, "CardTitle"))
            info_row.addLayout(c)
        info_row.addStretch(1)
        body.addLayout(info_row)
        body.addStretch(1)
        scroll.setWidget(host)
        root.addWidget(scroll, 1)
        root.addWidget(Divider())

        # -------- прогресс --------
        self.prog_box = QWidget()
        self.prog_box.setObjectName("Transparent")
        pl = QVBoxLayout(self.prog_box)
        pl.setContentsMargins(28, 14, 28, 0)
        pl.setSpacing(7)
        self.prog_label = make_label("Подготовка…", "CardBody")
        row = QHBoxLayout()
        row.addWidget(self.prog_label, 1)
        self.prog_pct = make_label("0%", "MonoAccent")
        row.addWidget(self.prog_pct)
        pl.addLayout(row)
        self.bar = ProgressBar()
        pl.addWidget(self.bar)
        self.prog_box.setVisible(False)
        root.addWidget(self.prog_box)

        # -------- кнопки --------
        foot = QWidget()
        foot.setObjectName("Transparent")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(28, 16, 26, 20)
        fl.setSpacing(11)
        self.hint = make_label("Сохраним резервную копию текущей версии.", "Caption")
        self.hint.setWordWrap(False)
        self.hint.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        fl.addWidget(self.hint, 1)

        self.btn_web = QPushButton("Открыть на GitHub")
        self.btn_web.setObjectName("Link")
        self.btn_web.setCursor(Qt.PointingHandCursor)
        self.btn_web.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(self._info.page)))
        fl.addWidget(self.btn_web)

        self.btn_later = QPushButton("Позже")
        self.btn_later.setObjectName("Ghost")
        self.btn_later.setFixedHeight(42)
        self.btn_later.setCursor(Qt.PointingHandCursor)
        self.btn_later.clicked.connect(self.close)
        fl.addWidget(self.btn_later)

        self.btn_install = QPushButton("Установить")
        self.btn_install.setObjectName("Primary")
        self.btn_install.setFixedHeight(42)
        self.btn_install.setMinimumWidth(170)
        self.btn_install.setCursor(Qt.PointingHandCursor)
        self.btn_install.clicked.connect(self._start)
        fl.addWidget(self.btn_install)
        root.addWidget(foot)

        soft_shadow(self, 60, 200, 18)

    # ------------------------------------------------------------- установка
    def _start(self):
        self.btn_install.setEnabled(False)
        self.btn_install.setText("Установка…")
        self.btn_later.setText("Отмена")
        self.btn_later.clicked.disconnect()
        self.btn_later.clicked.connect(self._cancel)
        self.prog_box.setVisible(True)
        self.hint.setText("Не закрывайте программу.")

        self._worker = InstallWorker(self._info, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_ok.connect(self._on_ok)
        self._worker.failed.connect(self._on_fail)
        self._worker.start()

    def _cancel(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
        else:
            self.close()

    def _on_progress(self, pct: int, text: str):
        self.bar.setValue(pct)
        self.prog_pct.setText(f"{pct}%")
        self.prog_label.setText(text)

    def _on_ok(self, backup: str):
        self._backup = backup
        self.bar.setValue(100)
        self.prog_pct.setText("100%")
        self.prog_label.setText("Обновление установлено")
        self.hint.setText(f"Резервная копия: {Path(backup).name}")
        self.btn_later.setText("Позже")
        self.btn_later.clicked.disconnect()
        self.btn_later.clicked.connect(self.close)
        self.btn_install.setText("Перезапустить")
        self.btn_install.setEnabled(True)
        self.btn_install.clicked.disconnect()
        self.btn_install.clicked.connect(restart_app)
        self.installed.emit()

    def _on_fail(self, message: str):
        self.prog_label.setText(message)
        self.prog_pct.setText("—")
        self.bar.setValue(0)
        self.hint.setText("Можно скачать обновление вручную на GitHub.")
        self.btn_install.setEnabled(True)
        self.btn_install.setText("Повторить")
        self.btn_later.setText("Закрыть")
        self.btn_later.clicked.disconnect()
        self.btn_later.clicked.connect(self.close)

    # ---------------------------------------------------------------- окно
    def center_on_screen(self):
        scr = self.screen().availableGeometry()
        self.move(scr.center().x() - self.width() // 2,
                  scr.center().y() - self.height() // 2)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.position().y() < 168:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag = None
        super().mouseReleaseEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rad = settings.get("corner_radius") + 4
        r = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(r, rad, rad)
        p.setClipPath(path)
        p.fillRect(self.rect(), QColor(7, 10, 18, 252))
        p.setClipping(False)
        edge = QColor(current_accent().primary)
        edge.setAlpha(70)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(edge, 1))
        p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), rad, rad)
        p.end()


# ===========================================================================
class UpdateBanner(GlassCard):
    """Плашка на главном экране: «доступна новая версия»."""

    clicked = Signal()

    def __init__(self, info: UpdateInfo, parent=None):
        super().__init__(parent, hoverable=True, padding=16, spacing=0)
        self.setCursor(Qt.PointingHandCursor)
        row = QHBoxLayout()
        row.setSpacing(14)
        row.addWidget(OrbIcon("download", 42), 0, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(make_label(
            f"Доступна версия {info.version}", "CardTitle"))
        col.addWidget(make_label(
            info.title or "Нажмите, чтобы посмотреть изменения и установить.",
            "Caption"))
        row.addLayout(col, 1)
        btn = QPushButton("Обновить")
        btn.setObjectName("Primary")
        btn.setFixedHeight(38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self.clicked.emit)
        row.addWidget(btn, 0, Qt.AlignVCenter)
        self.body.addLayout(row)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)
