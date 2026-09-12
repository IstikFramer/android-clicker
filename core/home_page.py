"""Home page with release notes and a compact system overview."""

from __future__ import annotations

import logging
import platform
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

try:
    import psutil
except ImportError:  # pragma: no cover - dependency is installed in normal use
    psutil = None  # type: ignore[assignment]

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.app import APP_VERSION
from core.fluent import PrimaryPushButton, SmoothScrollArea
from core.glass import GlassCard
from core.theme import Sizes
from core.utils import format_bytes, get_user_name


class HomePage(QWidget):
    """Welcome page shown when the application starts."""

    def __init__(
        self,
        parent: QWidget | None = None,
        open_plugin: Callable[[int], None] | None = None,
    ) -> None:
        """Create the home page and populate its static content."""
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self._open_plugin = open_plugin
        self._module_grid: QGridLayout | None = None
        self._module_empty_label: QLabel | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the scrollable welcome page."""
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = SmoothScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("homeContent")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(Sizes.CONTENT_MARGIN, 24, Sizes.CONTENT_MARGIN, 30)
        content_layout.setSpacing(Sizes.CONTENT_SPACING)

        welcome = QVBoxLayout()
        welcome.setSpacing(4)
        title = QLabel(f"Добро пожаловать, {get_user_name()}", content)
        title.setProperty("role", "welcome-title")
        subtitle = QLabel(self._current_date(), content)
        subtitle.setProperty("role", "muted")
        welcome.addWidget(title)
        welcome.addWidget(subtitle)
        content_layout.addLayout(welcome)

        content_layout.addWidget(self._create_update_card())
        content_layout.addLayout(self._create_system_cards())

        modules_title = QLabel("Установленные модули", content)
        modules_title.setProperty("role", "section-title")
        content_layout.addWidget(modules_title)
        module_container = QWidget(content)
        module_layout = QVBoxLayout(module_container)
        module_layout.setContentsMargins(0, 0, 0, 0)
        module_layout.setSpacing(12)
        self._module_empty_label = QLabel(
            "Модули не установлены. Новые модули появятся в следующих обновлениях.",
            module_container,
        )
        self._module_empty_label.setProperty("role", "muted")
        self._module_empty_label.setWordWrap(True)
        module_layout.addWidget(self._module_empty_label)
        self._module_grid = QGridLayout()
        self._module_grid.setContentsMargins(0, 0, 0, 0)
        self._module_grid.setHorizontalSpacing(12)
        self._module_grid.setVerticalSpacing(12)
        module_layout.addLayout(self._module_grid)
        content_layout.addWidget(module_container)
        content_layout.addStretch(1)

        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

    @staticmethod
    def _current_date() -> str:
        """Format today's date using Russian month and weekday names."""
        date = datetime.now()
        months = (
            "января",
            "февраля",
            "марта",
            "апреля",
            "мая",
            "июня",
            "июля",
            "августа",
            "сентября",
            "октября",
            "ноября",
            "декабря",
        )
        weekdays = (
            "понедельник",
            "вторник",
            "среда",
            "четверг",
            "пятница",
            "суббота",
            "воскресенье",
        )
        return f"{date.day} {months[date.month - 1]} {date.year}, {weekdays[date.weekday()]}"

    def _create_update_card(self) -> QFrame:
        """Create the release note card for version 0.1.4."""
        card = GlassCard(frame_role="large-card")
        card.setMinimumHeight(270)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        accent_bar = QFrame(card)
        accent_bar.setObjectName("updateAccentBar")
        accent_bar.setFixedHeight(3)
        layout.addWidget(accent_bar)
        content = QWidget(card)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 18, 24, 22)
        content_layout.setSpacing(5)

        title = QLabel(f"Обновление v{APP_VERSION} — Новый визуальный стиль", content)
        title.setProperty("role", "card-title")
        subtitle = QLabel("Сентябрь 2026", content)
        subtitle.setProperty("role", "muted")
        text = QLabel(
            "Интерфейс полностью переработан.\n\n"
            "Что изменилось:\n"
            "-- Эффект прозрачности Mica (Windows 11)\n"
            "-- Стеклянные карточки и панели\n"
            "-- Плавные анимации переходов\n"
            "-- Обновлённые элементы управления в стиле Fluent Design\n"
            "-- Улучшенная боковая панель\n\n"
            "Следующее обновление:\n"
            "-- v0.1.5 — Файловый менеджмент",
            content,
        )
        text.setProperty("role", "update-text")
        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        content_layout.addWidget(title)
        content_layout.addWidget(subtitle)
        content_layout.addSpacing(9)
        content_layout.addWidget(text)
        layout.addWidget(content)

        return card

    def _create_system_cards(self) -> QHBoxLayout:
        """Create four equal-width cards with current system information."""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        system, release, machine = platform.system() or "Система", platform.release(), platform.machine()
        processor = platform.processor() or "Модель не определена"
        processor = processor.strip() or "Модель не определена"
        if len(processor) > 32:
            processor = f"{processor[:29]}..."
        logical_cores = "Не определено"
        memory_total, memory_percent = 0, 0
        disk_total, disk_free = 0, 0
        if psutil is not None:
            try:
                logical_cores = str(psutil.cpu_count(logical=True) or "Не определено")
                memory = psutil.virtual_memory()
                memory_total, memory_percent = memory.total, memory.percent
                disk_root = Path.home().anchor or str(Path.home())
                disk = psutil.disk_usage(disk_root)
                disk_total, disk_free = disk.total, disk.free
            except (OSError, RuntimeError, ValueError) as error:
                self._logger.warning("Could not collect system information: %s", error)
        cards = (
            ("Система", f"{system} {release}".strip(), machine or "Архитектура не определена"),
            ("Процессор", processor, f"{logical_cores} ядер"),
            ("Память", format_bytes(memory_total), f"Используется: {memory_percent:.0f}%"),
            ("Диск", format_bytes(disk_total), f"Свободно: {format_bytes(disk_free)}"),
        )
        for label, value, detail in cards:
            card = self._create_stat_card(label, value, detail)
            layout.addWidget(card, 1)
        return layout

    def _create_stat_card(self, label: str, value: str, detail: str) -> QFrame:
        """Create one system statistic card."""
        card = GlassCard()
        card.setMinimumHeight(90)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 13, 16, 13)
        layout.setSpacing(4)
        label_widget = QLabel(label, card)
        label_widget.setProperty("role", "muted")
        value_widget = QLabel(value, card)
        value_widget.setProperty("role", "stat-value")
        value_widget.setToolTip(value)
        detail_widget = QLabel(detail, card)
        detail_widget.setProperty("role", "muted")
        detail_widget.setWordWrap(True)
        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        layout.addWidget(detail_widget)
        return card

    def set_modules(self, modules: list[dict[str, Any]]) -> None:
        """Refresh the installed module cards.

        Args:
            modules: Plugin metadata dictionaries with ``name``, ``description``
                and ``page_index`` keys.
        """
        if self._module_grid is None or self._module_empty_label is None:
            return
        while self._module_grid.count():
            item = self._module_grid.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._module_empty_label.setVisible(not modules)
        for position, module in enumerate(modules):
            card = self._create_module_card(module)
            self._module_grid.addWidget(card, position // 2, position % 2)

    def _create_module_card(self, module: dict[str, Any]) -> QFrame:
        """Create a card for one dynamically loaded module."""
        card = GlassCard()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(7)
        title = QLabel(str(module.get("name", "Модуль")), card)
        title.setProperty("role", "card-title")
        description = QLabel(str(module.get("description", "")), card)
        description.setProperty("role", "muted")
        description.setWordWrap(True)
        button = PrimaryPushButton("Открыть", card)
        button.setProperty("variant", "primary")
        button.setFixedWidth(104)
        page_index = module.get("page_index")
        if isinstance(page_index, int) and self._open_plugin is not None:
            button.clicked.connect(lambda: self._open_plugin(page_index))
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addStretch(1)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
        return card
