# StripeOff

![Пример до и после](https://github.com/baslie/StripeOff/blob/main/before-after.jpg)

**StripeOff** — простое приложение для удаления белых рамок с изображений. Перетащите файлы или папку — программа обработает всё автоматически.

## Возможности

- Drag-and-drop интерфейс
- Поддержка папок (рекурсивная обработка всех изображений)
- Локализация: русский и английский языки
- История обработки с отображением прогресса
- Увеличенное окно (640×480) и удобный скролл-бар
- Поддержка форматов: PNG, JPG, JPEG, BMP, WebP

## Как пользоваться

1. Запустите `remove_borders_app.py`
2. Перетащите изображения или папку в окно программы
3. Обработанные файлы сохраняются рядом с оригиналами с суффиксом `_cropped`

![Скриншот приложения](https://github.com/baslie/StripeOff/blob/main/screenshot.jpg)

## Установка

### Вариант 1: Установщик (рекомендуется)

Скачайте `StripeOff_Setup_1.0.0.exe` из [Releases](https://github.com/baslie/StripeOff/releases) и запустите. Установщик создаст ярлыки на рабочем столе и в меню Пуск.

### Вариант 2: Портативная версия

Скачайте `StripeOff.exe` из [Releases](https://github.com/baslie/StripeOff/releases) — запускается без установки.

### Вариант 3: Из исходников

Требуется Python 3.9+

```
pip install -r requirements.txt
python remove_borders_app.py
```

## Сборка

### Портативный EXE

```
pip install pyinstaller
pyinstaller --name StripeOff --onefile --icon=eraser.ico --noconsole remove_borders_app.py
```

### Установщик

Требуется [Inno Setup 6](https://jrsoftware.org/isdl.php).

```
build_installer.bat
```

Результат:
- `dist/StripeOff.exe` — портативная версия
- `dist/StripeOff_Setup_1.0.0.exe` — установщик

## Лицензия

MIT
