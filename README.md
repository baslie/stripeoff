# StripeOff

![Пример до и после](https://github.com/baslie/StripeOff/blob/main/before-after.jpg)

**StripeOff** — простое приложение для удаления белых рамок с изображений. Перетащите файлы или папку — программа обработает всё автоматически.

## Возможности

- Drag-and-drop интерфейс
- Поддержка папок (рекурсивная обработка всех изображений)
- Локализация: русский и английский языки
- История обработки с отображением прогресса
- Поддержка форматов: PNG, JPG, JPEG, BMP, WebP

## Как пользоваться

1. Запустите `remove_borders_app.py`
2. Перетащите изображения или папку в окно программы
3. Обработанные файлы сохраняются рядом с оригиналами с суффиксом `_cropped`

![Скриншот приложения](https://github.com/baslie/StripeOff/blob/main/screenshot.jpg)

## Установка

Требуется Python 3.9+

```
pip install -r requirements.txt
```

## Компиляция в EXE

```
pip install pyinstaller
pyinstaller --name StripeOff --onefile --icon=eraser.ico --noconsole remove_borders_app.py
```

Готовый файл будет в папке `dist`.

## Лицензия

MIT
