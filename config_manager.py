"""
Модуль для работы с конфигурацией приложения.
Обеспечивает загрузку, сохранение и парсинг файла config.cfg.
"""
import os
from loguru import logger


def parse_config_line(line: str):
    """
    Разбирает строку конфигурации вида:
    <SOURCE> ===>>> <DEST>
    или
    <SOURCE> ===>>> <DEST> | EXCLUDE: pattern1;pattern2
    или
    [ACTIVE] <SOURCE> ===>>> <DEST> | EXCLUDE: pattern1;pattern2
    или
    [INACTIVE] <SOURCE> ===>>> <DEST>
    
    Args:
        line: Строка конфигурации
        
    Returns:
        dict с ключами: source_path, dest_path, exclude_patterns, is_active
        или None, если строка некорректна
    """
    raw = (line or "").strip()
    if not raw:
        return None

    # Проверяем префикс активности
    is_active = True  # по умолчанию активна для обратной совместимости
    if raw.startswith("[ACTIVE]"):
        is_active = True
        raw = raw[8:].strip()  # убираем префикс [ACTIVE]
    elif raw.startswith("[INACTIVE]"):
        is_active = False
        raw = raw[10:].strip()  # убираем префикс [INACTIVE]

    # Отделяем часть с парой папок от опций (после первого символа "|")
    if "|" in raw:
        raw_pair, raw_opts = raw.split("|", 1)
        raw_pair = raw_pair.strip()
        raw_opts = raw_opts.strip()
    else:
        raw_pair, raw_opts = raw, ""

    if " ===>>> " not in raw_pair:
        logger.error(f"Строка конфигурации имеет неверный формат (нет разделителя ' ===>>> '): '{raw}'")
        return None

    src, dest = raw_pair.split(" ===>>> ", 1)
    src = src.strip()
    dest = dest.strip()

    exclude_patterns = []
    if raw_opts:
        lower_opts = raw_opts.lower()
        if lower_opts.startswith("exclude:"):
            patterns_str = raw_opts.split(":", 1)[1].strip()
            if patterns_str:
                exclude_patterns = [p.strip() for p in patterns_str.split(";") if p.strip()]

    return {
        "source_path": src,
        "dest_path": dest,
        "exclude_patterns": exclude_patterns,
        "is_active": is_active,
    }


class ConfigManager:
    """Класс для управления конфигурацией приложения"""
    
    def __init__(self, config_file="config.cfg"):
        """
        Инициализация менеджера конфигурации.
        
        Args:
            config_file: Путь к файлу конфигурации
        """
        self.config_file = config_file
        self.dir_list = []
        self.load_config()
    
    def load_config(self):
        """Загружает конфигурацию из файла"""
        self.dir_list = []
        try:
            cfg_file = open(self.config_file, 'r')
            logger.debug(f"файл конфигурации '{os.path.abspath(os.curdir)}\\{cfg_file.name}' успешно открыт.")
            for line in cfg_file:
                str_line = line.replace("\n", '')
                if str_line.strip():  # Пропускаем пустые строки
                    self.dir_list.append(str_line)
                    logger.debug(f"загружена строка '{str_line}' из файла конфигурации.")
            cfg_file.close()
        except FileNotFoundError:
            cfg_file = open(self.config_file, 'w')
            logger.error(f"Файл конфигурации '{os.path.abspath(os.curdir)}\\{cfg_file.name}' не найден, по этому был создан пустой.")
            cfg_file.close()
    
    def save_config(self):
        """Сохраняет конфигурацию в файл"""
        cfg_file = open(self.config_file, 'w')
        for line in self.dir_list:
            cfg_file.write(f"{line}\n")
            logger.debug(f"строка '{line}' внесена в файл настройки.")
        cfg_file.close()
        logger.debug(f"файл конфигурации '{os.path.abspath(os.curdir)}\\{cfg_file.name}' успешно сохранен.")
    
    def get_config_list(self):
        """Возвращает список строк конфигурации"""
        return self.dir_list.copy()
    
    def set_config_list(self, new_list):
        """Устанавливает новый список конфигурации"""
        self.dir_list = new_list.copy()
    
    def get_parsed_configs(self):
        """
        Возвращает список распарсенных конфигураций.
        
        Returns:
            list: Список словарей с конфигурациями (или None для некорректных строк)
        """
        result = []
        for line in self.dir_list:
            parsed = parse_config_line(line)
            result.append(parsed)
        return result
