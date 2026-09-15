"""LIFE OS — экраны приложения (пока только оформление, без бизнес-логики)."""
from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QProgressBar, QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from . import config as cfg
from .theme import ACCENTS
from .widgets import (
    Divider, GlassCard, ImagePanel, LogoBadge, PulseLine, RingGauge, SparkChart,
    load_pixmap, make_label,
)


class BasePage(QScrollArea):
    """Прокручиваемая страница с общим отступом."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        host = QWidget()
        host.setAttribute(Qt.WA_TranslucentBackground, True)
        self.body = QVBoxLayout(host)
        self.body.setContentsMargins(30, 20, 30, 30)
        self.body.setSpacing(18)
        self.setWidget(host)
        self._accent_widgets: list = []

    def header(self, title: str, subtitle: str, badge: str | None = None):
        wrap = QWidget()
        lay = QHBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        col = QVBoxLayout()
        col.setSpacing(3)
        col.addWidget(make_label(title, "PageTitle"))
        col.addWidget(make_label(subtitle, "PageSub"))
        lay.addLayout(col)
        lay.addStretch(1)
        if badge:
            b = make_label(badge, "Badge")
            b.setAlignment(Qt.AlignCenter)
            lay.addWidget(b, 0, Qt.AlignTop)
        self.body.addWidget(wrap)
        return wrap

    def apply_accent(self, key: str):
        acc = ACCENTS[key]
        for w in self._accent_widgets:
            if isinstance(w, RingGauge):
                w.set_accent(acc.primary, acc.secondary)
            elif hasattr(w, "set_accent"):
                w.set_accent(acc.primary)


# ---------------------------------------------------------------- Dashboard
class DashboardPage(BasePage):
    def __init__(self, accent_key: str = "cyan", parent=None):
        super().__init__(parent)
        acc = ACCENTS[accent_key]
        self.header("Панель управления",
                    "Обзор состояния системы и быстрый доступ к модулям",
                    "LIVE · v" + cfg.APP_VERSION)

        # --- HERO -----------------------------------------------------------
        hero = ImagePanel(cfg.BACKGROUNDS / "hero_card.jpg", overlay=0.62, accent=acc.primary)
        hero.setMinimumHeight(212)
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(30, 26, 30, 26)
        hl.setSpacing(24)

        left = QVBoxLayout()
        left.setSpacing(8)
        left.addWidget(make_label("CORE ONLINE", "CardKicker"))
        left.addWidget(make_label("Добро пожаловать в LIFE OS", "HeroTitle"))
        left.addWidget(make_label(
            "Единая оболочка для работы с компьютером: модули, автоматизация\n"
            "и контроль системы в одном тёмном стеклянном интерфейсе.",
            "HeroBody", wrap=True))
        pulse = PulseLine(accent=acc.primary, height=54)
        left.addWidget(pulse)
        hl.addLayout(left, 3)

        badge = LogoBadge(size=130, accent=acc.primary, pixmap_name="logo_512.png")
        hl.addWidget(badge, 0, Qt.AlignCenter)
        hl.addStretch(1)

        self.body.addWidget(hero)
        self._accent_widgets += [hero, pulse, badge]

        # --- KPI-строка -----------------------------------------------------
        grid = QGridLayout()
        grid.setSpacing(16)
        stats = [
            ("CPU", 27, "Загрузка процессора"),
            ("MEMORY", 54, "Оперативная память"),
            ("DISK", 41, "Дисковое пространство"),
        ]
        for i, (kicker, val, cap) in enumerate(stats):
            card = GlassCard(padding=18)
            card.body.setSpacing(6)
            card.body.addWidget(make_label(kicker, "CardKicker"))
            gauge = RingGauge(value=val, accent=acc.primary,
                              accent2=acc.secondary, size=132)
            card.body.addWidget(gauge, 0, Qt.AlignCenter)
            cap_lb = make_label(cap, "StatCaption", wrap=True)
            cap_lb.setAlignment(Qt.AlignCenter)
            card.body.addWidget(cap_lb)
            grid.addWidget(card, 0, i)
            self._accent_widgets.append(gauge)

        activity = GlassCard(padding=18)
        activity.body.setSpacing(6)
        activity.body.addWidget(make_label("ACTIVITY", "CardKicker"))
        activity.body.addWidget(make_label("Активность за сессию", "CardTitle"))
        spark = SparkChart(accent=acc.primary, height=92)
        activity.body.addWidget(spark)
        activity.body.addWidget(make_label("Данные появятся в следующих версиях",
                                           "StatCaption"))
        grid.addWidget(activity, 0, 3)
        grid.setColumnStretch(3, 2)
        self._accent_widgets.append(spark)
        self.body.addLayout(grid)

        # --- Модули ---------------------------------------------------------
        self.body.addWidget(make_label("МОДУЛИ", "SidebarSection"))
        mods = QGridLayout()
        mods.setSpacing(16)
        modules = [
            ("dashboard_glyph_128.png", "Рабочий стол", "Виджеты, быстрый обзор дня и системы", "READY"),
            ("tools_glyph_128.png", "Автоматизация", "Сценарии, макросы и горячие клавиши", "SOON"),
            ("settings_glyph_128.png", "Оптимизация", "Очистка, автозагрузка, службы Windows", "SOON"),
            ("about_glyph_128.png", "Знания", "Заметки, база ссылок и личные инструкции", "SOON"),
        ]
        for i, (icon, title, desc, state) in enumerate(modules):
            card = GlassCard(padding=18)
            card.body.setSpacing(10)
            top = QHBoxLayout()
            ic = QLabel()
            ic.setPixmap(load_pixmap(cfg.ICONS / icon, 40, 40))
            top.addWidget(ic)
            top.addStretch(1)
            st = make_label(state, "Badge" if state == "READY" else "BadgeMuted")
            top.addWidget(st, 0, Qt.AlignTop)
            card.body.addLayout(top)
            card.body.addWidget(make_label(title, "CardTitle"))
            card.body.addWidget(make_label(desc, "CardBody", wrap=True))
            mods.addWidget(card, i // 4, i % 4)
        self.body.addLayout(mods)
        self.body.addStretch(1)


# ------------------------------------------------------------------- Tools
class ToolsPage(BasePage):
    def __init__(self, accent_key: str = "cyan", parent=None):
        super().__init__(parent)
        acc = ACCENTS[accent_key]
        self.header("Инструменты", "Каталог модулей LIFE OS для работы с ПК", "PREVIEW")

        search_row = QWidget()
        sl = QHBoxLayout(search_row)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(10)
        search = QLineEdit()
        search.setObjectName("Search")
        search.setPlaceholderText("Поиск инструмента…   (в разработке)")
        search.setFixedHeight(42)
        sl.addWidget(search, 1)
        for name in ("Все", "Система", "Файлы", "Сеть", "Медиа"):
            chip = QPushButton(name)
            chip.setObjectName("Chip")
            chip.setCheckable(True)
            chip.setChecked(name == "Все")
            chip.setFixedHeight(42)
            chip.setCursor(Qt.PointingHandCursor)
            sl.addWidget(chip)
        self.body.addWidget(search_row)

        grid = QGridLayout()
        grid.setSpacing(16)
        tools = [
            ("tools_glyph_128.png", "Быстрый запуск", "Единая палитра команд и приложений"),
            ("settings_glyph_128.png", "Чистильщик", "Временные файлы, кэш, корзина"),
            ("dashboard_glyph_128.png", "Монитор ресурсов", "CPU, RAM, диски и сеть в реальном времени"),
            ("tools_glyph_128.png", "Пакетные файлы", "Массовое переименование и сортировка"),
            ("settings_glyph_128.png", "Автозагрузка", "Управление стартом программ"),
            ("about_glyph_128.png", "Буфер обмена", "История копирований и шаблоны"),
        ]
        for i, (icon, title, desc) in enumerate(tools):
            card = GlassCard(padding=18)
            card.body.setSpacing(10)
            head = QHBoxLayout()
            ic = QLabel()
            ic.setPixmap(load_pixmap(cfg.ICONS / icon, 38, 38))
            head.addWidget(ic)
            head.addSpacing(4)
            tcol = QVBoxLayout()
            tcol.setSpacing(2)
            tcol.addWidget(make_label(title, "CardTitle"))
            tcol.addWidget(make_label("модуль v0.2", "Mono"))
            head.addLayout(tcol)
            head.addStretch(1)
            head.addWidget(make_label("SOON", "BadgeMuted"), 0, Qt.AlignTop)
            card.body.addLayout(head)
            card.body.addWidget(make_label(desc, "CardBody", wrap=True))
            bar = QProgressBar()
            bar.setObjectName("Thin")
            bar.setTextVisible(False)
            bar.setValue([70, 45, 88, 30, 55, 20][i])
            card.body.addWidget(bar)
            grid.addWidget(card, i // 3, i % 3)
        self.body.addLayout(grid)
        self.body.addStretch(1)


# ---------------------------------------------------------------- Settings
class SettingsPage(BasePage):
    """Настройки внешнего вида. Акценты переключаются, остальное — заготовки."""

    def __init__(self, accent_key: str, on_accent, on_background, parent=None):
        super().__init__(parent)
        self._on_accent = on_accent
        acc = ACCENTS[accent_key]
        self.header("Настройки", "Внешний вид и поведение оболочки", "v" + cfg.APP_VERSION)

        # --- Акцент ---------------------------------------------------------
        card = GlassCard(padding=22, hoverable=False)
        card.body.setSpacing(14)
        card.body.addWidget(make_label("APPEARANCE", "CardKicker"))
        card.body.addWidget(make_label("Акцентный цвет", "CardTitle"))
        card.body.addWidget(make_label(
            "Активны Cyan и Electric Blue. Остальные палитры уже заложены "
            "в тему и включатся в следующих версиях.", "CardBody", wrap=True))

        chips = QHBoxLayout()
        chips.setSpacing(10)
        self._chips: list[QPushButton] = []
        for key, a in ACCENTS.items():
            btn = QPushButton(a.title if a.available else a.title + "  ·  soon")
            btn.setObjectName("Chip")
            btn.setCheckable(True)
            btn.setChecked(key == accent_key)
            btn.setEnabled(a.available)
            btn.setFixedHeight(38)
            btn.setCursor(Qt.PointingHandCursor if a.available else Qt.ForbiddenCursor)
            btn.setStyleSheet(
                f"QPushButton#Chip {{ border-left: 4px solid {a.primary}; }}"
            )
            btn.clicked.connect(lambda _=False, k=key: self._pick(k))
            chips.addWidget(btn)
            self._chips.append(btn)
        chips.addStretch(1)
        card.body.addLayout(chips)
        self.body.addWidget(card)

        # --- Фон ------------------------------------------------------------
        bgcard = GlassCard(padding=22, hoverable=False)
        bgcard.body.setSpacing(12)
        bgcard.body.addWidget(make_label("BACKGROUND", "CardKicker"))
        bgcard.body.addWidget(make_label("Фон оболочки", "CardTitle"))
        bgrow = QHBoxLayout()
        bgrow.setSpacing(14)
        for name, file in (("Tech Glass", "bg_main.jpg"), ("Aurora", "bg_aurora.jpg")):
            tile = ImagePanel(cfg.BACKGROUNDS / f"{file.replace('.jpg', '@half.jpg')}",
                              radius=14, overlay=0.30, accent=acc.primary)
            tile.setFixedSize(220, 116)
            tl = QVBoxLayout(tile)
            tl.setContentsMargins(12, 12, 12, 12)
            tl.addStretch(1)
            tl.addWidget(make_label(name, "CardTitle"))
            pick = QPushButton("", tile)
            pick.setGeometry(0, 0, 220, 116)
            pick.setCursor(Qt.PointingHandCursor)
            pick.setStyleSheet("background: transparent; border: none;")
            pick.clicked.connect(lambda _=False, f=file: on_background(f))
            bgrow.addWidget(tile)
            self._accent_widgets.append(tile)
        bgrow.addStretch(1)
        bgcard.body.addLayout(bgrow)
        self.body.addWidget(bgcard)

        # --- Переключатели --------------------------------------------------
        opts = GlassCard(padding=22, hoverable=False)
        opts.body.setSpacing(4)
        opts.body.addWidget(make_label("SYSTEM", "CardKicker"))
        opts.body.addWidget(make_label("Поведение", "CardTitle"))
        opts.body.addSpacing(8)
        switches = [
            ("Запускать вместе с Windows", "Оболочка стартует свёрнутой в трей", False),
            ("Сворачивать в трей при закрытии", "Крестик прячет окно, а не закрывает", True),
            ("Анимации интерфейса", "Пульс, свечение и плавные переходы", True),
            ("Эффект стекла (acrylic)", "Полупрозрачные панели поверх фона", True),
            ("Звуковые уведомления", "Появятся в версии 0.3", False),
        ]
        for i, (title, desc, checked) in enumerate(switches):
            if i:
                opts.body.addWidget(Divider())
            r = QWidget()
            rl = QHBoxLayout(r)
            rl.setContentsMargins(0, 10, 0, 10)
            col = QVBoxLayout()
            col.setSpacing(2)
            col.addWidget(make_label(title, "CardTitle"))
            col.addWidget(make_label(desc, "StatCaption"))
            rl.addLayout(col)
            rl.addStretch(1)
            sw = QCheckBox()
            sw.setObjectName("Switch")
            sw.setChecked(checked)
            sw.setCursor(Qt.PointingHandCursor)
            rl.addWidget(sw)
            opts.body.addWidget(r)
        self.body.addWidget(opts)

        # --- Язык/масштаб ---------------------------------------------------
        misc = GlassCard(padding=22, hoverable=False)
        misc.body.setSpacing(12)
        misc.body.addWidget(make_label("LOCALE", "CardKicker"))
        mrow = QHBoxLayout()
        mrow.setSpacing(24)
        for label, items in (("Язык интерфейса", ["Русский", "English"]),
                             ("Масштаб", ["100%", "125%", "150%"]),
                             ("Тема", ["Dark Glass", "Light (soon)"])):
            col = QVBoxLayout()
            col.setSpacing(6)
            col.addWidget(make_label(label, "StatCaption"))
            cb = QComboBox()
            cb.setObjectName("Select")
            cb.addItems(items)
            cb.setCursor(Qt.PointingHandCursor)
            col.addWidget(cb)
            mrow.addLayout(col)
        mrow.addStretch(1)
        misc.body.addLayout(mrow)
        self.body.addWidget(misc)
        self.body.addStretch(1)

    def _pick(self, key: str):
        for btn, k in zip(self._chips, ACCENTS.keys()):
            btn.setChecked(k == key)
        self._on_accent(key)


# ------------------------------------------------------------------- About
class AboutPage(BasePage):
    def __init__(self, accent_key: str = "cyan", parent=None):
        super().__init__(parent)
        acc = ACCENTS[accent_key]
        self.header("О программе", "LIFE OS — персональная операционная система", "ALPHA")

        hero = ImagePanel(cfg.BACKGROUNDS / "about_art.jpg", overlay=0.58, accent=acc.primary)
        hero.setMinimumHeight(260)
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(34, 28, 34, 28)
        hl.setSpacing(28)
        logo = LogoBadge(size=160, accent=acc.primary, pixmap_name="logo_512.png")
        hl.addWidget(logo, 0, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(8)
        col.addWidget(make_label(f"{cfg.APP_NAME}", "HeroTitle"))
        col.addWidget(make_label(cfg.APP_TAGLINE, "HeroBody"))
        col.addWidget(make_label(f"BUILD {cfg.APP_BUILD}  ·  PySide 6  ·  {cfg.APP_ORG}", "Mono"))
        col.addSpacing(6)
        btns = QHBoxLayout()
        btns.setSpacing(10)
        b1 = QPushButton("Что нового")
        b1.setObjectName("Primary")
        b1.setFixedHeight(40)
        b1.setCursor(Qt.PointingHandCursor)
        b2 = QPushButton("Репозиторий")
        b2.setObjectName("Ghost")
        b2.setFixedHeight(40)
        b2.setCursor(Qt.PointingHandCursor)
        btns.addWidget(b1)
        btns.addWidget(b2)
        btns.addStretch(1)
        col.addLayout(btns)
        hl.addLayout(col, 1)
        self.body.addWidget(hero)
        self._accent_widgets += [hero, logo]

        grid = QGridLayout()
        grid.setSpacing(16)
        roadmap = [
            ("0.1", "Оболочка", "Тёмный glass-интерфейс, навигация, трей, брендинг", "DONE"),
            ("0.2", "Инструменты", "Мониторинг системы и быстрый запуск", "NEXT"),
            ("0.3", "Автоматизация", "Сценарии, макросы, горячие клавиши", "PLAN"),
            ("0.4", "Синхронизация", "Профили, облако и резервные копии", "PLAN"),
        ]
        for i, (ver, title, desc, state) in enumerate(roadmap):
            card = GlassCard(padding=18)
            card.body.setSpacing(8)
            head = QHBoxLayout()
            head.addWidget(make_label("v" + ver, "CardKicker"))
            head.addStretch(1)
            head.addWidget(make_label(state, "Badge" if state == "DONE" else "BadgeMuted"))
            card.body.addLayout(head)
            card.body.addWidget(make_label(title, "CardTitle"))
            card.body.addWidget(make_label(desc, "CardBody", wrap=True))
            grid.addWidget(card, 0, i)
        self.body.addLayout(grid)

        credits = GlassCard(padding=22, hoverable=False)
        credits.body.setSpacing(6)
        credits.body.addWidget(make_label("STACK", "CardKicker"))
        credits.body.addWidget(make_label(
            "Python 3 · PySide6 (Qt 6) · кастомный QSS · собственная графика 4K",
            "CardBody", wrap=True))
        credits.body.addWidget(make_label(
            "© 2026 IstikFramer. Версия 0.1 — визуальный прототип оболочки: "
            "функциональные модули подключаются в следующих релизах.",
            "StatCaption", wrap=True))
        self.body.addWidget(credits)
        self.body.addStretch(1)
