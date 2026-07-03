# FolderSync

Настольное приложение на Python/tkinter для синхронизации (резервного копирования) содержимого папок по настраиваемому списку пар каталогов.

## Возможности

- Синхронизация папок с сохранением структуры каталогов
- Копирование только новых и изменённых файлов (по дате изменения `mtime`)
- Маски исключений для файлов и папок (`*.tmp`, `__pycache__`, `cache/*`)
- Включение/отключение отдельных пар без удаления из списка
- Опциональное удаление исходных файлов после синхронизации
- Подробное логирование в файл с ротацией
- GUI на tkinter с прогресс-баром и окном настроек
- Многопоточность: GUI в главном потоке, синхронизация в фоновом

## Требования

- **Python** 3.10+
- **ОС** Windows
- **Зависимости**: нет (только стандартная библиотека Python)

## Установка и запуск

### Готовый exe (рекомендуется)

Скачайте `FolderSync.exe` из [Releases](https://github.com/kabzon93region/FolderSync/releases) — Python не требуется.

### Из исходников

1. Склонируйте репозиторий:

```bash
git clone https://github.com/kabzon93region/FolderSync.git
cd FolderSync
```

2. Запустите `setup_venv.cmd` — создаст виртуальное окружение.

3. Запустите приложение:
   - `run_sync.cmd` — с консолью (для отладки)
   - `run_sync_silent.cmd` — без консоли

### Ручной запуск

```bash
venv\Scripts\python.exe main.py
```

## Конфигурация

Файл `config.cfg` содержит пары папок для синхронизации. Формат:

```text
<ИСТОЧНИК> ===>>> <НАЗНАЧЕНИЕ>
<ИСТОЧНИК> ===>>> <НАЗНАЧЕНИЕ> | EXCLUDE: *.tmp;*.log;__pycache__
[ACTIVE] <ИСТОЧНИК> ===>>> <НАЗНАЧЕНИЕ>
[INACTIVE] <ИСТОЧНИК> ===>>> <НАЗНАЧЕНИЕ> | EXCLUDE: cache/*
```

Пример:

```text
D:\Downloads ===>>> E:\Archive\Downloads
[ACTIVE] Z:\USB\DriverPack ===>>> D:\USB\DriverPack | EXCLUDE: cache;tmp;temp;~
[INACTIVE] T:\FileExchanger ===>>> Z:\T\FileExchanger | EXCLUDE: .git;venv
```

Настройки можно менять через GUI (кнопка "Настройки") или вручную в файле.

## Структура проекта

```
main.py              # Точка входа
logger_config.py     # Логирование (стандартный logging)
config_manager.py    # Загрузка/сохранение config.cfg
sync_core.py         # Ядро синхронизации
ui_main.py           # Главное окно (многопоточность)
ui_settings.py       # Окно настроек
requirements.txt     # Зависимости (пусто — только stdlib)
config.cfg           # Конфигурация (не в репозитории)
setup_venv.cmd       # Создание venv
run_sync.cmd         # Запуск с консолью
run_sync_silent.cmd  # Запуск без консоли
build_exe.cmd        # Сборка exe через PyInstaller
```

## Лицензия

MIT
