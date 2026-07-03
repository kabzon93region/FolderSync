"""
Модуль главного окна приложения.
Содержит класс MainWindow для управления главным интерфейсом.
"""
from datetime import datetime as dt
from pathlib import Path
from loguru import logger
from tkinter import ttk
import tkinter as tk
import shutil
import time

from config_manager import ConfigManager, parse_config_line
from sync_core import sync_pair
from ui_settings import SettingsWindow


class MainWindow:
    """Класс главного окна приложения"""
    
    # Константы стиля
    BG_COLOR = '#1E1F22'
    ACT_BG_COLOR = '#575A63'
    TXT_COLOR = '#B8BAC0'
    ACT_TXT_COLOR = '#15161A'
    TITLE = "FolderSync"
    ICON_PATH = "./main.ico"
    FONT = ('Consolas', 10)
    WINDOW_WIDTH = 640
    WINDOW_HEIGHT = 300
    
    def __init__(self, config_manager: ConfigManager):
        """
        Инициализация главного окна.
        
        Args:
            config_manager: Экземпляр ConfigManager для работы с конфигурацией
        """
        self.config_manager = config_manager
        self.is_syncing = False
        self.should_stop = False
        
        # Создание главного окна
        self.window = tk.Tk()
        self._setup_window()
        
        # Создание элементов интерфейса
        self._create_widgets()
        
        # Ссылка на окно настроек (будет создано при открытии)
        self.settings_window = None
    
    def _setup_window(self):
        """Настройка параметров окна"""
        xspos = (self.window.winfo_screenwidth() - self.WINDOW_WIDTH) / 2
        yspos = (self.window.winfo_screenheight() - self.WINDOW_HEIGHT) / 2
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self.window.title(self.TITLE)
        self.window.geometry("%dx%d+%d+%d" % (self.WINDOW_WIDTH, self.WINDOW_HEIGHT, xspos, yspos))
        self.window.resizable(False, False)
        
        try:
            self.window.iconbitmap(self.ICON_PATH)
        except:
            logger.error(f"не найден файл иконки в папке запуска программы {Path(self.ICON_PATH).absolute()}")
        
        self.window.config(bg=self.BG_COLOR)
        
        for i in range(5):
            self.window.grid_rowconfigure(i, minsize=60)
            if i <= 5:
                self.window.grid_columnconfigure(i, minsize=128)
    
    def _create_widgets(self):
        """Создание элементов интерфейса"""
        # Текстовая область для логов
        self.textarea = tk.Text(
            self.window,
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            font=self.FONT,
            height=1
        )
        self.textarea.grid(row=2, column=0, sticky='nwes', columnspan=5, rowspan=3)
        
        # Чекбокс удаления файлов
        self.deleting = tk.BooleanVar()
        self.deleting.set(False)
        deleting_checkbutton = tk.Checkbutton(
            self.window,
            text="Удалять синхронизованные файлы",
            variable=self.deleting,
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            activebackground=self.ACT_BG_COLOR,
            activeforeground=self.ACT_TXT_COLOR,
            font=self.FONT
        )
        deleting_checkbutton.grid(row=0, column=0, sticky='nwes', columnspan=3)
        
        # Прогрессбар
        self.prbr = ttk.Progressbar(orient="horizontal", length=100, value=0)
        self.prbr.grid(row=1, column=0, sticky='nwes', columnspan=3)
        
        # Кнопка "Старт"
        self.btn_start = tk.Button(
            self.window,
            text="Старт",
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            activebackground=self.ACT_BG_COLOR,
            activeforeground=self.ACT_TXT_COLOR,
            font=self.FONT,
            command=self._on_start_click
        )
        self.btn_start.grid(row=0, column=4, sticky='nwes', columnspan=1, rowspan=2)
        
        # Кнопка "Настройки"
        self.btn_settings = tk.Button(
            self.window,
            text="Настройки",
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            activebackground=self.ACT_BG_COLOR,
            activeforeground=self.ACT_TXT_COLOR,
            font=self.FONT,
            command=self._on_settings_click
        )
        self.btn_settings.grid(row=0, column=3, sticky='nwes', columnspan=1, rowspan=2)
    
    def _on_start_click(self):
        """Обработчик нажатия кнопки Старт/Стоп"""
        if not self.is_syncing:
            self._start_sync()
        else:
            self._stop_sync()
    
    def _on_settings_click(self):
        """Обработчик нажатия кнопки Настройки"""
        self.btn_settings.config(state="disabled")
        self.settings_window = SettingsWindow(self.window, self.config_manager, self._on_settings_closed)
    
    def _on_settings_closed(self):
        """Обработчик закрытия окна настроек"""
        self.btn_settings.config(state="normal")
        # Перезагружаем конфигурацию на случай изменений
        self.config_manager.load_config()
    
    def _start_sync(self):
        """Запуск синхронизации"""
        self.is_syncing = True
        self.should_stop = False
        self.btn_start.config(text="Стоп")
        self.btn_settings.config(state="disabled")
        
        # Принудительное обновление GUI перед началом
        self.window.update_idletasks()
        self.window.update()
        
        start_timer = time.time()
        config_list = self.config_manager.get_config_list()
        total_pairs = len([line for line in config_list if parse_config_line(line) and parse_config_line(line).get("is_active", True)])
        processed_pairs = 0
        
        for cfg_line in config_list:
            if self.should_stop:
                break
            
            # Периодически обновляем GUI во время обработки списка пар
            self.window.update_idletasks()
            
            cfg = parse_config_line(cfg_line)
            if cfg is None:
                self._log_message(f"!ОШИБКА! : Строка конфигурации пропущена из-за неверного формата: '{cfg_line}'")
                continue
            
            # Пропускаем неактивные пары
            if not cfg.get("is_active", True):
                self._log_message(f"Пара пропущена (неактивна): {cfg['source_path']} → {cfg['dest_path']}")
                logger.info(f"Пара пропущена (неактивна): {cfg['source_path']} → {cfg['dest_path']}")
                continue
            
            processed_pairs += 1
            source_path = str(cfg["source_path"])
            dest_path = str(cfg["dest_path"])
            exclude_patterns = cfg.get("exclude_patterns") or []
            delete = self.deleting.get()
            
            logger.debug(f"задача передана на исполнение: {source_path}, {dest_path}, delete={delete}, exclude={exclude_patterns}")
            
            # Выполняем синхронизацию
            self._sync_single_pair(source_path, dest_path, delete, exclude_patterns)
            
            logger.debug(f"задача завершена: {source_path}, {dest_path}, delete={delete}, exclude={exclude_patterns}")
            
            # Обновляем GUI после каждой пары
            self.window.update_idletasks()
        
        self.is_syncing = False
        self.btn_start.config(text="Старт")
        self.btn_settings.config(state="normal")
        
        end_timer = time.time() - start_timer
        self._log_message(f"Синхронизация списка завершена за {end_timer} секунд")
        logger.info(f"Синхронизация списка завершена за {end_timer} секунд")
        self.prbr.configure(value=0)
        self.window.update()
    
    def _stop_sync(self):
        """Остановка синхронизации"""
        self.should_stop = True
        self._log_message("Остановка синхронизации...")
    
    def _sync_single_pair(self, source_folder, dest_folder, delete, exclude_patterns):
        """Синхронизация одной пары папок"""
        start_time = time.time()
        
        self.prbr.configure(value=0)
        self.window.update()
        
        logger.info(f"Задача синхронизации запущена: {source_folder} → {dest_folder}")
        self._log_message(f"---- Пара: {source_folder} → {dest_folder} ----")
        
        def progress_callback(progress, message):
            """Callback для обновления прогресса"""
            self.prbr.configure(value=progress)
            if message:
                now = dt.now().strftime("%H:%M:%S:%f")
                self._log_message(f"{now}: {message}")
            # Принудительное обновление GUI для предотвращения зависаний
            self.window.update_idletasks()
            self.window.update()
        
        def stop_check():
            """Проверка необходимости остановки"""
            return self.should_stop
        
        # Выполняем синхронизацию через sync_core
        result = sync_pair(
            source_folder,
            dest_folder,
            delete=delete,
            exclude_patterns=exclude_patterns,
            progress_callback=progress_callback,
            stop_check=stop_check
        )
        
        if result.was_cancelled:
            self.prbr.configure(value=0)
            self._log_message("Синхронизация прервана пользователем")
            return
        
        # Выводим ошибки, если есть
        for error in result.errors:
            now = dt.now().strftime("%H:%M:%S:%f")
            self._log_message(f"{now}: !ОШИБКА! {error}")
        
        self.prbr.configure(value=100)
        self.window.update()
        
        end_time = time.time() - start_time
        now = dt.now().strftime("%H:%M:%S:%f")
        self._log_message(f"{now}: Синхронизация завершена за {end_time} секунд")
        logger.info(f"Синхронизация завершена за {end_time} секунд")
        logger.info(f"Задача синхронизации завершена: {source_folder} → {dest_folder}, delete={delete}")
    
    def _log_message(self, message):
        """Добавляет сообщение в текстовую область"""
        now = dt.now().strftime("%H:%M:%S:%f")
        self.textarea.insert('end', f"\n{now}: {message}\n")
        self.textarea.see('end')
        self.window.update()
    
    def _on_close(self):
        """Обработчик закрытия окна"""
        logger.info("Программа остановлена.")
        self.window.destroy()
    
    def run(self):
        """Запуск главного цикла приложения"""
        self.window.mainloop()
