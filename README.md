# StripeOff

![](https://github.com/baslie/StripeOff/blob/main/before-after.jpg)

StripeOff is a simple Python application that removes white borders from images using a drag-and-drop interface. The application is built with PyQt5 and OpenCV, making it easy for users to process multiple images with just a few clicks.

## How to use

1. Run the `remove_borders_app.py` script.
2. A graphical user interface (GUI) will appear with a drop zone for images.
3. Drag and drop the images you want to remove the white borders from into the drop zone.
4. The application will process the images and save them in the same directory with the suffix "_cropped" added to the original filename.

**Note**: The application does not work with Cyrillic filenames and folder names. Please use Latin characters only for file and folder names.

## Dependencies

- Python 3.6 or later
- OpenCV
- PyQt5

To install the dependencies, run:

```
pip install opencv-python
pip install PyQt5
```

## Compiling with PyInstaller

To compile the script into an executable using PyInstaller, follow these steps:

1. Install PyInstaller:

```
pip install pyinstaller
```

2. Run the following command in the terminal or command prompt:

```
pyinstaller --name StripeOff --onefile --icon=eraser.ico --noconsole remove_borders_app.py
```

The compiled executable will be located in the **`dist`** directory.

## License

This project is released under the MIT License.
