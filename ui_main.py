"""
Модуль главного окна приложения.
Содержит класс MainWindow для управления главным интерфейсом.
"""
from datetime import datetime as dt
from pathlib import Path
from logger_config import logger
from tkinter import ttk
import tkinter as tk
import threading
import queue
import sys
import os
import time

from config_manager import ConfigManager, parse_config_line
from sync_core import sync_pair
from ui_settings import SettingsWindow


def _resource_path(relative_path):
    """Получает абсолютный путь к ресурсу (работает и для exe, и для исходников)."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


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
    POLL_INTERVAL_MS = 50

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.is_syncing = False
        self._stop_event = threading.Event()
        self._msg_queue = queue.Queue()
        self._sync_thread = None

        self.window = tk.Tk()
        self._setup_window()
        self._create_widgets()
        self.settings_window = None

    def _setup_window(self):
        xspos = (self.window.winfo_screenwidth() - self.WINDOW_WIDTH) / 2
        yspos = (self.window.winfo_screenheight() - self.WINDOW_HEIGHT) / 2
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)
        self.window.title(self.TITLE)
        self.window.geometry("%dx%d+%d+%d" % (self.WINDOW_WIDTH, self.WINDOW_HEIGHT, xspos, yspos))
        self.window.resizable(False, False)

        try:
            icon_path = _resource_path(self.ICON_PATH)
            self.window.iconbitmap(icon_path)
        except Exception as e:
            logger.error(f"не удалось загрузить иконку: {e}")

        self.window.config(bg=self.BG_COLOR)

        for i in range(5):
            self.window.grid_rowconfigure(i, minsize=60)
            if i <= 5:
                self.window.grid_columnconfigure(i, minsize=128)

    def _create_widgets(self):
        self.textarea = tk.Text(
            self.window,
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            font=self.FONT,
            height=1
        )
        self.textarea.grid(row=2, column=0, sticky='nwes', columnspan=5, rowspan=3)

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

        self.prbr = ttk.Progressbar(orient="horizontal", length=100, value=0)
        self.prbr.grid(row=1, column=0, sticky='nwes', columnspan=3)

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
        if not self.is_syncing:
            self._start_sync()
        else:
            self._stop_sync()

    def _on_settings_click(self):
        self.btn_settings.config(state="disabled")
        self.settings_window = SettingsWindow(self.window, self.config_manager, self._on_settings_closed)

    def _on_settings_closed(self):
        self.btn_settings.config(state="normal")
        self.config_manager.load_config()

    # --- Потокобезопасная доставка сообщений в GUI ---

    def _put_msg(self, msg_type, **kwargs):
        """Потокобезопасная отправка сообщения в очередь."""
        self._msg_queue.put((msg_type, kwargs))

    def _poll_queue(self):
        """Опрос очереди сообщений из главного потока (через after)."""
        try:
            while True:
                msg_type, data = self._msg_queue.get_nowait()

                if msg_type == "log":
                    self._append_log(data["text"])

                elif msg_type == "progress":
                    self.prbr.configure(value=data["value"])

                elif msg_type == "done":
                    self._on_sync_finished(data["elapsed"])
                    return

                elif msg_type == "error":
                    self._append_log(f"!ОШИБКА! {data['text']}")
        except queue.Empty:
            pass

        if self.is_syncing:
            self.window.after(self.POLL_INTERVAL_MS, self._poll_queue)

    def _append_log(self, text):
        now = dt.now().strftime("%H:%M:%S:%f")
        self.textarea.insert('end', f"\n{now}: {text}\n")
        self.textarea.see('end')

    def _on_sync_finished(self, elapsed):
        self.is_syncing = False
        self.btn_start.config(text="Старт")
        self.btn_settings.config(state="normal")
        self._append_log(f"Синхронизация списка завершена за {elapsed:.1f} секунд")
        logger.info(f"Синхронизация списка завершена за {elapsed:.1f} секунд")
        self.prbr.configure(value=0)

    # --- Запуск / остановка синхронизации ---

    def _start_sync(self):
        self.is_syncing = True
        self._stop_event.clear()
        self.btn_start.config(text="Стоп")
        self.btn_settings.config(state="disabled")
        self.textarea.delete('1.0', 'end')

        self._sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
        self._sync_thread.start()
        self.window.after(self.POLL_INTERVAL_MS, self._poll_queue)

    def _stop_sync(self):
        self._stop_event.set()
        self._put_msg("log", text="Остановка синхронизации...")

    def _sync_worker(self):
        """Рабочий поток: выполняет всю синхронизацию."""
        start_timer = time.time()

        def progress_callback(progress, message):
            self._put_msg("progress", value=progress)
            if message:
                self._put_msg("log", text=message)

        def stop_check():
            return self._stop_event.is_set()

        config_list = self.config_manager.get_config_list()

        for cfg_line in config_list:
            if self._stop_event.is_set():
                break

            cfg = parse_config_line(cfg_line)
            if cfg is None:
                self._put_msg("log", text=f"!ОШИБКА! Строка конфигурации пропущена: '{cfg_line}'")
                continue

            if not cfg.get("is_active", True):
                self._put_msg("log", text=f"Пара пропущена (неактивна): {cfg['source_path']} → {cfg['dest_path']}")
                logger.info(f"Пара пропущена (неактивна): {cfg['source_path']} → {cfg['dest_path']}")
                continue

            source_path = str(cfg["source_path"])
            dest_path = str(cfg["dest_path"])
            exclude_patterns = cfg.get("exclude_patterns") or []
            delete = self.deleting.get()

            logger.debug(f"задача передана на исполнение: {source_path}, {dest_path}, delete={delete}, exclude={exclude_patterns}")
            self._put_msg("log", text=f"---- Пара: {source_path} → {dest_path} ----")

            result = sync_pair(
                source_path,
                dest_path,
                delete=delete,
                exclude_patterns=exclude_patterns,
                progress_callback=progress_callback,
                stop_check=stop_check
            )

            if result.was_cancelled:
                self._put_msg("progress", value=0)
                self._put_msg("log", text="Синхронизация прервана пользователем")
                break

            for error in result.errors:
                self._put_msg("error", text=error)

            self._put_msg("progress", value=100)
            logger.debug(f"задача завершена: {source_path}, {dest_path}, delete={delete}, exclude={exclude_patterns}")

        elapsed = time.time() - start_timer
        self._put_msg("done", elapsed=elapsed)

    def _on_close(self):
        if self.is_syncing:
            self._stop_event.set()
            self._sync_thread.join(timeout=3)
        logger.info("Программа остановлена.")
        self.window.destroy()

    def run(self):
        self.window.mainloop()
