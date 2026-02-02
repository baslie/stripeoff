# pyinstaller --name StripeOff --onefile --icon=eraser.ico --noconsole remove_borders_app.py

import sys
import os

# Подавление предупреждений Qt о несовместимых шрифтах
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts=false'

import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QLabel, QMainWindow, QPushButton,
    QVBoxLayout, QHBoxLayout, QWidget, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QObject, QEvent, QSettings, QTimer
from PyQt5.QtGui import QFont, QIcon

# Константы
WINDOW_WIDTH = 520
WINDOW_HEIGHT = 380
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
ADAPTIVE_THRESHOLD_BLOCK_SIZE = 11
ADAPTIVE_THRESHOLD_C = 2

# Локализация
TRANSLATIONS = {
    'en': {
        'window_title': 'Remove White Borders',
        'app_name': 'StripeOff',
        'app_description': 'Remove white borders from images',
        'drop_hint': 'Drag and drop images or folder here',
    },
    'ru': {
        'window_title': 'Удаление белых рамок',
        'app_name': 'StripeOff',
        'app_description': 'Удаление белых рамок с изображений',
        'drop_hint': 'Перетащите изображения или папку сюда',
    }
}


def resource_path(relative_path: str) -> str:
    """Получить абсолютный путь к ресурсу для PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)


def remove_borders(image_path: str, output_path: str) -> bool:
    """Удаляет белые границы с изображения."""
    try:
        image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            return False

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_MEAN_C,
            cv2.THRESH_BINARY_INV,
            ADAPTIVE_THRESHOLD_BLOCK_SIZE,
            ADAPTIVE_THRESHOLD_C
        )

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        closed = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        max_area = 0
        max_rect = (0, 0, 0, 0)
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            if area > max_area:
                max_area = area
                max_rect = (x, y, w, h)

        x, y, w, h = max_rect
        if w == 0 or h == 0:
            return False

        cropped_image = image[y:y+h, x:x+w]
        ext = os.path.splitext(output_path)[1]
        is_success, im_buf = cv2.imencode(ext, cropped_image)
        if is_success:
            im_buf.tofile(output_path)
        return is_success

    except Exception:
        return False


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

    def __init__(self, original_name: str, parent=None):
        super().__init__(parent)
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
        """Установить статус успешной обработки."""
        self.spinner_timer.stop()
        self.status_label.setText('✓')
        self.status_label.setStyleSheet('color: #7a7; font-size: 18px;')
        self.arrow_label.show()
        self.new_name_label.setText(new_name)
        self.new_name_label.show()

    def set_error(self):
        """Установить статус ошибки."""
        self.spinner_timer.stop()
        self.status_label.setText('✗')
        self.status_label.setStyleSheet('color: #a77; font-size: 18px;')
        self.name_label.setStyleSheet('color: #a77; font-size: 16px;')


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
        self.file_widgets = []
        self.processing_queue = []
        self.is_processing = False
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

        # Верхняя панель с кнопкой языка
        top_bar = QHBoxLayout()
        top_bar.addStretch()
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
                width: 6px;
                border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 3px;
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

    def update_ui_texts(self) -> None:
        """Обновить все тексты интерфейса."""
        self.setWindowTitle(self.tr('window_title'))
        self.title_label.setText(self.tr('app_name'))
        self.desc_label.setText(self.tr('app_description'))
        self.hint_label.setText(self.tr('drop_hint'))
        self.lang_button.setText(self.current_lang.upper())

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

        for path in file_paths:
            original_name = os.path.basename(path)
            widget = FileItemWidget(original_name)
            self.files_layout.insertWidget(self.files_layout.count() - 1, widget)
            self.file_widgets.append(widget)
            self.processing_queue.append((path, widget))

        # Прокрутка вниз
        QTimer.singleShot(50, self._scroll_to_bottom)

        # Запуск обработки
        if not self.is_processing:
            self._process_next()

    def _scroll_to_bottom(self):
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _process_next(self):
        """Обработать следующий файл в очереди."""
        if not self.processing_queue:
            self.is_processing = False
            return

        self.is_processing = True
        path, widget = self.processing_queue.pop(0)

        # Небольшая задержка для визуального эффекта
        QTimer.singleShot(50, lambda: self._do_process(path, widget))

    def _do_process(self, path: str, widget: FileItemWidget):
        """Выполнить обработку файла."""
        base, ext = os.path.splitext(path)
        output_path = f"{base}_cropped{ext}"
        output_name = os.path.basename(output_path)

        success = remove_borders(path, output_path)

        if success:
            widget.set_success(output_name)
        else:
            widget.set_error()

        # Обработка следующего файла
        QTimer.singleShot(30, self._process_next)


if __name__ == '__main__':
    app = QApplication([])
    app.setFont(QFont('Segoe UI', 9))
    window = RemoveBordersWindow()
    window.show()
    app.exec_()
