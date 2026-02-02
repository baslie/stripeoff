# StripeOff

![Before and after example](https://github.com/baslie/StripeOff/blob/main/before-after.jpg)

**StripeOff** — a simple application for removing white borders from images. Drag and drop files or a folder — the program will process everything automatically.

## Features

- Drag-and-drop interface
- Folder support (recursive processing of all images)
- Localization: Russian and English
- Processing history with progress display
- Supported formats: PNG, JPG, JPEG, BMP, WebP

## How to Use

1. Run `remove_borders_app.py`
2. Drag images or a folder into the program window
3. Processed files are saved next to the originals with the `_cropped` suffix

![Application screenshot](https://github.com/baslie/StripeOff/blob/main/screenshot.jpg)

## Installation

### Option 1: Installer (recommended)

Download `StripeOff_Setup_1.0.0.exe` from [Releases](https://github.com/baslie/StripeOff/releases) and run it. The installer will create shortcuts on the desktop and in the Start menu.

### Option 2: Portable version

Download `StripeOff.exe` from [Releases](https://github.com/baslie/StripeOff/releases) — runs without installation.

### Option 3: From source

Requires Python 3.9+

```
pip install -r requirements.txt
python remove_borders_app.py
```

## Building

### Portable EXE

```
pip install pyinstaller
pyinstaller StripeOff.spec
```

### Installer

Requires [Inno Setup 6](https://jrsoftware.org/isdl.php).

```
build_installer.bat
```

Output:
- `dist/StripeOff.exe` — portable version
- `dist/StripeOff_Setup_1.0.0.exe` — installer

## License

MIT
