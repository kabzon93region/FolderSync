"""
Модуль логирования на базе стандартного logging.
Предоставляет API, совместимый с loguru (remove, add, info, debug, warning, error, exception).
"""
import logging
import sys
import os
import re
from datetime import datetime
from logging.handlers import RotatingFileHandler


class _LoguruFormatter(logging.Formatter):
    """Форматтер, воспроизводящий формат loguru."""
    
    def __init__(self, fmt: str):
        super().__init__()
        self._fmt_template = fmt
        self._converter = datetime.fromtimestamp
    
    def formatTime(self, record, datefmt=None):
        ct = self._converter(record.created)
        # Поддержка ключевых подстановок loguru-стиля
        # {time:DD.MM.YYYY HH:mm:ss:(x)} — полная дата
        s = self._fmt_template
        # Извлекаем все подстановки {time:...} из шаблона
        for match in re.finditer(r'\{time:([^}]+)\}', s):
            pattern = match.group(1)
            try:
                formatted = ct.strftime(pattern)
            except ValueError:
                formatted = ct.strftime("%Y-%m-%d %H:%M:%S")
            # Заменяем в record.message позже — пока сохраняем
            record._time_formatted = formatted
            break
        else:
            record._time_formatted = ct.strftime("%Y-%m-%d %H:%M:%S")
        return record._time_formatted
    
    def format(self, record):
        # Форматируем время
        self.formatTime(record)
        
        msg = record.getMessage()
        
        # Подстановки из шаблона
        result = self._fmt_template
        
        # {time:...} — уже отформатировано
        result = re.sub(r'\{time:[^}]+\}', record._time_formatted, result)
        
        # {level} — уровень
        level = record.levelname
        # {level: <8} — выравнивание
        level_match = re.search(r'\{level:\s*<(\d+)\}', result)
        if level_match:
            width = int(level_match.group(1))
            level = level.ljust(width)
            result = re.sub(r'\{level:\s*<\d+\}', level, result)
        else:
            result = result.replace('{level}', level)
        
        # {message} — сообщение
        result = result.replace('{message}', msg)
        
        return result


class _Logger:
    """
    Обёртка над logging.Logger с API, совместимым с loguru.
    
    Поддерживает:
      - logger.remove()
      - logger.add(sink, format=..., level=..., rotation=..., compression=..., enqueue=..., backtrace=..., diagnose=..., colorize=...)
      - logger.info / debug / warning / error / exception
    """
    
    # Маппинг уровней loguru → logging
    _LEVEL_MAP = {
        "TRACE": logging.DEBUG,
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "SUCCESS": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    
    def __init__(self):
        self._logger = logging.getLogger("app")
        self._logger.setLevel(logging.DEBUG)
        self._logger.propagate = False
    
    def remove(self):
        """Удаляет все handler'ы."""
        for h in self._logger.handlers[:]:
            self._logger.removeHandler(h)
            h.close()
    
    def add(self, sink, **kwargs):
        """
        Добавляет handler. 
        
        sink может быть:
          - строкой (путь к файлу) → RotatingFileHandler
          - callable → StreamHandler с custom stream
          - sys.stderr / sys.stdout → StreamHandler
        """
        level_str = kwargs.get("level", "DEBUG")
        level = self._LEVEL_MAP.get(level_str.upper(), logging.DEBUG)
        
        fmt_str = kwargs.get("format", "{time:DD.MM.YYYY HH:mm:ss} | {level: <8} | {message}")
        colorize = kwargs.get("colorize", False)
        rotation = kwargs.get("rotation", None)
        compression = kwargs.get("compression", None)
        
        formatter = _LoguruFormatter(fmt_str)
        
        # Определяем тип sink
        if callable(sink) and not isinstance(sink, type):
            # lambda / callable — оборачиваем в StreamHandler
            class _CallableHandler(logging.Handler):
                def __init__(self, fn):
                    super().__init__()
                    self._fn = fn
                def emit(self, record):
                    try:
                        msg = self.format(record)
                        self._fn(msg)
                    except Exception:
                        self.handleError(record)
            
            handler = _CallableHandler(sink)
            handler.setLevel(level)
            handler.setFormatter(formatter)
            
        elif hasattr(sink, 'write'):
            # sys.stderr, sys.stdout, или file-like объект
            handler = logging.StreamHandler(sink)
            handler.setLevel(level)
            handler.setFormatter(formatter)
            
        elif isinstance(sink, str):
            # Путь к файлу
            log_dir = os.path.dirname(sink)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            
            max_bytes = None
            backup_count = 0
            if rotation:
                max_bytes = self._parse_rotation(rotation)
                backup_count = 10
            
            if max_bytes:
                handler = RotatingFileHandler(
                    sink, maxBytes=max_bytes, backupCount=backup_count,
                    encoding="utf-8"
                )
            else:
                handler = logging.FileHandler(sink, encoding="utf-8")
            
            handler.setLevel(level)
            handler.setFormatter(formatter)
        else:
            return
        
        self._logger.addHandler(handler)
    
    @staticmethod
    def _parse_rotation(rotation):
        """Парсит строку rotation loguru ('25 MB', '100 KB', '1 GB') в байты."""
        if isinstance(rotation, (int, float)):
            return int(rotation)
        s = str(rotation).strip().upper()
        match = re.match(r'(\d+(?:\.\d+)?)\s*(KB|MB|GB|B)?', s)
        if not match:
            return None
        value = float(match.group(1))
        unit = match.group(2) or "B"
        multipliers = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3}
        return int(value * multipliers.get(unit, 1))
    
    # --- Методы логирования (совместимые с loguru) ---
    
    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)
    
    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)
    
    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)
    
    def error(self, msg, *args, **kwargs):
        self._logger.error(msg, *args, **kwargs)
    
    def critical(self, msg, *args, **kwargs):
        self._logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg, *args, **kwargs):
        self._logger.exception(msg, *args, **kwargs)
    
    def trace(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)


# Глобальный экземпляр — аналог `from loguru import logger`
logger = _Logger()
