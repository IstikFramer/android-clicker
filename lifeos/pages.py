"""LIFE OS — экраны приложения: Главная, Настройки, О программе."""
from __future__ import annotations

import json

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QScrollArea, QSizePolicy, QVBoxLayout, QWidget,
)

from . import config as cfg
from . import icons
from .settings import settings
from .system_tools import own_autostart_enabled, set_own_autostart
from .theme import ACCENTS, current_accent
from .elevation import can_elevate, is_admin
from .update_ui import UpdateBanner
from .updater import UpdateInfo
from .widgets import (
    ColorDot, Divider, GlassCard, ImagePanel, LogoOrb, OrbIcon,
    SegmentedControl, SliderRow, Switch, make_label,
)


def load_json(name: str) -> dict:
    try:
        return json.loads((cfg.DATA / name).read_text("utf-8"))
    except (OSError, ValueError):
        return {}


CHANGE_TYPES = {
    "added":    ("ДОБАВЛЕНО", "sparkles"),
    "improved": ("УЛУЧШЕНО", "layers"),
    "fixed":    ("ИСПРАВЛЕНО", "shield"),
}


class BasePage(QScrollArea):
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

    def header(self, title: str, subtitle: str, badge: str | None = None):
        wrap = QWidget()
        wrap.setObjectName("Transparent")
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


# =========================================================== Главный экран
class HomePage(BasePage):
    """Что нового в текущей версии — то, что видит пользователь при запуске."""

    def __init__(self, on_update=None, parent=None):
        super().__init__(parent)
        self._on_update = on_update
        self._banner: UpdateBanner | None = None
        data = load_json("changelog.json")
        releases = data.get("releases", [])
        rel = releases[0] if releases else {}

        # ---------- hero ----------
        hero = ImagePanel(cfg.BACKGROUNDS / "hero_card.jpg", overlay=0.66)
        hero.setMinimumHeight(230)
        hero.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(34, 28, 34, 28)
        hl.setSpacing(26)

        col = QVBoxLayout()
        col.setSpacing(9)
        top = QHBoxLayout()
        top.setSpacing(8)
        top.addWidget(make_label(f"ВЕРСИЯ {rel.get('version', cfg.APP_VERSION)}", "CardKicker"))
        ch = make_label(rel.get("channel", cfg.APP_CHANNEL), "Badge")
        top.addWidget(ch)
        top.addStretch(1)
        col.addLayout(top)
        col.addWidget(make_label(rel.get("title", "Обновление"), "HeroTitle"))
        col.addWidget(make_label(rel.get("summary", ""), "HeroBody", wrap=True))
        col.addStretch(1)

        stats = QHBoxLayout()
        stats.setSpacing(22)
        counts = {"added": 0, "improved": 0, "fixed": 0}
        for c in rel.get("changes", []):
            counts[c.get("type", "added")] = counts.get(c.get("type", "added"), 0) + 1
        for key, label in (("added", "новое"), ("improved", "улучшено"), ("fixed", "исправлено")):
            box = QVBoxLayout()
            box.setSpacing(0)
            n = make_label(str(counts.get(key, 0)), "PageTitle")
            box.addWidget(n)
            box.addWidget(make_label(label, "Caption"))
            stats.addLayout(box)
        stats.addStretch(1)
        col.addLayout(stats)
        hl.addLayout(col, 1)
        hl.addWidget(LogoOrb(size=150), 0, Qt.AlignVCenter)
        self.body.addWidget(hero)

        # место под плашку «доступно обновление»
        self._banner_slot = QVBoxLayout()
        self._banner_slot.setContentsMargins(0, 0, 0, 0)
        self._banner_slot.setSpacing(0)
        self.body.addLayout(self._banner_slot)

        # ---------- список изменений ----------
        self.body.addSpacing(4)
        self.body.addWidget(make_label("ЧТО НОВОГО В ЭТОЙ ВЕРСИИ", "SidebarSection"))

        grouped: dict[str, list[str]] = {"added": [], "improved": [], "fixed": []}
        for c in rel.get("changes", []):
            grouped.setdefault(c.get("type", "added"), []).append(c.get("text", ""))

        grid = QGridLayout()
        grid.setSpacing(16)
        acc = current_accent()
        cols = 0
        for key in ("added", "improved", "fixed"):
            items = grouped.get(key) or []
            if not items:
                continue
            title, icon_name = CHANGE_TYPES[key]
            card = GlassCard(padding=20, spacing=10)
            head = QHBoxLayout()
            head.setSpacing(9)
            ic = QLabel()
            ic.setPixmap(icons.pixmap(icon_name, 18, acc.primary, 1.8))
            ic.setFixedSize(18, 18)
            head.addWidget(ic)
            head.addWidget(make_label(title, "CardKicker"))
            head.addStretch(1)
            head.addWidget(make_label(str(len(items)), "BadgeMuted"))
            card.body.addLayout(head)
            for text in items:
                row = QHBoxLayout()
                row.setSpacing(9)
                dot = QLabel("•")
                dot.setObjectName("MonoAccent")
                dot.setFixedWidth(9)
                dot.setAlignment(Qt.AlignTop)
                row.addWidget(dot, 0, Qt.AlignTop)
                row.addWidget(make_label(text, "CardBody", wrap=True), 1)
                card.body.addLayout(row)
            card.body.addStretch(1)
            grid.addWidget(card, 0, cols)
            cols += 1
        for i in range(cols):
            grid.setColumnStretch(i, 1)
        self.body.addLayout(grid)

        # ---------- прошлые версии ----------
        if len(releases) > 1:
            self.body.addSpacing(6)
            self.body.addWidget(make_label("ПРЕДЫДУЩИЕ ВЕРСИИ", "SidebarSection"))
            for old in releases[1:]:
                card = GlassCard(padding=18, spacing=8, hoverable=True)
                head = QHBoxLayout()
                head.setSpacing(10)
                head.addWidget(make_label("v" + old.get("version", ""), "MonoAccent"))
                head.addWidget(make_label(old.get("title", ""), "CardTitle"))
                head.addStretch(1)
                head.addWidget(make_label(old.get("date", ""), "Caption"))
                card.body.addLayout(head)
                texts = " · ".join(c.get("text", "") for c in old.get("changes", []))
                card.body.addWidget(make_label(texts, "CardBody", wrap=True))
                self.body.addWidget(card)

        self.body.addStretch(1)

    def on_update_state(self, info: UpdateInfo):
        """Показывает или прячет плашку обновления."""
        if self._banner is not None:
            self._banner.setParent(None)
            self._banner.deleteLater()
            self._banner = None
        if not (info and info.available):
            return
        banner = UpdateBanner(info)
        if self._on_update:
            banner.clicked.connect(self._on_update)
        self._banner_slot.addWidget(banner)
        self._banner = banner


