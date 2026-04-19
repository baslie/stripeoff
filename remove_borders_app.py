# pyinstaller --name StripeOff --onefile --icon=eraser.ico --noconsole remove_borders_app.py

import sys
import os

# Подавление предупреждений Qt о несовместимых шрифтах
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts=false'

import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QLabel, QMainWindow, QPushButton, QCheckBox,
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QObject, QEvent, QSettings, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from enum import Enum
from queue import Queue


class ProcessResult(Enum):
    SUCCESS = "success"   # Обрезано и сохранено
    SKIPPED = "skipped"   # Белых рамок нет
    ERROR = "error"       # Ошибка обработки


class ImageProcessorWorker(QThread):
    """Рабочий поток для обработки изображений."""
    file_processed = pyqtSignal(int, object, str)  # widget_id, result, output_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_queue = Queue()
        self._running = True

    def add_task(self, widget_id: int, path: str, output_path: str, output_name: str):
        """Добавить задачу в очередь."""
        self.task_queue.put((widget_id, path, output_path, output_name))

    def run(self):
        """Обработка задач из очереди."""
        while self._running:
            try:
                task = self.task_queue.get(timeout=0.1)
            except:
                continue

            widget_id, path, output_path, output_name = task
            result = remove_borders(path, output_path)
            self.file_processed.emit(widget_id, result, output_name)

    def stop(self):
        """Остановить рабочий поток."""
        self._running = False
        self.wait()


# Константы
WINDOW_WIDTH = 640
WINDOW_HEIGHT = 480
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
WHITE_THRESHOLD = 250  # Пиксель считается белым если все каналы >= 250
ALPHA_THRESHOLD = 5    # Пиксель считается прозрачным если alpha <= 5
MIN_BORDER_WIDTH = 5   # Минимальная ширина рамки для обрезки (в пикселях)

# Локализация
TRANSLATIONS = {
    'en': {
        'window_title': 'Remove White Borders',
        'app_name': 'StripeOff',
        'app_description': 'Remove white borders from images',
        'drop_hint': 'Drag and drop images or folder here',
        'no_borders': 'No borders detected',
        'overwritten': 'overwritten',
        'overwrite_label': 'Overwrite originals',
        'overwrite_tooltip': 'Originals are replaced with cropped versions (cannot be undone). When off — copies are saved with the _cropped suffix.',
    },
    'ru': {
        'window_title': 'Удаление белых рамок',
        'app_name': 'StripeOff',
        'app_description': 'Удаление белых рамок с изображений',
        'drop_hint': 'Перетащите изображения или папку сюда',
        'no_borders': 'Рамки не обнаружены',
        'overwritten': 'перезаписан',
        'overwrite_label': 'Перезаписывать оригиналы',
        'overwrite_tooltip': 'Оригиналы заменяются обрезанными версиями (нельзя отменить). Когда выключено — сохраняются копии с суффиксом _cropped.',
    }
}


