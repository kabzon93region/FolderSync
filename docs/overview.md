## Обзор и архитектура FolderSync

FolderSync — настольное приложение на Python/tkinter для синхронизации папок по списку пар из `config.cfg`.

---

### Основные компоненты

1. **Точка входа (`main.py`)**:
   - инициализация логирования;
   - создание `ConfigManager`;
   - запуск главного окна.

2. **Логирование (`logger_config.py`)**:
   - обёртка над стандартным `logging` с API, совместимым с loguru;
   - ротация логов по размеру (25 MB);
   - формат: `{time:DD.MM.YYYY HH:mm:ss:(x)} - {level} - {message}`.

3. **Модуль конфигурации (`config_manager.py`)**:
   - `ConfigManager`: загрузка/сохранение `config.cfg`;
   - `parse_config_line()`: парсинг строк с поддержкой `[ACTIVE]`/`[INACTIVE]` и `| EXCLUDE:`.

4. **Ядро синхронизации (`sync_core.py`)**:
   - `scan_directory()` — рекурсивное сканирование с исключениями;
   - `should_copy_file()` — сравнение по `mtime`;
   - `sync_pair()` — полный цикл синхронизации одной пары.

5. **Главное окно (`ui_main.py`)**:
   - `MainWindow` — GUI с прогресс-баром и логом;
   - синхронизация в `threading.Thread`, прогресс через `queue.Queue` + `window.after()`.

6. **Окно настроек (`ui_settings.py`)**:
   - `SettingsWindow` — редактирование списка пар с чекбоксами активности.

---

### Поток работы

1. Запуск `main.py` → логирование → `ConfigManager` → `MainWindow`.
2. Пользователь настраивает пары через «Настройки».
3. Нажатие «Старт» → рабочий поток выполняет `sync_pair()` для каждой активной пары.
4. Прогресс и логи доставляются в GUI через очередь.
5. Завершение → итоговое сообщение.

---

### Потокобезопасность

- GUI (tkinter) — главный поток.
- Синхронизация (`sync_pair`) — `threading.Thread(daemon=True)`.
- Обратная связь: `queue.Queue` → `window.after(50ms)`.
- Остановка: `threading.Event`.
