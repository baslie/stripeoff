# pyinstaller --name StripeOff --onefile --icon=eraser.ico --noconsole remove_borders_app.py
# Программа не работает с кириллическими названиями изображений и папок. Названия файлов и папок — только на латинице!

import sys
import os

# Подавление предупреждений Qt о несовместимых шрифтах (Noto Display ExtraCondensed и др.)
os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts=false'

import cv2
from PyQt5.QtWidgets import QApplication, QMessageBox, QLabel, QMainWindow
from PyQt5.QtCore import Qt, QObject, QEvent
from PyQt5.QtGui import QFont, QIcon

# Константы
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 400
SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.webp')
ADAPTIVE_THRESHOLD_BLOCK_SIZE = 11
ADAPTIVE_THRESHOLD_C = 2


def resource_path(relative_path: str) -> str:
    """Получить абсолютный путь к ресурсу для PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.dirname(__file__), relative_path)


def remove_borders(image_path: str, output_path: str) -> bool:
    """
    Удаляет белые границы с изображения.

    Args:
        image_path: Путь к исходному изображению
        output_path: Путь для сохранения результата

    Returns:
        True если обработка успешна, False в случае ошибки
    """
    try:
        image = cv2.imread(image_path)

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
        success = cv2.imwrite(output_path, cropped_image)

        return success

    except Exception:
        return False


class DropZoneFilter(QObject):
    """Event filter для обработки drag-and-drop событий."""

    def __init__(self, parent: 'RemoveBordersWindow'):
        super().__init__(parent)
        self.window = parent

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.DragEnter:
            if event.mimeData().hasUrls():
                event.acceptProposedAction()
            return True
        elif event.type() == QEvent.Drop:
            file_paths = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith(SUPPORTED_EXTENSIONS):
                    file_paths.append(file_path)
            if file_paths:
                self.window.process_images(file_paths)
            return True
        return False


class RemoveBordersWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Remove White Borders')
        self.setWindowIcon(QIcon(resource_path('eraser.ico')))
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet('background-color: #333; color: white;')

        self.drop_zone = QLabel('<p style="line-height: 1.5;">Drag and drop images here</p>', self)
        self.drop_zone.setGeometry(10, 40, 780, 200)
        self.drop_zone.setStyleSheet('background-color: #444; color: white; border: 2px dashed #666; font-size: 18px;')
        self.drop_zone.setAlignment(Qt.AlignCenter)
        self.drop_zone.setAcceptDrops(True)

        self.drop_filter = DropZoneFilter(self)
        self.drop_zone.installEventFilter(self.drop_filter)

        self.warning_label = QLabel(
            '<p style="line-height: 1.5;">'
            'The program does not work with Cyrillic image and folder names.<br/>'
            'File and folder names must be in Latin characters only!'
            '</p>',
            self
        )
        self.warning_label.setStyleSheet('color: white; font-size: 14px;')
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setWordWrap(True)
        self.warning_label.setGeometry(0, 0, self.width(), self.warning_label.sizeHint().height())
        self.warning_label.move(
            (self.width() - self.warning_label.width()) // 2,
            self.height() - self.warning_label.height() - 10
        )

    def process_images(self, file_paths: list[str]) -> None:
        """Обрабатывает список изображений."""
        success_count = 0
        failed_files = []

        for image_path in file_paths:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_cropped{ext}"

            if remove_borders(image_path, output_path):
                success_count += 1
            else:
                failed_files.append(os.path.basename(image_path))

        self.show_result_popup(success_count, failed_files)

    def show_result_popup(self, success_count: int, failed_files: list[str]) -> None:
        """Показывает результат обработки."""
        popup = QMessageBox(self)
        popup.setStyleSheet('font-size: 14px;')

        if failed_files:
            popup.setIcon(QMessageBox.Warning)
            popup.setWindowTitle('Processing Complete')
            failed_list = '<br/>'.join(failed_files[:5])
            if len(failed_files) > 5:
                failed_list += f'<br/>... and {len(failed_files) - 5} more'
            popup.setText(
                f'<p style="line-height: 1.5;">'
                f'Successfully processed: {success_count}<br/>'
                f'Failed: {len(failed_files)}<br/><br/>'
                f'Failed files:<br/>{failed_list}'
                f'</p>'
            )
        else:
            popup.setIcon(QMessageBox.Information)
            popup.setWindowTitle('Done')
            popup.setText(f'<p style="line-height: 1.5;">Successfully processed {success_count} image(s)!</p>')

        popup.exec_()


if __name__ == '__main__':
    app = QApplication([])
    app.setFont(QFont('Segoe UI', 9))
    remove_borders_window = RemoveBordersWindow()
    remove_borders_window.show()
    app.exec_()
