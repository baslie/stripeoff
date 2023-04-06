# pyinstaller --name StripeOff --onefile --icon=eraser.ico --noconsole remove_borders_app.py
# Программа не работает с кириллическими названиями изображений и папок. Названия файлов и папок — только на латинице!

import cv2
import os
from PyQt5.QtWidgets import QApplication, QMessageBox, QLabel, QLineEdit, QPushButton, QFileDialog, QVBoxLayout, QMainWindow
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

class RemoveBordersWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Remove White Borders')
        self.setWindowIcon(QIcon('eraser.ico'))
        self.setFixedSize(800, 400)
        self.setStyleSheet('background-color: #333; color: white;')

        self.drop_zone = QLabel('Drag and drop images here', self)
        self.drop_zone.setGeometry(10, 40, 780, 200)
        self.drop_zone.setStyleSheet('background-color: #444; color: white; border: 2px dashed #666;')
        self.drop_zone.setAlignment(Qt.AlignCenter)
        self.drop_zone.setAcceptDrops(True)
        self.drop_zone.dragEnterEvent = self.dragEnterEvent
        self.drop_zone.dropEvent = self.dropEvent

        self.warning_label = QLabel('The program does not work with Cyrillic image and folder names.<br/>File and folder names must be in Latin characters only!', self)
        self.warning_label.setStyleSheet('color: white;')
        self.warning_label.setAlignment(Qt.AlignCenter)
        self.warning_label.setWordWrap(True)
        self.warning_label.setGeometry(0, 0, self.width(), self.warning_label.sizeHint().height())
        self.warning_label.move((self.width() - self.warning_label.width()) // 2, self.height() - self.warning_label.height() - 10)

    def process_images(self, file_paths):
        for image_path in file_paths:
            output_path = image_path.split('.')[0] + '_cropped.jpg'
            remove_borders(image_path, output_path)
        self.success_popup()

    def success_popup(self):
        popup = QMessageBox()
        popup.setWindowTitle('Done')
        popup.setText('Image processing completed!')
        popup.exec_()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        file_paths = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.endswith('.png') or file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
                file_paths.append(file_path)
        self.process_images(file_paths)

def remove_borders(image_path, output_path):
    image = cv2.imread(image_path)
    
    # Check if the image exists
    if image is None:
        print(f"Failed to read image file: {image_path}")
        return
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Apply adaptive threshold
    adaptive_thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # Morphological operations: closing to fill small gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    closed = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
    
    # Find contours
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
    cropped_image = image[y:y+h, x:x+w]
    cv2.imwrite(image_path, cropped_image)


if __name__ == '__main__':
    app = QApplication([])
    remove_borders_window = RemoveBordersWindow()
    remove_borders_window.show()
    app.exec_()