def resource_path(relative_path: str) -> str:
    """Получить абсолютный путь к ресурсу для PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)


def _build_empty_mask(image: np.ndarray) -> np.ndarray:
    """Вернуть 2D-маску, где True — пиксель «пустой» (прозрачный или белый)."""
    if image.ndim == 3 and image.shape[2] == 4:
        alpha = image[:, :, 3]
        bgr = image[:, :, :3]
        return (alpha <= ALPHA_THRESHOLD) | np.all(bgr >= WHITE_THRESHOLD, axis=2)
    if image.ndim == 3:
        return np.all(image >= WHITE_THRESHOLD, axis=2)
    return image >= WHITE_THRESHOLD


def remove_borders(image_path: str, output_path: str) -> ProcessResult:
    """Удаляет пустые (прозрачные или белые) границы с изображения."""
    try:
        image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
        if image is None:
            return ProcessResult.ERROR

        h, w = image.shape[:2]
        empty_mask = _build_empty_mask(image)

        rows_all_empty = np.all(empty_mask, axis=1)
        non_empty_rows = np.where(~rows_all_empty)[0]
        if non_empty_rows.size == 0:
            return ProcessResult.SKIPPED

        top = int(non_empty_rows[0])
        bottom = int(non_empty_rows[-1]) + 1

        cols_all_empty = np.all(empty_mask, axis=0)
        non_empty_cols = np.where(~cols_all_empty)[0]
        left = int(non_empty_cols[0])
        right = int(non_empty_cols[-1]) + 1

        has_significant_border = (
            top >= MIN_BORDER_WIDTH or
            (h - bottom) >= MIN_BORDER_WIDTH or
            left >= MIN_BORDER_WIDTH or
            (w - right) >= MIN_BORDER_WIDTH
        )

        if not has_significant_border:
            return ProcessResult.SKIPPED

        cropped = image[top:bottom, left:right]

        ext = os.path.splitext(output_path)[1]
        is_success, im_buf = cv2.imencode(ext, cropped)
        if is_success:
            im_buf.tofile(output_path)
            return ProcessResult.SUCCESS
        return ProcessResult.ERROR

    except Exception:
        return ProcessResult.ERROR


def collect_images_from_paths(paths: list[str]) -> list[str]:
    """Собрать все изображения из списка путей (файлы и папки)."""
    images = []
    for path in paths:
        if os.path.isdir(path):
            # Рекурсивно собираем изображения из папки
            for root, _, files in os.walk(path):
                for file in files:
                    if file.lower().endswith(SUPPORTED_EXTENSIONS):
                        images.append(os.path.join(root, file))
        elif path.lower().endswith(SUPPORTED_EXTENSIONS):
            images.append(path)
    return images


class FileItemWidget(QFrame):
    """Виджет для отображения одного обработанного файла."""
    _next_id = 0  # Статический счётчик для уникальных ID

    def __init__(self, original_name: str, parent=None):
        super().__init__(parent)
        self.widget_id = FileItemWidget._next_id
        FileItemWidget._next_id += 1
        self.original_name = original_name
        self.setStyleSheet('''
            FileItemWidget {
                background-color: #3a3a3a;
                border-radius: 6px;
            }
        ''')
        self.setFixedHeight(44)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 8)
        layout.setSpacing(12)

        # Иконка/спиннер
        self.status_label = QLabel('⏳')
        self.status_label.setStyleSheet('font-size: 18px;')
        self.status_label.setFixedWidth(26)
        layout.addWidget(self.status_label)

        # Имя файла
        self.name_label = QLabel(original_name)
        self.name_label.setStyleSheet('color: #bbb; font-size: 16px;')
        layout.addWidget(self.name_label)

        # Стрелка (скрыта изначально)
        self.arrow_label = QLabel('→')
        self.arrow_label.setStyleSheet('color: #777; font-size: 16px;')
        self.arrow_label.hide()
        layout.addWidget(self.arrow_label)

        # Новое имя (скрыто изначально)
        self.new_name_label = QLabel('')
        self.new_name_label.setStyleSheet('color: #7a7; font-size: 16px;')
        self.new_name_label.hide()
        layout.addWidget(self.new_name_label)

        layout.addStretch()

        # Анимация спиннера
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner_index = 0
        self.spinner_timer = QTimer(self)
        self.spinner_timer.timeout.connect(self._update_spinner)
        self.spinner_timer.start(80)

    def _update_spinner(self):
        self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
        self.status_label.setText(self.spinner_chars[self.spinner_index])

    def set_success(self, new_name: str):
        """Установить статус успешной обработки (копия с новым именем)."""
        self.spinner_timer.stop()
        self.status_label.setText('✓')
        self.status_label.setStyleSheet('color: #7a7; font-size: 18px;')
        self.arrow_label.show()
        self.new_name_label.setText(new_name)
        self.new_name_label.show()

    def set_overwritten(self, label: str):
        """Установить статус успешной перезаписи оригинала."""
        self.spinner_timer.stop()
        self.status_label.setText('✓')
        self.status_label.setStyleSheet('color: #7a7; font-size: 18px;')
        self.new_name_label.setText(f'({label})')
        self.new_name_label.setStyleSheet('color: #7a7; font-size: 14px; font-style: italic;')
        self.new_name_label.show()

    def set_error(self):
        """Установить статус ошибки."""
        self.spinner_timer.stop()
        self.status_label.setText('✗')
        self.status_label.setStyleSheet('color: #a77; font-size: 18px;')
        self.name_label.setStyleSheet('color: #a77; font-size: 16px;')

    def set_skipped(self, message: str):
        """Установить статус пропуска (нет белых рамок)."""
        self.spinner_timer.stop()
        self.status_label.setText('○')
        self.status_label.setStyleSheet('color: #aa7; font-size: 18px;')
        self.arrow_label.setText('—')
        self.arrow_label.setStyleSheet('color: #777; font-size: 16px;')
        self.arrow_label.show()
        self.new_name_label.setText(message)
        self.new_name_label.setStyleSheet('color: #aa7; font-size: 16px;')
        self.new_name_label.show()


class DropEventFilter(QObject):
    """Event filter для обработки drag-and-drop на всём окне."""

    def __init__(self, parent: 'RemoveBordersWindow'):
        super().__init__(parent)
        self.window = parent

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.DragEnter:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
                self.window.on_drag_enter()
            return True
        elif event.type() == QEvent.DragLeave:
            self.window.on_drag_leave()
            return True
        elif event.type() == QEvent.Drop:
            self.window.on_drag_leave()
            paths = [url.toLocalFile() for url in event.mimeData().urls()]
            images = collect_images_from_paths(paths)
            if images:
                self.window.process_images(images)
            return True
        return False


class RemoveBordersWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('StripeOff', 'StripeOff')
        self.current_lang = self.settings.value('language', 'ru')
        self.overwrite_originals = self.settings.value('overwrite_originals', False, type=bool)
        self.file_widgets = []
        self.widget_registry = {}  # widget_id -> FileItemWidget
        self.overwrite_registry = {}  # widget_id -> bool (был ли файл перезаписан)
        self.worker = None
        self.has_processed = False  # Флаг: были ли уже обработаны файлы

        self.setWindowIcon(QIcon(resource_path('eraser.ico')))
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setAcceptDrops(True)

        # Центральный виджет
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.central.setAcceptDrops(True)
        self.central.setStyleSheet('background-color: #333;')

        main_layout = QVBoxLayout(self.central)
        main_layout.setContentsMargins(20, 15, 20, 20)
        main_layout.setSpacing(0)

        # Верхняя панель: чекбокс режима перезаписи + кнопка языка
        top_bar = QHBoxLayout()
        top_bar.setSpacing(12)
        top_bar.addStretch()

        self.overwrite_checkbox = QCheckBox()
        self.overwrite_checkbox.setChecked(self.overwrite_originals)
        self.overwrite_checkbox.setCursor(Qt.PointingHandCursor)
        self.overwrite_checkbox.setStyleSheet('''
            QCheckBox {
                color: #888;
                font-size: 12px;
                spacing: 6px;
            }
            QCheckBox:hover {
                color: #ccc;
            }
            QCheckBox:checked {
                color: #e8a070;
            }
            QCheckBox::indicator {
                width: 14px;
                height: 14px;
                border-radius: 3px;
                background-color: #3a3a3a;
                border: 1px solid #555;
            }
            QCheckBox::indicator:hover {
                background-color: #4a4a4a;
                border: 1px solid #777;
            }
            QCheckBox::indicator:checked {
                background-color: #c07040;
                border: 1px solid #d08050;
            }
            QCheckBox::indicator:checked:hover {
                background-color: #d08050;
            }
        ''')
        self.overwrite_checkbox.toggled.connect(self.on_mode_toggled)
        top_bar.addWidget(self.overwrite_checkbox)

        self.lang_button = QPushButton()
        self.lang_button.setFixedSize(40, 22)
        self.lang_button.setStyleSheet('''
            QPushButton {
                background-color: #444;
                color: #999;
                border: none;
                border-radius: 3px;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #555;
                color: #ccc;
            }
        ''')
        self.lang_button.clicked.connect(self.toggle_language)
        top_bar.addWidget(self.lang_button)
        main_layout.addLayout(top_bar)

        # Приветственный экран (показывается изначально)
        self.welcome_widget = QWidget()
        welcome_layout = QVBoxLayout(self.welcome_widget)
        welcome_layout.setContentsMargins(0, 40, 0, 0)
        welcome_layout.setSpacing(8)
        welcome_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

        self.title_label = QLabel()
        self.title_label.setStyleSheet('color: #ddd; font-size: 42px; font-weight: bold;')
        self.title_label.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(self.title_label)

        self.desc_label = QLabel()
        self.desc_label.setStyleSheet('color: #888; font-size: 18px;')
        self.desc_label.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(self.desc_label)

        welcome_layout.addSpacing(40)

        self.hint_icon = QLabel('⇣')
        self.hint_icon.setStyleSheet('color: #555; font-size: 48px;')
        self.hint_icon.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(self.hint_icon)

        self.hint_label = QLabel()
        self.hint_label.setStyleSheet('color: #666; font-size: 16px;')
        self.hint_label.setAlignment(Qt.AlignCenter)
        welcome_layout.addWidget(self.hint_label)

        main_layout.addWidget(self.welcome_widget, 1)

        # Прокручиваемая область для списка файлов (скрыта изначально)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet('''
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background-color: #3a3a3a;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        ''')
        self.scroll_area.hide()

        self.files_container = QWidget()
        self.files_container.setStyleSheet('background-color: transparent;')
        self.files_layout = QVBoxLayout(self.files_container)
        self.files_layout.setContentsMargins(0, 0, 0, 0)
        self.files_layout.setSpacing(4)
        self.files_layout.addStretch()

        self.scroll_area.setWidget(self.files_container)
        main_layout.addWidget(self.scroll_area, 1)

        # Event filter для drag-and-drop
        self.drop_filter = DropEventFilter(self)
        self.central.installEventFilter(self.drop_filter)

        self.update_ui_texts()

    def tr(self, key: str) -> str:
        """Получить перевод по ключу."""
        return TRANSLATIONS[self.current_lang].get(key, key)

    def toggle_language(self) -> None:
        """Переключить язык интерфейса."""
        self.current_lang = 'en' if self.current_lang == 'ru' else 'ru'
        self.settings.setValue('language', self.current_lang)
        self.update_ui_texts()

    def on_mode_toggled(self, checked: bool) -> None:
        """Переключить режим: создавать копии или перезаписывать оригиналы."""
        self.overwrite_originals = checked
        self.settings.setValue('overwrite_originals', checked)
        self.update_ui_texts()

    def update_ui_texts(self) -> None:
        """Обновить все тексты интерфейса."""
        self.setWindowTitle(self.tr('window_title'))
        self.title_label.setText(self.tr('app_name'))
        self.desc_label.setText(self.tr('app_description'))
        self.hint_label.setText(self.tr('drop_hint'))
        self.lang_button.setText(self.current_lang.upper())
        self.overwrite_checkbox.setText(self.tr('overwrite_label'))
        self.overwrite_checkbox.setToolTip(self.tr('overwrite_tooltip'))

    def on_drag_enter(self):
        """Подсветка при перетаскивании."""
        self.central.setStyleSheet('background-color: #3a4a3a;')

    def on_drag_leave(self):
        """Убрать подсветку."""
        self.central.setStyleSheet('background-color: #333;')

    def process_images(self, file_paths: list[str]) -> None:
        """Добавить изображения в очередь обработки."""
        # Скрыть приветствие, показать список
        if not self.has_processed:
            self.has_processed = True
            self.welcome_widget.hide()
            self.scroll_area.show()

        # Создать worker при первом вызове
        if self.worker is None:
            self.worker = ImageProcessorWorker(self)
            self.worker.file_processed.connect(self._on_file_processed)
            self.worker.start()

        overwrite = self.overwrite_originals
        for path in file_paths:
            original_name = os.path.basename(path)
            widget = FileItemWidget(original_name)
            self.files_layout.insertWidget(self.files_layout.count() - 1, widget)
            self.file_widgets.append(widget)

            # Регистрация и добавление задачи
            self.widget_registry[widget.widget_id] = widget
            self.overwrite_registry[widget.widget_id] = overwrite
            if overwrite:
                output_path = path
                output_name = original_name
            else:
                base, ext = os.path.splitext(path)
                output_path = f"{base}_cropped{ext}"
                output_name = os.path.basename(output_path)
            self.worker.add_task(widget.widget_id, path, output_path, output_name)

        # Прокрутка вниз
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _on_file_processed(self, widget_id: int, result: ProcessResult, output_name: str):
        """Обработать результат от worker'а."""
        widget = self.widget_registry.get(widget_id)
        if widget is None:
            return

        was_overwrite = self.overwrite_registry.pop(widget_id, False)
        if result == ProcessResult.SUCCESS:
            if was_overwrite:
                widget.set_overwritten(self.tr('overwritten'))
            else:
                widget.set_success(output_name)
        elif result == ProcessResult.SKIPPED:
            widget.set_skipped(self.tr('no_borders'))
        else:
            widget.set_error()

    def closeEvent(self, event):
        """Корректно останавливаем worker при закрытии."""
        if self.worker is not None:
            self.worker.stop()
        event.accept()


if __name__ == '__main__':
    app = QApplication([])
    app.setFont(QFont('Segoe UI', 9))
    window = RemoveBordersWindow()
    window.show()
    app.exec_()
