"""LIFE OS — экран пользовательского соглашения.

Используется в двух режимах:
  * первый запуск — модальное окно с кнопкой «Принимаю» (обязательное);
  * из раздела «О программе» — режим просмотра с кнопкой «Закрыть».
"""
from __future__ import annotations

import json

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QPushButton, QScrollArea,
    QVBoxLayout, QWidget,
)

from . import config as cfg
from . import icons
from .settings import settings
from .theme import current_accent
from .widgets import Divider, LogoOrb, make_label, soft_shadow


def _load() -> dict:
    try:
        return json.loads((cfg.DATA / "eula.json").read_text("utf-8"))
    except (OSError, ValueError):
        return {"title": "Пользовательское соглашение", "sections": []}


class EulaWindow(QWidget):
    accepted = Signal()
    declined = Signal()

    def __init__(self, first_run: bool = False, parent=None):
        super().__init__(parent)
        self._first_run = first_run
        self._drag = None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowModality(Qt.ApplicationModal)
        self.resize(860, 660)
        self.setMinimumSize(640, 480)

        data = _load()

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---------------- шапка ----------------
        head = QWidget()
        head.setObjectName("Transparent")
        hl = QHBoxLayout(head)
        hl.setContentsMargins(30, 26, 26, 18)
        hl.setSpacing(16)
        hl.addWidget(LogoOrb(size=54, breathe=False), 0, Qt.AlignTop)
        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(make_label(data.get("title", ""), "PageTitle"))
        col.addWidget(make_label(data.get("subtitle", ""), "PageSub"))
        hl.addLayout(col, 1)
        if not first_run:
            close = QPushButton("")
            close.setObjectName("WinBtn")
            close.setFixedSize(34, 34)
            close.setCursor(Qt.PointingHandCursor)
            close.setIcon(icons.icon("close", 16, "#9DABC2"))
            close.clicked.connect(self.close)
            hl.addWidget(close, 0, Qt.AlignTop)
        root.addWidget(head)

        line = Divider()
        line.setContentsMargins(0, 0, 0, 0)
        root.addWidget(line)

        # ---------------- текст ----------------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        host = QWidget()
        host.setObjectName("Transparent")
        body = QVBoxLayout(host)
        body.setContentsMargins(30, 22, 30, 24)
        body.setSpacing(16)

        intro = make_label(data.get("intro", ""), "Legal", wrap=True)
        body.addWidget(intro)

        for sec in data.get("sections", []):
            block = QWidget()
            block.setObjectName("Transparent")
            bl = QVBoxLayout(block)
            bl.setContentsMargins(0, 0, 0, 0)
            bl.setSpacing(6)
            head_row = QHBoxLayout()
            head_row.setSpacing(10)
            num = make_label(sec.get("n", ""), "MonoAccent")
            num.setFixedWidth(20)
            head_row.addWidget(num, 0, Qt.AlignTop)
            head_row.addWidget(make_label(sec.get("title", ""), "LegalTitle"), 1)
            bl.addLayout(head_row)
            text = make_label(sec.get("text", ""), "Legal", wrap=True)
            text.setContentsMargins(30, 0, 0, 0)
            bl.addWidget(text)
            body.addWidget(block)

        body.addSpacing(6)
        body.addWidget(make_label(data.get("footer", ""), "Caption"))
        body.addStretch(1)
        scroll.setWidget(host)
        root.addWidget(scroll, 1)

        root.addWidget(Divider())

        # ---------------- кнопки ----------------
        foot = QWidget()
        foot.setObjectName("Transparent")
        fl = QHBoxLayout(foot)
        fl.setContentsMargins(30, 18, 26, 22)
        fl.setSpacing(12)
        if first_run:
            fl.addWidget(make_label(
                "Продолжая, вы подтверждаете согласие с условиями.", "Caption"), 1)
            decline = QPushButton("Отказаться")
            decline.setObjectName("Ghost")
            decline.setFixedHeight(42)
            decline.setCursor(Qt.PointingHandCursor)
            decline.clicked.connect(self._decline)
            accept = QPushButton("Принимаю")
            accept.setObjectName("Primary")
            accept.setFixedHeight(42)
            accept.setMinimumWidth(170)
            accept.setCursor(Qt.PointingHandCursor)
            accept.clicked.connect(self._accept)
            fl.addWidget(decline)
            fl.addWidget(accept)
        else:
            fl.addWidget(make_label(
                f"Редакция от {cfg.DEV_YEAR} · {cfg.DEV_NAME}", "Caption"), 1)
            ok = QPushButton("Закрыть")
            ok.setObjectName("Primary")
            ok.setFixedHeight(42)
            ok.setMinimumWidth(150)
            ok.setCursor(Qt.PointingHandCursor)
            ok.clicked.connect(self.close)
            fl.addWidget(ok)
        root.addWidget(foot)
        soft_shadow(self, 60, 200, 18)

    # ------------------------------------------------------------- события
    def _accept(self):
        settings.set("eula_accepted", True)
        settings.set("eula_version", cfg.APP_VERSION)
        self.accepted.emit()
        self.close()

    def _decline(self):
        self.declined.emit()
        self.close()

    def closeEvent(self, e):
        if self._first_run and not settings.get("eula_accepted"):
            self.declined.emit()
        super().closeEvent(e)

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton and e.position().y() < 90:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(e)

    def mouseMoveEvent(self, e):
        if self._drag and e.buttons() & Qt.LeftButton:
            self.move(e.globalPosition().toPoint() - self._drag)
        super().mouseMoveEvent(e)

    def mouseReleaseEvent(self, e):
        self._drag = None
        super().mouseReleaseEvent(e)

    def center_on_screen(self):
        scr = self.screen().availableGeometry()
        self.move(scr.center().x() - self.width() // 2,
                  scr.center().y() - self.height() // 2)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        rad = settings.get("corner_radius") + 4
        r = QRectF(self.rect())
        path = QPainterPath()
        path.addRoundedRect(r, rad, rad)
        p.setClipPath(path)
        p.fillRect(self.rect(), QColor(7, 10, 18, 252))
        # Цвет рамки берём при каждой отрисовке: акцент меняется в настройках.
        edge = QColor(current_accent().primary)
        edge.setAlpha(70)
        p.setClipping(False)
        p.setBrush(Qt.NoBrush)
        from PySide6.QtGui import QPen
        p.setPen(QPen(edge, 1))
        p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), rad, rad)
        p.end()
