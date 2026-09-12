"""Visual styles and Russian interface strings for the file manager."""

from __future__ import annotations


COLORS: dict[str, str] = {
    "background": "#1a1a2e",
    "surface": "#16213e",
    "accent_surface": "#0f3460",
    "text": "#e0e0e0",
    "muted": "#8a8a8a",
    "accent": "#00adb5",
    "accent_hover": "#00cfd8",
    "error": "#e74c3c",
    "success": "#2ecc71",
    "warning": "#f39c12",
    "border": "#2a2a4a",
    "input": "#111a32",
}


TEXTS: dict[str, str] = {
    "title": "Файловый менеджмент",
    "description": "Инструменты сортировки, поиска и анализа файлов",
    "plugin_name": "Файловый менеджмент",
    "plugin_description": "Сортировка, поиск, дубликаты, переименование и анализ диска",
    "sort": "Сортировка",
    "duplicates": "Дубликаты",
    "rename": "Переименование",
    "space": "Анализ диска",
    "search": "Поиск",
    "ready": "Готово",
    "browse": "Обзор",
    "folder_placeholder": "Выберите папку",
    "include_subfolders": "Включая подпапки",
    "move": "Перемещать",
    "copy": "Копировать",
    "preview": "Предпросмотр",
    "execute": "Выполнить сортировку",
    "cancel": "Отмена",
    "add_rule": "Добавить правило",
    "remove_rule": "Удалить правило",
    "new_category": "Новая категория",
    "category": "Категория",
    "extensions": "Расширения",
    "destination": "Папка назначения",
    "operation_log": "Журнал операций",
    "new_name": "Новое имя",
    "up": "Вверх",
    "search_button": "Искать",
    "query_placeholder": "Имя файла или шаблон *.txt",
    "scan": "Сканировать",
    "refresh": "Обновить",
    "file_name": "Имя",
    "file_path": "Путь",
    "file_size": "Размер",
    "modified": "Изменён",
    "file_type": "Тип",
    "all": "Все",
    "files_only": "Только файлы",
    "folders_only": "Только папки",
    "extension": "Расширение",
    "min_size": "Размер от",
    "max_size": "Размер до",
    "unit": "Единица",
    "content_search": "Искать по содержимому",
    "content_text": "Текст в файле",
    "date_from": "Дата от",
    "date_to": "Дата до",
    "filter_panel": "Фильтры",
    "found": "Найдено {count} файлов за {seconds:.1f} с",
    "confirm_trash": "Удалить в корзину?\n{path}",
    "minimum_size": "Минимальный размер",
    "mark_duplicates": "Отметить все дубликаты",
    "unmark_duplicates": "Снять все отметки",
    "trash_selected": "Удалить отмеченные в корзину",
    "delete_selected": "Удалить отмеченные навсегда",
    "keep_original": "Оригинал — оставить",
    "duplicate_group": "Группа #{number} — {count} файла, {size} каждый",
    "duplicate_summary": "Найдено {groups} групп дубликатов. Можно освободить {size}.",
    "phase_size": "Этап 1/3: Анализ размеров...",
    "phase_partial": "Этап 2/3: Сравнение первых 4 КБ...",
    "phase_full": "Этап 3/3: Полное сравнение файлов...",
    "confirm_duplicates_trash": "Удалить в корзину отмеченные файлы: {count}?",
    "confirm_duplicates_permanent": "Удалить файлы без возможности восстановления: {count}?",
    "deleted_files": "Удалено файлов: {deleted} из {total}",
    "pattern": "Шаблон имени",
    "pattern_hint": "photo_{num:03d}",
    "start_number": "Начало",
    "step": "Шаг",
    "find": "Найти",
    "replace": "Заменить",
    "case": "Регистр",
    "case_keep": "Без изменений",
    "case_upper": "ВЕРХНИЙ",
    "case_lower": "нижний",
    "case_title": "Первая Заглавная",
    "remove_chars": "Удалить символы",
    "rename_button": "Переименовать",
    "undo_rename": "Отменить последнее переименование",
    "rename_preview": "Предпросмотр переименования",
    "loaded_files": "Загружено файлов: {count}",
    "preview_ready": "Предпросмотр готов: {count} файлов",
    "renamed_files": "Переименовано файлов: {count}",
    "conflict": "Обнаружены конфликты имён. Измените шаблон перед продолжением.",
    "no_files": "Файлы не найдены",
    "disk_folder": "Диск или папка",
    "no_extension": "Без расширения",
    "analyzed": "Проанализировано: {path}",
    "summary": "Всего: {total} | Занято: {used} | Свободно: {free}",
    "top_files": "Топ-50 самых больших файлов",
    "type_distribution": "Распределение по типам",
    "name": "Название",
    "size": "Размер",
    "path": "Путь",
    "open": "Открыть файл",
    "open_folder": "Открыть папку с файлом",
    "copy_path": "Копировать путь",
    "delete_trash": "Удалить в корзину",
    "status_error": "Операция завершилась с ошибкой",
    "select_folder": "Выберите папку для работы",
    "nothing_to_do": "Нет файлов для обработки",
    "library_missing": "Библиотека send2trash не установлена",
    "name_occupied": "имя уже занято",
    "processed_files": "Обработано {processed} из {total} файлов",
}


