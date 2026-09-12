"""Collapsible navigation sidebar."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QParallelAnimationGroup, QSize, Signal, Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.app import APP_VERSION
from core.config import ConfigManager
from core.theme import Colors, Sizes
from core.utils import get_user_name, load_icon


@dataclass
class NavigationItem:
    """Runtime data for a sidebar navigation item."""

    label: str
    page_index: int
    button: QPushButton


class Sidebar(QWidget):
    """Animated sidebar with user identity and page navigation."""

    navigation_requested = Signal(int)
    collapsed_changed = Signal(bool)

    def __init__(self, config: ConfigManager, parent: QWidget | None = None) -> None:
        """Create the sidebar using the saved collapsed state."""
        super().__init__(parent)
        self._logger = logging.getLogger(__name__)
        self.config = config
        self._items: list[NavigationItem] = []
        self._collapsed = bool(config.get("sidebar.collapsed", False))
        self._active_page = 0
        self._animation_group: QParallelAnimationGroup | None = None
        self.setObjectName("sidebar")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self._build_ui()
        self._apply_collapsed_state(animate=False)

    def _build_ui(self) -> None:
        """Build the user block, navigation area and footer."""
        self.setMinimumWidth(Sizes.SIDEBAR_COLLAPSED)
        self.setMaximumWidth(Sizes.SIDEBAR_EXPANDED)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.addStretch(1)
        self.toggle_button = QPushButton()
        self.toggle_button.setProperty("role", "sidebar-toggle")
        self.toggle_button.setIconSize(QSize(18, 18))
        self.toggle_button.setToolTip("Свернуть панель")
        self.toggle_button.clicked.connect(self.toggle_collapsed)
        header.addWidget(self.toggle_button)
        layout.addLayout(header)

        self.user_panel = QFrame(self)
        self.user_panel.setObjectName("userPanel")
        user_layout = QHBoxLayout(self.user_panel)
        user_layout.setContentsMargins(8, 7, 8, 7)
        user_layout.setSpacing(10)
        self.avatar_label = QLabel(self.user_panel)
        self.avatar_label.setObjectName("avatarLabel")
        self.avatar_label.setText(self._user_initial())
        self.avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_label.setFixedSize(40, 40)
        avatar_glow = QGraphicsDropShadowEffect(self.avatar_label)
        avatar_glow.setBlurRadius(18)
        avatar_glow.setOffset(0, 0)
        glow_color = QColor(Colors.ACCENT)
        glow_color.setAlpha(120)
        avatar_glow.setColor(glow_color)
        self.avatar_label.setGraphicsEffect(avatar_glow)
        user_layout.addWidget(self.avatar_label)
        self.user_name_label = QLabel(get_user_name(), self.user_panel)
        self.user_name_label.setObjectName("userNameLabel")
        self.user_name_label.setToolTip(get_user_name())
        self.user_name_label.setWordWrap(True)
        user_layout.addWidget(self.user_name_label, 1)
        layout.addWidget(self.user_panel)

        layout.addWidget(self._divider())
        self.navigation_layout = QVBoxLayout()
        self.navigation_layout.setContentsMargins(0, 0, 0, 0)
        self.navigation_layout.setSpacing(4)
        layout.addLayout(self.navigation_layout)
        layout.addStretch(1)

        layout.addWidget(self._divider())
        self.version_label = QLabel(f"v{APP_VERSION}", self)
        self.version_label.setObjectName("sidebarVersion")
        self.version_label.setProperty("role", "muted")
        self.version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.version_label)

    @staticmethod
    def _user_initial() -> str:
        """Return the first letter of the current user name."""
        name = get_user_name().strip()
        return name[:1].upper() if name else "П"

    @staticmethod
    def _divider() -> QFrame:
        """Create a horizontal sidebar divider."""
        divider = QFrame()
        divider.setObjectName("sidebarDivider")
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setFixedHeight(1)
        return divider

    def add_navigation_item(self, label: str, icon_name: str, page_index: int) -> QPushButton:
        """Add a page button and connect it to a stack index.

        Args:
            label: Visible page title.
            icon_name: SVG file name in ``assets/icons``.
            page_index: Corresponding QStackedWidget index.

        Returns:
            The created button, useful for plugin bookkeeping.
        """
        button = QPushButton(label, self)
        button.setProperty("role", "sidebar-item")
        button.setProperty("active", page_index == self._active_page)
        button.setIcon(load_icon(icon_name))
        button.setIconSize(QSize(20, 20))
        button.setToolTip(label)
        button.clicked.connect(lambda: self.navigation_requested.emit(page_index))
        self.navigation_layout.addWidget(button)
        item = NavigationItem(label=label, page_index=page_index, button=button)
        self._items.append(item)
        self._update_item(item)
        return button

    def set_active_page(self, page_index: int) -> None:
        """Mark one navigation item as active."""
        self._active_page = page_index
        for item in self._items:
            item.button.setProperty("active", item.page_index == page_index)
            self._refresh_style(item.button)

    def toggle_collapsed(self) -> None:
        """Animate between the expanded and compact sidebar widths."""
        self._collapsed = not self._collapsed
        self._apply_collapsed_state(animate=True)

    def _apply_collapsed_state(self, animate: bool) -> None:
        """Apply the current collapsed state and optionally animate it."""
        target = Sizes.SIDEBAR_COLLAPSED if self._collapsed else Sizes.SIDEBAR_EXPANDED
        if animate and bool(self.config.get("appearance.animations", True)):
            self._animate_width(target)
        else:
            self.setFixedWidth(target)
        self._update_content_visibility()
        self.config.set("sidebar.collapsed", self._collapsed)
        self.collapsed_changed.emit(self._collapsed)

    def _animate_width(self, target: int) -> None:
        """Animate both width constraints to keep layout negotiation stable."""
        if self._animation_group is not None:
            self._animation_group.stop()
        start = self.width()
        self.setMinimumWidth(start)
        self.setMaximumWidth(start)
        group = QParallelAnimationGroup(self)
        for property_name in (b"minimumWidth", b"maximumWidth"):
            animation = QPropertyAnimation(self, property_name, group)
            animation.setDuration(200)
            animation.setStartValue(start)
            animation.setEndValue(target)
            animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
            group.addAnimation(animation)
        self._animation_group = group
        group.finished.connect(lambda: self.setFixedWidth(target))
        group.start()

    def _update_content_visibility(self) -> None:
        """Update labels, alignment and toggle icon for the new width."""
        self.user_name_label.setVisible(not self._collapsed)
        self.version_label.setVisible(not self._collapsed)
        self.toggle_button.setIcon(load_icon("arrow_right.svg" if self._collapsed else "arrow_left.svg"))
        self.toggle_button.setToolTip("Развернуть панель" if self._collapsed else "Свернуть панель")
        self.user_panel.setProperty("collapsed", self._collapsed)
        self._refresh_style(self.user_panel)
        for item in self._items:
            self._update_item(item)

    def _update_item(self, item: NavigationItem) -> None:
        """Update one button to match the current sidebar mode."""
        item.button.setText("" if self._collapsed else item.label)
        item.button.setProperty("active", item.page_index == self._active_page)
        item.button.setToolTip(item.label)
        item.button.setIconSize(QSize(20, 20))
        self._refresh_style(item.button)

    @staticmethod
    def _refresh_style(widget: QWidget) -> None:
        """Re-evaluate a widget's dynamic QSS properties."""
        style = widget.style()
        style.unpolish(widget)
        style.polish(widget)
        widget.update()

    @property
    def is_collapsed(self) -> bool:
        """Return whether the sidebar is currently compact."""
        return self._collapsed

    def set_collapsed(self, collapsed: bool, animate: bool = False) -> None:
        """Set the sidebar state explicitly.

        Args:
            collapsed: Desired compact state.
            animate: Whether to animate the transition.
        """
        if self._collapsed == collapsed and self.width() in (Sizes.SIDEBAR_COLLAPSED, Sizes.SIDEBAR_EXPANDED):
            return
        self._collapsed = collapsed
        self._apply_collapsed_state(animate=animate)