# ============================================================== Настройки
class SettingsPage(BasePage):
    """Живые настройки: любое изменение сразу применяется и сохраняется."""

    def __init__(self, on_restyle, on_background, parent=None):
        super().__init__(parent)
        self._on_restyle = on_restyle
        self._on_background = on_background
        self._switches: dict[str, Switch] = {}
        # настройка могла разойтись с реальностью: запись из автозагрузки
        # мог убрать сам пользователь или другая программа
        if settings.get("autostart") != own_autostart_enabled():
            settings.set("autostart", own_autostart_enabled())
        self.header("Настройки", "Внешний вид, производительность и поведение программы")

        self._build_appearance()
        self._build_performance()
        self._build_updates()
        self._build_behaviour()
        self._build_reset()
        self.body.addStretch(1)

    # ------------------------------------------------------- внешний вид
    def _build_appearance(self):
        card = GlassCard(padding=22, spacing=14, hoverable=False)
        card.body.addWidget(make_label("ВНЕШНИЙ ВИД", "CardKicker"))

        # акцент
        row = QHBoxLayout()
        row.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(make_label("Акцентный цвет", "CardTitle"))
        col.addWidget(make_label("Подсветка активных элементов и свечение", "Caption"))
        row.addLayout(col)
        row.addStretch(1)
        self._dots: list[ColorDot] = []
        for key, a in ACCENTS.items():
            dot = ColorDot(key, a.primary, a.secondary, key == settings.get("accent"))
            dot.setToolTip(a.title)
            dot.clicked.connect(self._pick_accent)
            row.addWidget(dot)
            self._dots.append(dot)
        card.body.addLayout(row)
        card.body.addWidget(Divider())

        # фон
        bg_row = QHBoxLayout()
        bg_row.setSpacing(14)
        col2 = QVBoxLayout()
        col2.setSpacing(1)
        col2.addWidget(make_label("Фон оболочки", "CardTitle"))
        col2.addWidget(make_label("Изображение под интерфейсом", "Caption"))
        bg_row.addLayout(col2)
        bg_row.addStretch(1)
        self._bg_tiles: list[tuple[QWidget, str]] = []
        for name, file in (("Blue", "bg_main.jpg"), ("Violet", "bg_violet.jpg"),
                           ("Deep", "bg_deep.jpg"),
                           ("Aurora", "bg_aurora.jpg")):
            tile = ImagePanel(cfg.BACKGROUNDS / file.replace(".jpg", "@half.jpg"),
                              overlay=0.28, radius=12)
            tile.setFixedSize(150, 84)
            tile.setCursor(Qt.PointingHandCursor)
            tl = QVBoxLayout(tile)
            tl.setContentsMargins(10, 8, 10, 8)
            tl.addStretch(1)
            tl.addWidget(make_label(name, "CardTitle"))
            btn = QPushButton("", tile)
            btn.setGeometry(0, 0, 150, 84)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("background: transparent; border: none;")
            btn.clicked.connect(lambda _=False, f=file: self._pick_bg(f))
            bg_row.addWidget(tile)
            self._bg_tiles.append((tile, file))
        card.body.addLayout(bg_row)
        card.body.addWidget(Divider())

        # слайдеры
        sliders = [
            ("glass_opacity", "Прозрачность панелей", "Плотность стеклянных поверхностей", 0, 100, "%", 1),
            ("glow_strength", "Сила свечения", "Яркость неонового ореола элементов", 0, 100, "%", 1),
            ("corner_radius", "Скругление углов", "Радиус карточек, кнопок и окна", 4, 28, " px", 1),
            ("ui_scale", "Масштаб интерфейса", "Размер текста и элементов", 85, 130, "%", 5),
        ]
        for i, (key, title, desc, lo, hi, suf, step) in enumerate(sliders):
            if i:
                card.body.addWidget(Divider())
            r = SliderRow(title, desc, lo, hi, settings.get(key), suf, step)
            r.valueChanged.connect(lambda v, k=key: self._apply(k, v))
            card.body.addWidget(r)
        self.body.addWidget(card)

    # --------------------------------------------------- производительность
    def _build_performance(self):
        card = GlassCard(padding=22, spacing=14, hoverable=False)
        card.body.addWidget(make_label("ПРОИЗВОДИТЕЛЬНОСТЬ", "CardKicker"))

        row = QHBoxLayout()
        row.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(make_label("Ограничение частоты кадров", "CardTitle"))
        col.addWidget(make_label("Выше — плавнее, ниже — экономнее для ноутбука", "Caption"))
        row.addLayout(col)
        row.addStretch(1)
        fps_values = [30, 60, 120]
        current = settings.get("fps_limit")
        seg = SegmentedControl(["30", "60", "120"],
                               fps_values.index(current) if current in fps_values else 1)
        seg.setFixedWidth(210)
        seg.changed.connect(lambda i: self._apply("fps_limit", fps_values[i]))
        row.addWidget(seg)
        card.body.addLayout(row)
        card.body.addWidget(Divider())

        speed = SliderRow("Скорость анимаций", "Темп переходов и подсветки",
                          50, 200, settings.get("anim_speed"), "%", 5)
        speed.valueChanged.connect(lambda v: self._apply("anim_speed", v))
        card.body.addWidget(speed)
        card.body.addWidget(Divider())

        toggles = [
            ("animations", "Анимации интерфейса", "Плавные переходы и подсветка элементов"),
            ("heavy_effects", "Тяжёлые эффекты", "Тени, свечение фона и дыхание логотипа"),
            ("power_saving", "Режим энергосбережения", "Ограничивает кадры и отключает фоновые эффекты"),
        ]
        for i, (key, title, desc) in enumerate(toggles):
            if i:
                card.body.addWidget(Divider())
            card.body.addWidget(self._switch_row(key, title, desc))
        self.body.addWidget(card)

    # ----------------------------------------------------------- обновления
    def _build_updates(self):
        card = GlassCard(padding=22, spacing=14, hoverable=False)
        card.body.addWidget(make_label("ОБНОВЛЕНИЯ", "CardKicker"))
        card.body.addWidget(self._switch_row(
            "auto_update_check", "Проверять обновления автоматически",
            "Программа сама узнаёт о новых версиях в фоне"))
        card.body.addWidget(Divider())

        row = QHBoxLayout()
        col = QVBoxLayout()
        col.setSpacing(2)
        col.addWidget(make_label("Как часто проверять", "CardTitle"))
        col.addWidget(make_label(
            "Реже — меньше обращений к сети", "Caption"))
        row.addLayout(col, 1)
        mapping = {1: 0, 6: 1, 24: 2}
        seg = SegmentedControl(["1 час", "6 часов", "Раз в сутки"],
                               index=mapping.get(settings.get("update_interval_h"), 0))
        seg.changed.connect(
            lambda i: settings.set("update_interval_h", (1, 6, 24)[i]))
        row.addWidget(seg)
        card.body.addLayout(row)
        self.body.addWidget(card)

    # -------------------------------------------------------------- система
    def _build_behaviour(self):
        card = GlassCard(padding=22, spacing=14, hoverable=False)
        card.body.addWidget(make_label("СИСТЕМА", "CardKicker"))
        toggles = [
            ("autostart", "Запускать вместе с системой",
             "Программа стартует при входе в учётную запись"),
            ("start_minimized", "Запускать свёрнутой", "Открывать сразу в области уведомлений"),
            ("close_to_tray", "Сворачивать в трей при закрытии", "Кнопка закрытия прячет окно, а не завершает работу"),
            ("tray_notifications", "Уведомления в трее", "Всплывающие подсказки при сворачивании"),
        ]
        for i, (key, title, desc) in enumerate(toggles):
            if i:
                card.body.addWidget(Divider())
            card.body.addWidget(self._switch_row(key, title, desc))

        card.body.addWidget(Divider())
        row = QHBoxLayout()
        row.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(make_label("Язык интерфейса", "CardTitle"))
        col.addWidget(make_label("Другие языки появятся в следующих версиях", "Caption"))
        row.addLayout(col)
        row.addStretch(1)
        cb = QComboBox()
        cb.setObjectName("Select")
        cb.addItems(["Русский"])
        cb.setCursor(Qt.PointingHandCursor)
        row.addWidget(cb)
        w = QWidget()
        w.setObjectName("Transparent")
        w.setLayout(row)
        card.body.addWidget(w)
        self.body.addWidget(card)

    def _build_reset(self):
        card = GlassCard(padding=20, spacing=12, hoverable=False)
        row = QHBoxLayout()
        row.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(make_label("Сбросить настройки", "CardTitle"))
        col.addWidget(make_label(
            f"Вернуть все параметры к значениям по умолчанию · {cfg.SETTINGS_FILE}",
            "Caption"))
        row.addLayout(col)
        row.addStretch(1)
        btn = QPushButton("Сбросить")
        btn.setObjectName("Ghost")
        btn.setFixedHeight(38)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._reset)
        row.addWidget(btn)
        card.body.addLayout(row)
        self.body.addWidget(card)

    # ------------------------------------------------------------ элементы
    def _switch_row(self, key: str, title: str, desc: str) -> QWidget:
        w = QWidget()
        w.setObjectName("Transparent")
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 9, 0, 9)
        lay.setSpacing(12)
        col = QVBoxLayout()
        col.setSpacing(1)
        col.addWidget(make_label(title, "CardTitle"))
        col.addWidget(make_label(desc, "Caption"))
        lay.addLayout(col)
        lay.addStretch(1)
        sw = Switch(settings.get(key))
        sw.toggled.connect(lambda v, k=key: self._apply(k, v))
        self._switches[key] = sw
        lay.addWidget(sw)
        return w

    def _sync_autostart(self):
        """Вернуть переключатель к настоящему состоянию автозагрузки."""
        sw = self._switches.get("autostart")
        if sw is not None:
            sw.setChecked(settings.get("autostart"))

    # -------------------------------------------------------------- логика
    def _apply(self, key: str, value):
        settings.set(key, value)
        if key == "autostart":
            ok, err = set_own_autostart(bool(value))
            if not ok:
                settings.set("autostart", not value)
                QMessageBox.warning(
                    self, "Автозагрузка",
                    "Не удалось изменить автозагрузку.\n\n" + err)
                self._sync_autostart()

    def _pick_accent(self, key: str):
        settings.set("accent", key)
        for dot in self._dots:
            dot.setSelected(dot._key == key)

    def _pick_bg(self, file: str):
        settings.set("background", file)
        self._on_background()

    def _reset(self):
        settings.reset()
        self._on_restyle(rebuild=True)