DEFAULT_RULES: list[tuple[str, str, str]] = [
    ("Изображения", ".png .jpg .jpeg .webp .gif .bmp .svg .ico", "Images"),
    ("Видео", ".mp4 .mkv .avi .mov .wmv .flv", "Videos"),
    ("Документы", ".pdf .docx .xlsx .pptx .txt .rtf .odt", "Documents"),
    ("Архивы", ".zip .rar .7z .tar .gz", "Archives"),
    ("Музыка", ".mp3 .flac .wav .ogg .aac", "Music"),
    ("Код", ".py .js .ts .html .css .json .xml .yaml .sql", "Code"),
    ("Установщики", ".exe .msi .deb .dmg .apk", "Installers"),
]


def stylesheet() -> str:
    """Return the complete stylesheet used by the file manager widget."""
    c = COLORS
    return f"""
    QWidget#fileManagerRoot {{
        background-color: {c['background']};
        color: {c['text']};
    }}
    QFrame[fmRole="header"], QFrame[fmRole="sidebar"], QFrame[fmRole="panel"],
    QFrame[fmRole="group"] {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 8px;
    }}
    QFrame[fmRole="header"] {{
        border: none;
        border-bottom: 1px solid {c['border']};
        border-radius: 0px;
    }}
    QFrame[fmRole="sidebar"] {{
        border-top: none;
        border-bottom: none;
        border-left: none;
        border-radius: 0px;
    }}
    QLabel[fmRole="title"] {{
        color: {c['text']};
        font-family: "Segoe UI Semibold";
        font-size: 18pt;
        font-weight: 600;
    }}
    QLabel[fmRole="subtitle"], QLabel[fmRole="muted"] {{
        color: {c['muted']};
    }}
    QLabel[fmRole="section"] {{
        color: {c['text']};
        font-family: "Segoe UI Semibold";
        font-size: 12pt;
        font-weight: 600;
    }}
    QLabel[fmRole="mono"] {{
        color: {c['text']};
        font-family: "Cascadia Code", "Consolas";
        font-size: 9pt;
    }}
    QPushButton[fmRole="nav"] {{
        background-color: transparent;
        color: {c['text']};
        border: none;
        border-left: 3px solid transparent;
        border-radius: 6px;
        padding: 0px 12px;
        text-align: left;
        min-height: 42px;
    }}
    QPushButton[fmRole="nav"]:hover {{
        background-color: {c['accent_surface']};
    }}
    QPushButton[fmRole="nav"][active="true"] {{
        background-color: {c['accent_surface']};
        color: {c['accent']};
        border-left-color: {c['accent']};
    }}
    QPushButton[fmRole="primary"] {{
        background-color: {c['accent']};
        color: #ffffff;
        border: 1px solid {c['accent']};
        border-radius: 6px;
        padding: 7px 14px;
        min-height: 18px;
    }}
    QPushButton[fmRole="primary"]:hover {{
        background-color: {c['accent_hover']};
        border-color: {c['accent_hover']};
    }}
    QPushButton[fmRole="danger"] {{
        color: {c['error']};
        border: 1px solid {c['error']};
        background-color: transparent;
        border-radius: 6px;
        padding: 7px 14px;
    }}
    QPushButton[fmRole="danger"]:hover {{
        background-color: {c['error']};
        color: #ffffff;
    }}
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QDateEdit {{
        background-color: {c['input']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        padding: 6px 9px;
        min-height: 18px;
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus {{
        border-color: {c['accent']};
    }}
    QTableWidget, QListWidget, QTextEdit, QPlainTextEdit {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        border-radius: 6px;
        selection-background-color: {c['accent_surface']};
        selection-color: {c['text']};
    }}
    QHeaderView::section {{
        background-color: {c['accent_surface']};
        color: {c['text']};
        border: none;
        border-bottom: 1px solid {c['border']};
        padding: 7px;
    }}
    QCheckBox, QRadioButton {{
        color: {c['text']};
        spacing: 7px;
        padding: 3px 0px;
    }}
    QCheckBox::indicator, QRadioButton::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {c['border']};
        background-color: transparent;
        border-radius: 4px;
    }}
    QRadioButton::indicator {{
        border-radius: 8px;
    }}
    QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
        background-color: {c['accent']};
        border-color: {c['accent']};
    }}
    QScrollBar:vertical {{
        width: 7px;
        background: transparent;
    }}
    QScrollBar::handle:vertical {{
        background: {c['border']};
        border-radius: 3px;
        min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {c['accent']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ height: 0px; }}
    QProgressBar {{
        background-color: {c['background']};
        border: 1px solid {c['border']};
        border-radius: 4px;
        text-align: center;
        color: {c['text']};
        min-height: 12px;
    }}
    QProgressBar::chunk {{ background-color: {c['accent']}; border-radius: 3px; }}
    QGraphicsView {{
        background-color: {c['surface']};
        border: 1px solid {c['border']};
        border-radius: 6px;
    }}
    QToolTip {{
        background-color: {c['surface']};
        color: {c['text']};
        border: 1px solid {c['border']};
        padding: 5px;
    }}
    """
