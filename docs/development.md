## Руководство для разработчиков FolderSync

---

### 1. Стек и зависимости

- Язык: **Python 3.10+**
- GUI: `tkinter` (стандартная библиотека)
- Логирование: стандартный `logging` через `logger_config.py`
- Внешних зависимостей нет

---

### 2. Структура проекта

| Файл | Назначение |
|------|-----------|
| `main.py` | Точка входа: логирование, `ConfigManager`, `MainWindow` |
| `logger_config.py` | Обёртка над `logging` с API loguru-стиля |
| `config_manager.py` | `ConfigManager`, `parse_config_line()` |
| `sync_core.py` | `scan_directory`, `should_copy_file`, `sync_pair`, `SyncResult` |
| `ui_main.py` | `MainWindow` — главное окно, многопоточность |
| `ui_settings.py` | `SettingsWindow` — список пар, чекбоксы |

---

### 3. Запуск в режиме разработки

```bash
git clone https://github.com/kabzon93region/FolderSync.git
cd FolderSync
setup_venv.cmd
run_sync.cmd
```

Или вручную:

```bash
venv\Scripts\python.exe main.py
```

---

### 4. Логирование

Логирование настроено в `main.py` через `logger_config.py`:

- Файл: `logs/log.log` с ротацией (25 MB)
- Консоль: INFO и выше (при запуске из терминала)
- Формат: `{time:DD.MM.YYYY HH:mm:ss:(x)} - {level} - {message}`

Использование в модулях:

```python
from logger_config import logger
logger.info("сообщение")
logger.debug("отладка")
logger.error("ошибка")
```

---

### 5. Сборка exe

```bash
build_exe.cmd
```

Результат: `dist/FolderSync.exe`

Требования: `pip install pyinstaller` (в venv или глобально).

---

### 6. Многопоточность

- GUI работает в главном потоке (tkinter не потокобезопасен).
- Синхронизация выполняется в `threading.Thread(daemon=True)`.
- Прогресс/логи: `queue.Queue` → `window.after(50ms)`.
- Остановка: `threading.Event`.
- При закрытии окна поток дожидается завершения (`join(timeout=3)`).
