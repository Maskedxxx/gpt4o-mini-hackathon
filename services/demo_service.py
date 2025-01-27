import os
from typing import Optional
from config.config import Config, Environment
from core.logger import setup_logger

logger = setup_logger(__name__)

class DemoService:
    """
    Сервис для управления демонстрационным режимом приложения.
    В production режиме обеспечивает настройку callback URL для OAuth2 авторизации
    через внешний домен Render.com.
    """
    
    def __init__(self, config: Config):
        """
        Инициализация сервиса демонстрационного режима.
        
        Args:
            config: Конфигурация приложения
        """
        self.config = config
        
    async def setup(self) -> None:
        """
        Настраивает демонстрационное окружение.
        В production режиме использует домен Render.com для callback URL.
        В режиме разработки использует localhost.
        """
        try:
            if self.config.environment == Environment.DEMO:
                # Получаем домен из переменной окружения Render или используем localhost
                domain = os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:8000')
                
                # Обновляем redirect_uri в конфигурации
                self.config.hh.update_redirect_uri(f"{domain}")
                logger.info(f"Установлен redirect_uri для production: {self.config.hh.redirect_uri}")
                
                # Выводим инструкции для настройки
                self._print_setup_instructions()
            else:
                # Режим разработки
                logger.info("Приложение запущено в режиме разработки")
                self.config.hh.update_redirect_uri("http://localhost:8000/callback")
                self._print_development_instructions()
                
        except Exception as e:
            logger.error(f"Ошибка при настройке демонстрационного режима: {e}")
            raise
    
    def _print_setup_instructions(self) -> None:
        """Выводит инструкции по настройке для production режима."""
        print("\n=== ВАЖНО ===")
        print("Для работы приложения выполните следующие шаги:")
        print("1. Перейдите в настройки API вашего аккаунта разработчика на HeadHunter")
        print("2. Добавьте следующий Redirect URI:")
        print(f"   {self.config.hh.redirect_uri}")
        print("3. Сохраните изменения")
        print("============\n")
    
    def _print_development_instructions(self) -> None:
        """Выводит инструкции по настройке для режима разработки."""
        print("\n=== ВАЖНО ===")
        print("Переключение в режим разработки.")
        print("Убедитесь, что в настройках API вашего аккаунта разработчика на HeadHunter установлен Redirect URI:")
        print("http://localhost:8000/callback")
        print("============\n")
    
    async def cleanup(self) -> None:
        """
        Очищает ресурсы демонстрационного режима.
        В данной реализации не требуется специальной очистки.
        """
        logger.info("Очистка ресурсов демонстрационного режима")