# =========================================================== О программе
class AboutPage(BasePage):
    def __init__(self, on_show_eula, on_check=None, on_update=None,
                 on_elevate=None, parent=None):
        super().__init__(parent)
        self._on_check = on_check
        self._on_update = on_update
        self.header("О программе", f"{cfg.APP_NAME} · сведения о продукте и разработчике")

        hero = ImagePanel(cfg.BACKGROUNDS / "about_art.jpg", overlay=0.70)
        hero.setMinimumHeight(240)
        hero.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        hl = QHBoxLayout(hero)
        hl.setContentsMargins(34, 28, 34, 28)
        hl.setSpacing(28)
        hl.addWidget(LogoOrb(size=136), 0, Qt.AlignVCenter)
        col = QVBoxLayout()
        col.setSpacing(7)
        col.addWidget(make_label(cfg.APP_NAME, "HeroTitle"))
        col.addWidget(make_label(cfg.APP_TAGLINE, "HeroBody"))
        col.addWidget(make_label(
            f"ВЕРСИЯ {cfg.APP_VERSION}  ·  СБОРКА {cfg.APP_BUILD}  ·  {cfg.APP_CHANNEL}",
            "Mono"))
        hl.addLayout(col, 1)
        self.body.addWidget(hero)

        # --- разработчик ---
        acc = current_accent()
        grid = QGridLayout()
        grid.setSpacing(16)

        dev = GlassCard(padding=20, spacing=10)
        dev.body.addWidget(make_label("РАЗРАБОТЧИК", "CardKicker"))
        dev.body.addWidget(make_label(cfg.DEV_NAME, "HeroTitle"))
        dev.body.addWidget(make_label(
            "Разработка и поддержка программного обеспечения.", "CardBody", wrap=True))
        dev.body.addStretch(1)
        grid.addWidget(dev, 0, 0)

        contact = GlassCard(padding=20, spacing=10)
        contact.body.addWidget(make_label("СВЯЗЬ", "CardKicker"))
        mail_row = QHBoxLayout()
        mail_row.setSpacing(9)
        ic = QLabel()
        ic.setPixmap(icons.pixmap("mail", 18, acc.primary, 1.8))
        ic.setFixedSize(18, 18)
        mail_row.addWidget(ic, 0, Qt.AlignVCenter)
        mail_row.addWidget(make_label(cfg.DEV_EMAIL, "CardTitle"), 1)
        contact.body.addLayout(mail_row)
        contact.body.addWidget(make_label(
            "Вопросы, сообщения об ошибках и предложения.", "CardBody", wrap=True))
        btns = QHBoxLayout()
        btns.setSpacing(10)
        write = QPushButton("Написать")
        write.setObjectName("Primary")
        write.setFixedHeight(38)
        write.setCursor(Qt.PointingHandCursor)
        write.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(f"mailto:{cfg.DEV_EMAIL}")))
        copy = QPushButton("Копировать адрес")
        copy.setObjectName("Ghost")
        copy.setFixedHeight(38)
        copy.setCursor(Qt.PointingHandCursor)
        copy.clicked.connect(self._copy_mail)
        self._copy_btn = copy
        btns.addWidget(write)
        btns.addWidget(copy)
        btns.addStretch(1)
        contact.body.addLayout(btns)
        contact.body.addStretch(1)
        grid.addWidget(contact, 0, 1)

        legal = GlassCard(padding=20, spacing=10)
        legal.body.addWidget(make_label("ПРАВОВАЯ ИНФОРМАЦИЯ", "CardKicker"))
        legal.body.addWidget(make_label("Пользовательское соглашение", "CardTitle"))
        legal.body.addWidget(make_label(
            "Условия использования программы, ограничения и ответственность сторон.",
            "CardBody", wrap=True))
        open_btn = QPushButton("Открыть соглашение")
        open_btn.setObjectName("Ghost")
        open_btn.setFixedHeight(38)
        open_btn.setCursor(Qt.PointingHandCursor)
        open_btn.clicked.connect(on_show_eula)
        legal.body.addWidget(open_btn, 0, Qt.AlignLeft)
        legal.body.addStretch(1)
        grid.addWidget(legal, 0, 2)

        for i in range(3):
            grid.setColumnStretch(i, 1)
        self.body.addLayout(grid)

        # --- обновления ---
        upd = GlassCard(padding=20, spacing=12, hoverable=False)
        head = QHBoxLayout()
        head.setSpacing(14)
        head.addWidget(OrbIcon("update", 44), 0, Qt.AlignVCenter)
        col_u = QVBoxLayout()
        col_u.setSpacing(2)
        col_u.addWidget(make_label("ОБНОВЛЕНИЯ", "CardKicker"))
        self._upd_title = make_label(
            f"Установлена версия {cfg.APP_VERSION}", "CardTitle")
        self._upd_sub = make_label(
            "Программа проверяет новые версии автоматически раз в час.",
            "Caption")
        col_u.addWidget(self._upd_title)
        col_u.addWidget(self._upd_sub)
        head.addLayout(col_u, 1)
        head.addWidget(OrbIcon("clock", 34), 0, Qt.AlignVCenter)

        self._btn_check = QPushButton("Проверить сейчас")
        self._btn_check.setObjectName("Ghost")
        self._btn_check.setFixedHeight(38)
        self._btn_check.setCursor(Qt.PointingHandCursor)
        if on_check:
            self._btn_check.clicked.connect(lambda: on_check(False))
        head.addWidget(self._btn_check, 0, Qt.AlignVCenter)

        self._btn_install = QPushButton("Обновить")
        self._btn_install.setObjectName("Primary")
        self._btn_install.setFixedHeight(38)
        self._btn_install.setCursor(Qt.PointingHandCursor)
        self._btn_install.setVisible(False)
        if on_update:
            self._btn_install.clicked.connect(on_update)
        head.addWidget(self._btn_install, 0, Qt.AlignVCenter)
        upd.body.addLayout(head)
        self.body.addWidget(upd)

        # --- права доступа ---
        if can_elevate() or is_admin():
            sec = GlassCard(padding=20, spacing=12, hoverable=False)
            r = QHBoxLayout()
            r.setSpacing(14)
            r.addWidget(OrbIcon("admin", 44), 0, Qt.AlignVCenter)
            c = QVBoxLayout()
            c.setSpacing(2)
            c.addWidget(make_label("ПРАВА ДОСТУПА", "CardKicker"))
            c.addWidget(make_label(
                "Запущено от администратора" if is_admin()
                else "Запущено от обычного пользователя", "CardTitle"))
            c.addWidget(make_label(
                "Доступна очистка системных папок Windows." if is_admin()
                else "Часть системного мусора недоступна для очистки.",
                "Caption"))
            r.addLayout(c, 1)
            if can_elevate():
                b = QPushButton("Перезапустить от админа")
                b.setObjectName("Ghost")
                b.setFixedHeight(38)
                b.setCursor(Qt.PointingHandCursor)
                if on_elevate:
                    b.clicked.connect(on_elevate)
                r.addWidget(b, 0, Qt.AlignVCenter)
            sec.body.addLayout(r)
            self.body.addWidget(sec)

        # --- технические сведения ---
        tech = GlassCard(padding=20, spacing=12, hoverable=False)
        tech.body.addWidget(make_label("СВЕДЕНИЯ О СБОРКЕ", "CardKicker"))
        rows = [
            ("Версия", cfg.APP_VERSION),
            ("Сборка", cfg.APP_BUILD),
            ("Канал", cfg.APP_CHANNEL),
            ("Платформа", "Windows · Linux · macOS"),
            ("Файл настроек", str(cfg.SETTINGS_FILE)),
        ]
        for i, (k, v) in enumerate(rows):
            if i:
                tech.body.addWidget(Divider())
            r = QHBoxLayout()
            r.addWidget(make_label(k, "CardBody"))
            r.addStretch(1)
            r.addWidget(make_label(v, "Mono"))
            tech.body.addLayout(r)
        self.body.addWidget(tech)

        self.body.addWidget(make_label(
            f"© {cfg.DEV_YEAR} {cfg.DEV_NAME} Все права защищены.", "Caption"))
        self.body.addStretch(1)

    def on_check_started(self):
        self._btn_check.setEnabled(False)
        self._btn_check.setText("Проверка…")
        self._upd_sub.setText("Связь с сервером обновлений…")

    def on_update_state(self, info: UpdateInfo):
        self._btn_check.setEnabled(True)
        self._btn_check.setText("Проверить сейчас")
        if info and info.available:
            self._upd_title.setText(f"Доступна версия {info.version}")
            self._upd_sub.setText(
                info.title or "Нажмите «Обновить», чтобы установить новую версию.")
            self._btn_install.setVisible(True)
        else:
            self._upd_title.setText(f"Установлена версия {cfg.APP_VERSION}")
            self._upd_sub.setText("Это последняя версия программы.")
            self._btn_install.setVisible(False)

    def _copy_mail(self):
        QGuiApplication.clipboard().setText(cfg.DEV_EMAIL)
        self._copy_btn.setText("Скопировано")
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1600, lambda: self._copy_btn.setText("Копировать адрес"))
