"""
Модуль окна настроек приложения.
Содержит класс SettingsWindow для управления окном редактирования конфигурации.
"""
from tkinter import filedialog, messagebox
from pathlib import Path
from logger_config import logger
import tkinter as tk

from config_manager import ConfigManager, parse_config_line


class SettingsWindow:
    """Класс окна настроек"""
    
    # Константы стиля (совпадают с MainWindow)
    BG_COLOR = '#1E1F22'
    ACT_BG_COLOR = '#575A63'
    TXT_COLOR = '#B8BAC0'
    ACT_TXT_COLOR = '#15161A'
    FONT = ('Consolas', 10)
    WINDOW_WIDTH = 865
    WINDOW_HEIGHT = 420
    
    def __init__(self, parent_window, config_manager: ConfigManager, on_close_callback=None):
        """
        Инициализация окна настроек.
        
        Args:
            parent_window: Родительское окно (tk.Tk или tk.Toplevel)
            config_manager: Экземпляр ConfigManager для работы с конфигурацией
            on_close_callback: Функция, вызываемая при закрытии окна
        """
        self.config_manager = config_manager
        self.on_close_callback = on_close_callback
        
        # Создание окна
        self.window = tk.Toplevel(parent_window)
        self._setup_window()
        
        # Создание элементов интерфейса
        self._create_widgets()
        
        # Инициализация данных
        self.current_index = -1
        self.checkboxes_list = []
        self.dir_lb_data = []
        
        # Загрузка списка
        self._refresh_list()
    
    def _setup_window(self):
        """Настройка параметров окна"""
        xspos = (self.window.winfo_screenwidth() - self.WINDOW_WIDTH) / 2
        yspos = (self.window.winfo_screenheight() - self.WINDOW_HEIGHT) / 2
        self.window.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.window.title("Настройки синхронизации")
        self.window.geometry("%dx%d+%d+%d" % (self.WINDOW_WIDTH, self.WINDOW_HEIGHT, xspos, yspos))
        self.window.resizable(False, False)
        self.window.config(bg=self.BG_COLOR)
        self.window.grab_set()
        
        for i in range(14):
            self.window.grid_rowconfigure(i, minsize=30)
            if i <= 8:
                self.window.grid_columnconfigure(i, minsize=100)
    
    def _create_widgets(self):
        """Создание элементов интерфейса"""
        # Поля ввода
        self.ent_source = tk.Entry(self.window)
        self.ent_source.grid(row=0, column=0, columnspan=6, rowspan=1, sticky='nwes')
        
        self.ent_dest = tk.Entry(self.window)
        self.ent_dest.grid(row=1, column=0, columnspan=6, rowspan=1, sticky='nwes')
        
        self.ent_exclude = tk.Entry(self.window)
        self.ent_exclude.grid(row=2, column=0, columnspan=6, rowspan=1, sticky='nwes')
        
        # Метка для исключений
        lbl_ex = tk.Label(
            self.window,
            text="Исключения (через ;) напр.: *.tmp;*.log;__pycache__",
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            font=self.FONT,
            wraplength=260,
            justify="left"
        )
        lbl_ex.grid(row=2, column=6, columnspan=2, rowspan=1, sticky='nwes')
        
        # Кнопки управления
        btn_ok = tk.Button(
            self.window,
            text="OK",
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            activebackground=self.ACT_BG_COLOR,
            activeforeground=self.ACT_TXT_COLOR,
            font=self.FONT,
            command=self._on_ok
        )
        btn_ok.grid(row=0, column=7, columnspan=1, rowspan=1, sticky='nwes')
        
        btn_cancel = tk.Button(
            self.window,
            text="Отмена",
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            activebackground=self.ACT_BG_COLOR,
            activeforeground=self.ACT_TXT_COLOR,
            font=self.FONT,
            command=self._on_cancel
        )
        btn_cancel.grid(row=1, column=7, columnspan=1, rowspan=1, sticky='nwes')
        
        btn_select_source = tk.Button(
            self.window,
            text="Выбрать исходную папку",
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            activebackground=self.ACT_BG_COLOR,
            activeforeground=self.ACT_TXT_COLOR,
            font=self.FONT,
            command=lambda: self._select_folder(self.ent_source, "Выберите исходную папку, из которой будет произведена копия(синхронизация)")
        )
        btn_select_source.grid(row=0, column=6, columnspan=1, rowspan=1, sticky='nwes')
        
        btn_select_dest = tk.Button(
            self.window,
            text="Выбрать конечную папку",
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            activebackground=self.ACT_BG_COLOR,
            activeforeground=self.ACT_TXT_COLOR,
            font=self.FONT,
            command=lambda: self._select_folder(self.ent_dest, "Выберите конечную папку, в которую будет произведена копия(синхронизация)")
        )
        btn_select_dest.grid(row=1, column=6, columnspan=1, rowspan=1, sticky='nwes')
        
        btn_edit = tk.Button(
            self.window,
            text="Редактировать",
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            activebackground=self.ACT_BG_COLOR,
            activeforeground=self.ACT_TXT_COLOR,
            font=self.FONT,
            command=self._on_edit
        )
        btn_edit.grid(row=3, column=0, columnspan=2, rowspan=1, sticky='nwes')
        
        btn_save = tk.Button(
            self.window,
            text="Сохранить",
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            activebackground=self.ACT_BG_COLOR,
            activeforeground=self.ACT_TXT_COLOR,
            font=self.FONT,
            command=self._on_save
        )
        btn_save.grid(row=3, column=2, columnspan=2, rowspan=1, sticky='nwes')
        
        btn_delete = tk.Button(
            self.window,
            text="Удалить",
            bg=self.BG_COLOR,
            fg=self.TXT_COLOR,
            activebackground=self.ACT_BG_COLOR,
            activeforeground=self.ACT_TXT_COLOR,
            font=self.FONT,
            command=self._on_delete
        )
        btn_delete.grid(row=3, column=4, columnspan=2, rowspan=1, sticky='nwes')
        
        # Создаем Frame с Canvas и Scrollbar для списка пар с чекбоксами
        list_frame = tk.Frame(self.window, bg=self.BG_COLOR)
        list_frame.grid(row=4, column=0, sticky='nwes', columnspan=8, rowspan=11)
        
        scrollbar = tk.Scrollbar(list_frame, bg=self.BG_COLOR)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas = tk.Canvas(list_frame, bg=self.BG_COLOR, yscrollcommand=scrollbar.set, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)
        
        # Frame внутри Canvas для элементов списка
        self.items_frame = tk.Frame(self.canvas, bg=self.BG_COLOR)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.items_frame, anchor='nw')
        
        def update_canvas_scroll_region(event=None):
            self.canvas.update_idletasks()
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        def on_canvas_configure(event):
            canvas_width = event.width
            self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.canvas.bind('<Configure>', on_canvas_configure)
        self.items_frame.bind('<Configure>', update_canvas_scroll_region)
    
    def _select_folder(self, entry_widget, title):
        """Выбор папки через диалог"""
        folder = filedialog.askdirectory(title=title)
        if folder:
            entry_widget.delete(0, 'end')
            entry_widget.insert(0, str(Path(folder)))
            logger.info(f"Выбрана папка: '{folder}'")
    
    def _refresh_list(self):
        """Обновляет отображение списка пар с чекбоксами"""
        # Очищаем существующие элементы
        for widget in self.items_frame.winfo_children():
            widget.destroy()
        self.checkboxes_list.clear()
        self.dir_lb_data.clear()
        
        # Создаем элементы списка
        for idx, line in enumerate(self.config_manager.get_config_list()):
            cfg = parse_config_line(line)
            is_active = cfg.get("is_active", True) if cfg else True
            
            # Frame для одной строки
            row_frame = tk.Frame(self.items_frame, bg=self.BG_COLOR)
            row_frame.pack(fill=tk.X, padx=2, pady=1)
            
            # Чекбокс активности
            var = tk.BooleanVar(value=is_active)
            checkbox = tk.Checkbutton(
                row_frame,
                variable=var,
                bg=self.BG_COLOR,
                fg=self.TXT_COLOR,
                activebackground=self.ACT_BG_COLOR,
                activeforeground=self.ACT_TXT_COLOR,
                selectcolor=self.BG_COLOR,
                font=self.FONT
            )
            checkbox.pack(side=tk.LEFT, padx=5)
            
            # Метка с текстом пары
            label_text = line
            # Убираем префикс активности из отображения для читаемости
            if label_text.startswith("[ACTIVE]"):
                label_text = label_text[8:].strip()
            elif label_text.startswith("[INACTIVE]"):
                label_text = label_text[10:].strip()
            
            label = tk.Label(
                row_frame,
                text=label_text,
                bg=self.BG_COLOR,
                fg=self.TXT_COLOR,
                font=self.FONT,
                anchor='w',
                cursor='hand2'
            )
            label.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            # Привязываем клик по метке к выбору строки
            def on_label_click(event, index=idx):
                self._select_item(index)
            
            label.bind('<Button-1>', on_label_click)
            
            self.checkboxes_list.append({
                'var': var,
                'checkbox': checkbox,
                'label': label,
                'row_frame': row_frame,
                'original_line': line
            })
            self.dir_lb_data.append(line)
        
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    
    def _select_item(self, index):
        """Выбирает элемент для редактирования"""
        if 0 <= index < len(self.dir_lb_data):
            self.current_index = index
            msg = self.dir_lb_data[index]
            cfg = parse_config_line(msg)
            if cfg is None:
                messagebox.showinfo("Информационное сообщение", "Выбранная строка конфигурации имеет неверный формат.")
                return
            self.ent_source.delete(0, 'end')
            self.ent_source.insert(0, str(cfg["source_path"]))
            self.ent_dest.delete(0, 'end')
            self.ent_dest.insert(0, str(cfg["dest_path"]))
            patterns = cfg.get("exclude_patterns") or []
            self.ent_exclude.delete(0, 'end')
            if patterns:
                self.ent_exclude.insert(0, ";".join(patterns))
        else:
            messagebox.showinfo("Информационное сообщение", "Не выбран в списке элемент для редактирования.")
    
    def _on_edit(self):
        """Обработчик кнопки Редактировать"""
        if self.current_index == -1:
            messagebox.showinfo("Информационное сообщение", "Выберите строку кликом по тексту для редактирования.")
    
    def _on_save(self):
        """Обработчик кнопки Сохранить"""
        if len(self.ent_source.get()) > 0 and len(self.ent_dest.get()) > 0:
            msg_list = f"{self.ent_source.get()} ===>>> {self.ent_dest.get()}"
            if len(self.ent_exclude.get()) > 0:
                msg_list = f"{msg_list} | EXCLUDE: {self.ent_exclude.get()}"
            
            # Сохраняем состояние активности из чекбокса
            if self.current_index != -1:
                idx = self.current_index
                # Получаем состояние активности из чекбокса
                if idx < len(self.checkboxes_list):
                    is_active = self.checkboxes_list[idx]['var'].get()
                    if not is_active:
                        msg_list = f"[INACTIVE] {msg_list}"
                    else:
                        msg_list = f"[ACTIVE] {msg_list}"
                
                # Обновляем в списке конфигурации
                config_list = self.config_manager.get_config_list()
                config_list[idx] = msg_list
                self.config_manager.set_config_list(config_list)
            else:
                # При добавлении нового элемента - по умолчанию активен
                msg_list = f"[ACTIVE] {msg_list}"
                config_list = self.config_manager.get_config_list()
                config_list.append(msg_list)
                self.config_manager.set_config_list(config_list)
            
            # Обновляем отображение списка
            self._refresh_list()
            self.current_index = -1
            # Очищаем поля редактирования
            self.ent_source.delete(0, 'end')
            self.ent_dest.delete(0, 'end')
            self.ent_exclude.delete(0, 'end')
        else:
            messagebox.showinfo("Информационное сообщение", "Не заполнены поля путей папок для сохранения в список.")
    
    def _on_delete(self):
        """Обработчик кнопки Удалить"""
        if self.current_index != -1 and 0 <= self.current_index < len(self.config_manager.get_config_list()):
            idx = self.current_index
            config_list = self.config_manager.get_config_list()
            config_list.pop(idx)
            self.config_manager.set_config_list(config_list)
            self._refresh_list()
            self.current_index = -1
            # Очищаем поля редактирования
            self.ent_source.delete(0, 'end')
            self.ent_dest.delete(0, 'end')
            self.ent_exclude.delete(0, 'end')
        else:
            messagebox.showinfo("Информационное сообщение", "Сначала выберите элемент для удаления (кликните по тексту строки).")
    
    def _on_ok(self):
        """Обработчик кнопки OK - сохранение конфигурации"""
        # Обновляем dirList с учетом состояния чекбоксов
        updated_dir_list = []
        for idx, checkbox_item in enumerate(self.checkboxes_list):
            is_active = checkbox_item['var'].get()
            original_line = checkbox_item['original_line']
            
            # Убираем префикс активности из оригинальной строки
            line_without_prefix = original_line
            if line_without_prefix.startswith("[ACTIVE]"):
                line_without_prefix = line_without_prefix[8:].strip()
            elif line_without_prefix.startswith("[INACTIVE]"):
                line_without_prefix = line_without_prefix[10:].strip()
            
            # Формируем строку с учетом текущего состояния активности
            if is_active:
                updated_line = f"[ACTIVE] {line_without_prefix}"
            else:
                updated_line = f"[INACTIVE] {line_without_prefix}"
            
            updated_dir_list.append(updated_line)
        
        # Сохраняем конфигурацию
        self.config_manager.set_config_list(updated_dir_list)
        self.config_manager.save_config()
        
        # Закрываем окно
        self._close()
    
    def _on_cancel(self):
        """Обработчик кнопки Отмена или закрытия окна"""
        self._close()
    
    def _close(self):
        """Закрытие окна"""
        self.window.grab_release()
        self.window.destroy()
        if self.on_close_callback:
            self.on_close_callback()
