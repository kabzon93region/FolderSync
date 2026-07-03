# Инструкция для следующего чата разработки (ИИ)

---

## 1. Что это за проект

**FolderSync** — настольное приложение на Python **tkinter** для резервного копирования / синхронизации папок по списку пар из `config.cfg`.

- **Язык интерфейса и логов:** русский.
- **ОС:** Windows.
- **Зависимости:** нет (только стандартная библиотека Python).
- **Логирование:** стандартный `logging` через `logger_config.py` (обёртка с API loguru-стиля).

---

## 2. Структура кода

| Файл | Назначение |
|------|------------|
| `main.py` | Точка входа: логирование, `ConfigManager`, `MainWindow` |
| `logger_config.py` | Обёртка над `logging` (`logger = _Logger()`) |
| `config_manager.py` | `ConfigManager`, `parse_config_line()` |
| `sync_core.py` | Сканирование, исключения, `sync_pair`, копирование |
| `ui_main.py` | `MainWindow` — главное окно, многопоточность (thread + queue) |
| `ui_settings.py` | `SettingsWindow` — список пар, чекбоксы активности |

Скрипты: `run_sync.cmd`, `run_sync_silent.cmd`, `setup_venv.cmd`, `build_exe.cmd`.

---

## 3. Ключевая логика

### Формат `config.cfg`

- Строка: `<SOURCE> ===>>> <DEST>` или с `| EXCLUDE: маски`.
- Опционально префикс `[ACTIVE]` / `[INACTIVE]`.
- Без префикса пара активна (обратная совместимость).

### Копирование

- `should_copy_file`: копировать, если файла нет в назначении **или** `mtime` источника новее.

### Многопоточность

- `sync_pair` выполняется в `threading.Thread(daemon=True)`.
- Прогресс: `queue.Queue` → `window.after(50ms)`.
- Остановка: `threading.Event`.

---

## 4. Запуск для проверки

```bash
cd FolderSync
setup_venv.cmd
run_sync.cmd
```

---

## 5. Сборка exe

```bash
pip install pyinstaller
build_exe.cmd
```

Результат: `dist/FolderSync.exe`

---

*Последнее обновление: июль 2026 (v1.0.0 — замена loguru на stdlib, многопоточность, exe-сборка).*
