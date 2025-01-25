# core/logger.py
import logging
import sys
from typing import Optional

def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Настраивает и возвращает logger с заданной конфигурацией.
    
    Args:
        name: Имя логгера
        
    Returns:
        Настроенный объект logger
    """
    logger = logging.getLogger(name or __name__)
    
    # Настройка уровня логирования
    logger.setLevel(logging.INFO)
    
    # Создание форматтера для логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Добавление обработчика для вывода в консоль
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger