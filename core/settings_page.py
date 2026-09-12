"""Application settings page."""

from __future__ import annotations

import logging
import platform
import sys
from typing import Any, Callable

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import Qt, QSignalBlocker, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget,
    QGraphicsDropShadowEffect,
)

from core.app import APP_DEVELOPER, APP_NAME, APP_VERSION
from core.config import ConfigManager
from core.fluent import CheckBox, ComboBox, PrimaryPushButton, PushButton, Slider, SmoothScrollArea
from core.theme import Sizes, shadow_color


class SettingsPage(QWidget):
    """Scrollable page for general, visual and update preferences."""

    status_message = Signal(str)
    effects_changed = Signal(str, int)

    def __init__(self, config: ConfigManager, parent: QWidget | None = None) -> None:
        """Create the settings page from values in ``config``."""
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self.config = config
        self._controls: dict[str, QWidget] = {}
        self._opacity_value_label: QLabel | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the scrollable settings layout."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = SmoothScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        content.setObjectName("settingsContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(Sizes.CONTENT_MARGIN, 24, Sizes.CONTENT_MARGIN, 30)
        layout.setSpacing(16)
        title = QLabel("Настройки", content)
        title.setProperty("role", "page-title")
        layout.addWidget(title)

        layout.addWidget(self._general_section())
        layout.addWidget(self._appearance_section())
        layout.addWidget(self._effects_section())
        layout.addWidget(self._updates_section())
        layout.addWidget(self._about_section())

        reset_button = PushButton("Сбросить настройки", content)
        reset_button.setProperty("variant", "danger")
        reset_button.setFixedWidth(190)
        reset_button.clicked.connect(self._confirm_reset)
        layout.addWidget(reset_button, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _general_section(self) -> QFrame:
        """Create the general settings card."""
        card, layout = self._section_card("Общие")
        self._add_checkbox_row(card, layout, "general.autostart", "Запускать при старте системы", False)
        self._add_checkbox_row(card, layout, "general.tray_on_close", "Сворачивать в трей при закрытии", True)
        self._add_checkbox_row(card, layout, "general.start_minimized", "Запускать в свёрнутом виде", False)
        language = QComboBox(card)
        language.addItem("Русский", userData="ru")
        language.setCurrentIndex(language.findData(self.config.get("general.language", "ru")))
        language.currentIndexChanged.connect(lambda: self._save_combo("general.language", language))
        self._controls["general.language"] = language
        self._add_control_row(card, layout, "Язык интерфейса", language)
        return card

    def _appearance_section(self) -> QFrame:
        """Create the appearance settings card."""
        card, layout = self._section_card("Внешний вид")
        theme = QComboBox(card)
        theme.addItem("Тёмная", userData="dark")
        theme.setCurrentIndex(theme.findData(self.config.get("appearance.theme", "dark")))
        theme.currentIndexChanged.connect(lambda: self._save_combo("appearance.theme", theme))
        self._controls["appearance.theme"] = theme
        self._add_control_row(card, layout, "Тема", theme)

        scale = QComboBox(card)
        for value in (100, 125, 150):
            scale.addItem(f"{value}%", userData=value)
        scale.setCurrentIndex(scale.findData(self.config.get("appearance.scale", 100)))
        scale.currentIndexChanged.connect(lambda: self._save_combo("appearance.scale", scale))
        self._controls["appearance.scale"] = scale
        self._add_control_row(card, layout, "Масштаб интерфейса", scale)
        self._add_checkbox_row(card, layout, "appearance.animations", "Анимации", True)
        return card

    def _effects_section(self) -> QFrame:
        """Create the live Mica, Acrylic and panel opacity controls."""
        card, layout = self._section_card("Эффекты")
        effect_combo = ComboBox(card)
        effect_combo.addItem("Mica", userData="mica")
        effect_combo.addItem("Acrylic", userData="acrylic")
        effect_combo.addItem("Без эффекта", userData="none")
        effect_combo.setCurrentIndex(effect_combo.findData(self.config.get("effects.window_effect", "mica")))
        effect_combo.currentIndexChanged.connect(lambda: self._save_effect_name(effect_combo))
        self._controls["effects.window_effect"] = effect_combo
        self._add_control_row(card, layout, "Эффект окна", effect_combo)

        slider_row = QHBoxLayout()
        slider_label = QLabel("Прозрачность панелей", card)
        slider_label.setProperty("role", "setting-label")
        opacity_slider = Slider(Qt.Orientation.Horizontal, card)
        opacity_slider.setRange(50, 100)
        try:
            opacity_value = max(50, min(100, int(self.config.get("effects.panel_opacity", 80))))
        except (TypeError, ValueError):
            opacity_value = 80
        opacity_slider.setValue(opacity_value)
        opacity_slider.setFixedWidth(220)
        opacity_value_label = QLabel(f"{opacity_value}%", card)
        opacity_value_label.setProperty("role", "muted")
        self._opacity_value_label = opacity_value_label
        opacity_slider.valueChanged.connect(
            lambda value: self._save_effect_opacity(value, opacity_value_label, effect_combo)
        )
        self._controls["effects.panel_opacity"] = opacity_slider
        slider_row.addWidget(slider_label)
        slider_row.addStretch(1)
        slider_row.addWidget(opacity_slider)
        slider_row.addWidget(opacity_value_label)
        layout.addLayout(slider_row)
        return card

    def _updates_section(self) -> QFrame:
        """Create the update preference card."""
        card, layout = self._section_card("Обновления")
        self._add_checkbox_row(card, layout, "updates.check_on_start", "Проверять обновления", True)
        button = PrimaryPushButton("Проверить сейчас", card)
        button.setProperty("variant", "primary")
        button.setFixedWidth(165)
        button.clicked.connect(self._check_updates)
        layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
        return card

    def _about_section(self) -> QFrame:
        """Create the application information card."""
        card, layout = self._section_card("О программе")
        rows = (
            ("Название приложения", APP_NAME),
            ("Версия", APP_VERSION),
            ("Разработчик", APP_DEVELOPER),
            ("Python", platform.python_version()),
            ("PySide6", PYSIDE_VERSION),
        )
        for label_text, value in rows:
            row = QHBoxLayout()
            label = QLabel(label_text, card)
            label.setProperty("role", "muted")
            value_label = QLabel(value, card)
            value_label.setProperty("role", "about-value")
            value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            row.addWidget(label)
            row.addStretch(1)
            row.addWidget(value_label)
            layout.addLayout(row)
        github = PushButton("GitHub", card)
        github.clicked.connect(self._github_placeholder)
        github.setFixedWidth(100)
        layout.addWidget(github, 0, Qt.AlignmentFlag.AlignLeft)
        return card

    @staticmethod
    def _section_card(title_text: str) -> tuple[QFrame, QVBoxLayout]:
        """Create a labeled settings card and its inner layout."""
        card = QFrame()
        card.setProperty("frameRole", "card")
        card.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        effect = QGraphicsDropShadowEffect(card)
        effect.setBlurRadius(30)
        effect.setOffset(0, 3)
        effect.setColor(shadow_color())
        card.setGraphicsEffect(effect)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 17, 20, 18)
        layout.setSpacing(10)
        title = QLabel(title_text, card)
        title.setProperty("role", "section-title")
        layout.addWidget(title)
        return card, layout

    def _add_checkbox_row(
        self,
        parent: QWidget,
        layout: QVBoxLayout,
        key: str,
        label: str,
        default: bool,
    ) -> None:
        """Add a persisted checkbox to a section."""
        checkbox = CheckBox(label, parent)
        checkbox.setChecked(bool(self.config.get(key, default)))
        checkbox.toggled.connect(lambda value: self.config.set(key, value))
        self._controls[key] = checkbox
        layout.addWidget(checkbox)

    def _add_control_row(self, parent: QWidget, layout: QVBoxLayout, label_text: str, control: QWidget) -> None:
        """Add a right-aligned labeled combo box row."""
        row = QHBoxLayout()
        label = QLabel(label_text, parent)
        label.setProperty("role", "setting-label")
        row.addWidget(label)
        row.addStretch(1)
        row.addWidget(control)
        layout.addLayout(row)

    def _save_combo(self, key: str, combo: QComboBox) -> None:
        """Persist the current data value of a combo box."""
        value = combo.currentData()
        self.config.set(key, value)
        self.status_message.emit("Настройки сохранены")

    def _save_effect_name(self, combo: ComboBox) -> None:
        """Persist and immediately broadcast the selected window effect."""
        effect_name = str(combo.currentData() or "mica")
        self.config.set("effects.window_effect", effect_name)
        opacity = int(self.config.get("effects.panel_opacity", 80))
        self.effects_changed.emit(effect_name, opacity)
        self.status_message.emit("Эффект окна применён")

    def _save_effect_opacity(self, value: int, value_label: QLabel, combo: ComboBox) -> None:
        """Persist and immediately broadcast the panel opacity."""
        value_label.setText(f"{value}%")
        self.config.set("effects.panel_opacity", value)
        self.effects_changed.emit(str(combo.currentData() or "mica"), value)
        self.status_message.emit("Прозрачность панелей обновлена")

    def _check_updates(self) -> None:
        """Show the placeholder update result."""
        QMessageBox.information(self, "Обновления", "Обновлений не найдено.")
        self.status_message.emit("Проверка обновлений завершена")

    def _github_placeholder(self) -> None:
        """Tell the user that a repository link has not been configured."""
        QMessageBox.information(self, "GitHub", "Ссылка на репозиторий пока не настроена.")

    def _confirm_reset(self) -> None:
        """Ask for confirmation before restoring default settings."""
        result = QMessageBox.question(
            self,
            "Сбросить настройки",
            "Вернуть все настройки к значениям по умолчанию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if result == QMessageBox.StandardButton.Yes:
            self.config.reset()
            self._restore_controls()
            self.effects_changed.emit(
                str(self.config.get("effects.window_effect", "mica")),
                int(self.config.get("effects.panel_opacity", 80)),
            )
            self.status_message.emit("Настройки сброшены")

    def _restore_controls(self) -> None:
        """Refresh all controls after a configuration reset."""
        for key, control in self._controls.items():
            value = self.config.get(key)
            if isinstance(control, CheckBox):
                with QSignalBlocker(control):
                    control.setChecked(bool(value))
            elif isinstance(control, ComboBox):
                with QSignalBlocker(control):
                    control.setCurrentIndex(control.findData(value))
            elif isinstance(control, Slider):
                with QSignalBlocker(control):
                    control.setValue(int(value))
                if self._opacity_value_label is not None:
                    self._opacity_value_label.setText(f"{int(value)}%")
