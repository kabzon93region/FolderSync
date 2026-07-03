"""
Модуль ядра синхронизации файлов.
Содержит функции для сканирования директорий, сравнения файлов и синхронизации.
"""
import os
import shutil
from datetime import datetime
from fnmatch import fnmatch
from loguru import logger

# Убеждаемся, что logger доступен (он должен быть инициализирован в main.py)
# Если logger не инициализирован, создадим базовую конфигурацию
try:
    logger.info("sync_core: logger доступен")
except:
    # Если logger не настроен, настраиваем базовую конфигурацию
    import sys
    logger.remove()  # Удаляем стандартный handler
    logger.add(sys.stderr, level="DEBUG")
    logger.add("./logs/log.log", format="{time:DD.MM.YYYY HH:mm:ss:(x)} - {level} - {message}", level="DEBUG", rotation="25 MB", compression="zip")


def is_excluded(source_path: str, name: str, exclude_patterns):
    """
    Проверяет, должен ли файл/папка быть исключён из обработки согласно списку масок.
    - Маски без слэша интерпретируются как маски имени (fnmatch по имени/базовому имени).
    - Маски, оканчивающиеся на '/*', интерпретируются как префикс пути каталога.
    
    Args:
        source_path: Полный путь к файлу/папке
        name: Имя файла/папки
        exclude_patterns: Список масок исключений
        
    Returns:
        bool: True, если элемент должен быть исключён
    """
    if not exclude_patterns:
        return False

    norm_source = os.path.normpath(source_path)
    basename = os.path.basename(source_path)
    name = name or basename

    for pattern in exclude_patterns:
        pat = pattern.strip()
        if not pat:
            continue

        # Исключение каталога/поддерева: путь/* 
        if pat.endswith("/*") or pat.endswith("\\*"):
            base = pat[:-2]
            base_norm = os.path.normpath(base)
            if norm_source.startswith(base_norm):
                logger.debug(f"элемент '{source_path}' исключён по паттерну каталога '{pat}'")
                return True

        # Маска по имени файла/каталога
        if fnmatch(name, pat) or fnmatch(basename, pat):
            logger.debug(f"элемент '{source_path}' исключён по маске имени '{pat}'")
            return True

    return False


def scan_directory(base_path, exclude_patterns=None, stop_requested=None, progress_callback=None):
    """
    Сканирует директорию и возвращает словарь с информацией о файлах.
    
    Args:
        base_path: Путь к базовой директории
        exclude_patterns: Список масок исключений
        stop_requested: Список из одного bool [False] — при True прерывать сканирование
        progress_callback: Функция callback(count, message) для периодического обновления прогресса
        
    Returns:
        dict: Словарь {относительный_путь: {'path': абсолютный_путь, 'size': размер, 'mtime': время_модификации}}
    """
    files_dict = {}
    base_path_norm = os.path.normpath(base_path)
    stop = lambda: (stop_requested is not None and stop_requested and stop_requested[0])
    file_count = 0
    last_update_count = 0
    update_frequency = 100  # Обновляем GUI каждые 100 файлов

    try:
        for root, dirs, files in os.walk(base_path):
            if stop():
                break
            if exclude_patterns:
                original_dirs = list(dirs)
                for dirname in original_dirs:
                    dir_full_path = os.path.join(root, dirname)
                    if is_excluded(dir_full_path, dirname, exclude_patterns):
                        dirs.remove(dirname)
                        logger.debug(f"Каталог '{dir_full_path}' пропущен по списку исключений.")

            for filename in files:
                if stop():
                    break
                full_path = os.path.join(root, filename)
                if exclude_patterns and is_excluded(full_path, filename, exclude_patterns):
                    logger.debug(f"Файл '{full_path}' пропущен по списку исключений.")
                    continue
                try:
                    rel_path = os.path.relpath(full_path, base_path_norm)
                    stat_info = os.stat(full_path)
                    files_dict[rel_path] = {
                        'path': full_path,
                        'size': stat_info.st_size,
                        'mtime': stat_info.st_mtime
                    }
                    file_count += 1
                    
                    # Периодически обновляем GUI для предотвращения зависаний
                    if progress_callback and (file_count - last_update_count >= update_frequency):
                        progress_callback(file_count, f"Сканирование: найдено {file_count} файлов...")
                        last_update_count = file_count
                except (OSError, PermissionError) as e:
                    logger.warning(f"Не удалось получить информацию о файле '{full_path}': {e}")
                    continue
    except Exception as e:
        logger.error(f"Ошибка при сканировании директории '{base_path}': {e}")

    # Финальное обновление прогресса
    if progress_callback and file_count > 0:
        progress_callback(file_count, f"Сканирование завершено: найдено {file_count} файлов")

    return files_dict


