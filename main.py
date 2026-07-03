"""
Точка входа приложения FolderSync.
Инициализирует логирование и запускает главное окно.
"""
from logger_config import logger
from config_manager import ConfigManager
from ui_main import MainWindow


def main():
    """Главная функция приложения"""
    # Инициализация логирования
    # Удаляем стандартный handler для консоли
    logger.remove()
    
    # Добавляем handler для файла с принудительной записью
    logger.add(
        "./logs/log.log",
        format="{time:DD.MM.YYYY HH:mm:ss:(x)} - {level} - {message}",
        level="DEBUG",
        rotation="25 MB",
        compression="zip",
        enqueue=True,  # Асинхронная запись для предотвращения блокировок
        backtrace=True,  # Полный стек вызовов при ошибках
        diagnose=True  # Детальная диагностика
    )
    
    # Также добавляем вывод в консоль для отладки
    logger.add(
        lambda msg: print(msg, end=""),
        format="{time:HH:mm:ss} | {level: <8} | {message}",
        level="INFO",
        colorize=True
    )
    
    logger.info("Программа запущена.")
    
    # Инициализация менеджера конфигурации
    config_manager = ConfigManager()
    
    # Создание и запуск главного окна
    app = MainWindow(config_manager)
    app.run()


if __name__ == "__main__":
    main()