def should_copy_file(source_info, dest_info):
    """
    Определяет, нужно ли копировать файл по дате изменения.
    Копируем, если файла нет в назначении или источник новее по дате изменения.
    Размер не учитывается: если файл в назначении старее — обновляем.
    
    Args:
        source_info: dict с информацией об исходном файле ('size', 'mtime')
        dest_info: dict с информацией о целевом файле или None
        
    Returns:
        bool: True, если файл нужно копировать
    """
    if dest_info is None:
        return True
    # Только по дате изменения: копируем, если источник новее
    return source_info['mtime'] > dest_info['mtime']


class SyncResult:
    """Класс для хранения результатов синхронизации"""
    def __init__(self):
        self.copied_count = 0
        self.total_files = 0
        self.deleted_count = 0
        self.errors = []
        self.was_cancelled = False


def sync_pair(source_folder, dest_folder, delete=False, exclude_patterns=None, 
              progress_callback=None, stop_check=None):
    """
    Выполняет синхронизацию пары папок.
    
    Args:
        source_folder: Путь к исходной папке
        dest_folder: Путь к целевой папке
        delete: Удалять ли исходные файлы после копирования
        exclude_patterns: Список масок исключений
        progress_callback: Функция callback(progress, message) для обновления прогресса
        stop_check: Функция, возвращающая True, если нужно остановить синхронизацию
        
    Returns:
        SyncResult: Результат синхронизации
    """
    result = SyncResult()
    
    # Проверка путей: допускаются корень диска (R:\, C:\) и любые подпапки
    src = (source_folder or "").strip()
    dst = (dest_folder or "").strip()
    if len(src) < 2 or len(dst) < 2:
        error_msg = "Не заданы пути папок для синхронизации"
        logger.error(error_msg)
        result.errors.append(error_msg)
        return result
    
    # Используем нормализованные пути
    source_folder = os.path.normpath(src)
    dest_folder = os.path.normpath(dst)
    
    if progress_callback:
        progress_callback(5, f"Шаг 1/5 — Сканирование исходной папки: {source_folder}")
    
    logger.info(f"Обработка пары: {source_folder} → {dest_folder}")
    
    # Шаг 1: Сканирование исходной папки
    stop_requested = [False]
    
    # Callback для обновления прогресса сканирования
    def scan_progress_callback(count, message):
        if progress_callback:
            # Прогресс сканирования: 5-12% от общего прогресса
            progress = 5 + int((count / max(count, 1)) * 7) if count > 0 else 5
            progress_callback(progress, message)
    
    source_files = scan_directory(source_folder, exclude_patterns, stop_requested, scan_progress_callback)
    
    if progress_callback:
        progress_callback(12, f"Найдено файлов в источнике: {len(source_files)}")
    
    logger.info(f"Пара {source_folder} → {dest_folder}: в источнике {len(source_files)} файлов")
    
    if stop_check and stop_check():
        result.was_cancelled = True
        return result
    
    # Шаг 2: Сканирование целевой папки
    if progress_callback:
        progress_callback(12, f"Шаг 2/5 — Сканирование целевой папки: {dest_folder}")
    
    dest_exists = os.path.exists(dest_folder)
    
    # Callback для обновления прогресса сканирования целевой папки
    def scan_dest_progress_callback(count, message):
        if progress_callback:
            # Прогресс сканирования: 12-20% от общего прогресса
            progress = 12 + int((count / max(count, 1)) * 8) if count > 0 else 12
            progress_callback(progress, message)
    
    dest_files = scan_directory(dest_folder, exclude_patterns, stop_requested, scan_dest_progress_callback) if dest_exists else {}
    
    if progress_callback:
        progress_callback(20, f"Найдено файлов в назначении: {len(dest_files)}")
    
    logger.info(f"Пара {source_folder} → {dest_folder}: в назначении {len(dest_files)} файлов")
    
    if stop_check and stop_check():
        result.was_cancelled = True
        return result
    
    # Шаг 3: Сверка списков (анализ различий)
    if progress_callback:
        progress_callback(20, "Шаг 3/5 — Сверка списков (анализ различий)")
    
    files_to_copy = []
    files_to_delete_source = []
    dirs_to_create = set()
    
    # Файлы для копирования/обновления
    total_source_files = len(source_files)
    processed_files = 0
    last_progress_update = 0
    
    for rel_path, source_info in source_files.items():
        if stop_check and stop_check():
            result.was_cancelled = True
            return result
        
        dest_path = os.path.join(dest_folder, rel_path)
        dest_info = dest_files.get(rel_path)
        
        if should_copy_file(source_info, dest_info):
            files_to_copy.append((source_info['path'], dest_path, rel_path, source_info))
            dest_dir = os.path.dirname(dest_path)
            if dest_dir:
                dirs_to_create.add(dest_dir)
            if delete:
                files_to_delete_source.append(source_info['path'])
        elif delete and dest_info is not None:
            # Файл в источнике не новее по дате, но есть в назначении — можно удалить из источника
            if source_info['mtime'] <= dest_info['mtime']:
                files_to_delete_source.append(source_info['path'])
        
        processed_files += 1
        # Периодически обновляем GUI во время сравнения файлов
        if progress_callback and (processed_files - last_progress_update >= 500 or processed_files == total_source_files):
            progress = 20 + int((processed_files / total_source_files) * 8) if total_source_files > 0 else 20
            progress_callback(progress, f"Сверка списков: обработано {processed_files}/{total_source_files} файлов")
            last_progress_update = processed_files
    
    if progress_callback:
        progress_callback(28, f"К копированию: {len(files_to_copy)} файлов, к созданию: {len(dirs_to_create)} папок")
    
    logger.info(f"Пара {source_folder} → {dest_folder}: к копированию {len(files_to_copy)} файлов")
    
    if stop_check and stop_check():
        result.was_cancelled = True
        return result
    
    # Шаг 4: Создание директорий
    logger.info(f"Проверка и создание {len(dirs_to_create)} директорий")
    if progress_callback:
        progress_callback(28, f"Шаг 4/5 — Создание директорий ({len(dirs_to_create)} папок)")
    
    created_dirs = []  # Список созданных директорий для логирования
    existing_dirs = []  # Список уже существующих директорий
    created_dirs_count = 0
    
    # Логируем список всех директорий, которые нужно проверить/создать
    logger.info("Список директорий для проверки:")
    for idx, dest_dir in enumerate(sorted(dirs_to_create), 1):
        logger.info(f"  {idx}. {dest_dir}")
    
    for dest_dir in sorted(dirs_to_create):
        if stop_check and stop_check():
            result.was_cancelled = True
            return result
        
        if not os.path.exists(dest_dir):
            try:
                os.makedirs(dest_dir, exist_ok=True)
                created_dirs_count += 1
                created_dirs.append(dest_dir)
                # Лог в файл с полным путём
                logger.info(f"✓ Создана папка: '{dest_dir}'")
                # И вывод в GUI / callback
                if progress_callback:
                    progress_callback(28, f"Создана папка: {dest_dir}")
            except Exception as e:
                error_msg = f"✗ Не удалось создать папку '{dest_dir}': {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)
        else:
            existing_dirs.append(dest_dir)
            logger.info(f"→ Папка уже существует: '{dest_dir}'")
    
    # Логируем итоговую информацию
    if created_dirs_count > 0:
        logger.info(f"Всего создано новых папок: {created_dirs_count}")
        if created_dirs:
            logger.info("Список созданных директорий:")
            for idx, dir_path in enumerate(created_dirs, 1):
                logger.info(f"  {idx}. {dir_path}")
        if progress_callback:
            progress_callback(28, f"Создано папок: {created_dirs_count}")
    
    if existing_dirs:
        logger.info(f"Папок уже существовало: {len(existing_dirs)}")
        if len(existing_dirs) <= 10:  # Логируем список, если папок немного
            logger.info("Список существующих директорий:")
            for idx, dir_path in enumerate(existing_dirs, 1):
                logger.info(f"  {idx}. {dir_path}")
    
    if created_dirs_count == 0 and not existing_dirs:
        logger.warning("Не было директорий для создания (список пуст)")
    
    # Шаг 5: Копирование файлов (синхронизация)
    result.total_files = len(files_to_copy)
    logger.info(f"Начало копирования {result.total_files} файлов из '{source_folder}' в '{dest_folder}'")
    if progress_callback:
        progress_callback(30, f"Шаг 5/5 — Копирование файлов (синхронизация): {result.total_files} файлов")
    
    for idx, item in enumerate(files_to_copy):
        # Поддержка старого формата (3 элемента) и нового (4 элемента с source_info)
        if len(item) == 4:
            source_path, dest_path, rel_path, source_info = item
        else:
            source_path, dest_path, rel_path = item[0], item[1], item[2]
            source_info = None
        
        if stop_check and stop_check():
            logger.info(f"Синхронизация прервана пользователем на файле {idx + 1}/{result.total_files}")
            result.was_cancelled = True
            return result
        
        try:
            # Копируем файл
            shutil.copy2(source_path, dest_path)
            result.copied_count += 1
            
            # Всегда логируем каждый скопированный файл: имя, размер, дата изменения
            if source_info:
                size_bytes = source_info['size']
                size_mb = size_bytes / (1024 * 1024)
                mtime_dt = datetime.fromtimestamp(source_info['mtime'])
                mtime_str = mtime_dt.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Скопирован: {rel_path} | размер: {size_mb:.4f} MB ({size_bytes} байт) | дата: {mtime_str}")
            else:
                st = os.stat(source_path)
                size_mb = st.st_size / (1024 * 1024)
                mtime_str = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Скопирован: {rel_path} | размер: {size_mb:.4f} MB | дата: {mtime_str}")
        except Exception as e:
            error_msg = f"Ошибка при копировании '{source_path}' в '{dest_path}': {e}"
            logger.exception(error_msg)
            result.errors.append(error_msg)
        
        # Периодически обновляем GUI
        update_frequency = 5 if result.total_files > 50 else 1
        if (idx + 1) % update_frequency == 0 or (idx + 1) == result.total_files:
            progress = 30 + int((idx + 1) / result.total_files * 55) if result.total_files > 0 else 30
            if progress_callback:
                progress_callback(progress, f"Скопировано: {idx + 1}/{result.total_files}")
            
            if (idx + 1) % 10 == 0 or (idx + 1) == result.total_files:
                logger.info(f"Прогресс копирования: {idx + 1}/{result.total_files} файлов скопировано")
    
    # Удаление файлов из источника (если включено)
    if delete and files_to_delete_source:
        if progress_callback:
            progress_callback(88, f"Удаление файлов из источника: {len(files_to_delete_source)} файлов")
        
        deleted_idx = 0
        for source_path in files_to_delete_source:
            if stop_check and stop_check():
                result.was_cancelled = True
                return result
            try:
                os.remove(source_path)
                result.deleted_count += 1
                logger.info(f"Файл '{source_path}' удален после синхронизации.")
            except PermissionError:
                error_msg = f"Файл '{source_path}' не удален, т.к. нет прав."
                logger.error(error_msg)
                result.errors.append(error_msg)
            except Exception as e:
                error_msg = f"Ошибка при удалении '{source_path}': {e}"
                logger.error(error_msg)
                result.errors.append(error_msg)
            
            deleted_idx += 1
            # Периодически обновляем GUI во время удаления
            if progress_callback and (deleted_idx % 50 == 0 or deleted_idx == len(files_to_delete_source)):
                progress = 88 + int((deleted_idx / len(files_to_delete_source)) * 10) if len(files_to_delete_source) > 0 else 88
                progress_callback(progress, f"Удалено файлов: {deleted_idx}/{len(files_to_delete_source)}")
    
    if progress_callback:
        progress_callback(100, f"Пара завершена: {source_folder} → {dest_folder}. Скопировано: {result.copied_count}/{result.total_files} файлов")
    
    logger.info(f"Пара {source_folder} → {dest_folder} завершена. Скопировано: {result.copied_count}/{result.total_files} файлов")
    
    return result
