from typing import Optional
from pyngrok import ngrok
from config.config import Config, Environment
from core.logger import setup_logger

logger = setup_logger(__name__)

class DemoService:
    """
    Сервис для управления демонстрационным режимом приложения.
    Отвечает за настройку публичного доступа через ngrok.
    """
    
    def __init__(self, config: Config):
        """
        Инициализация сервиса демонстрационного режима.
        
        Args:
            config: Конфигурация приложения
        """
        self.config = config
        self._tunnel = None
        # Настраиваем конфигурацию ngrok
        ngrok.set_auth_token("2ddCqDTXHAiJGpVlwsM9i1hGVH3_35GapDk7x4UvrRfhJk3UH")  
    
    async def setup(self) -> None:
        """
        Настраивает демонстрационное окружение.
        Создает туннель ngrok и обновляет redirect_uri в конфигурации.
        """
        if self.config.environment != Environment.DEMO:
            print("\n=== ВАЖНО ===")
            print("Переключение в режим разработки.")
            print("Убедитесь, что в настройках API вашего аккаунта разработчика на HeadHunter установлен Redirect URI:")
            print("http://localhost:8000/callback")
            print("============\n")
            return
            
        try:
            # Запускаем ngrok туннель
            self._tunnel = ngrok.connect(
                8000,
                "http"
            ).public_url
            logger.info(f"Ngrok туннель создан: {self._tunnel}")
            
            # Обновляем redirect_uri в конфигурации
            self.config.hh.update_redirect_uri(f"{self._tunnel}")
            logger.info(f"Обновлен redirect_uri: {self.config.hh.redirect_uri}")
            
            # Выводим инструкции для настройки
            self._print_setup_instructions()
            
        except Exception as e:
            logger.error(f"Ошибка при настройке демонстрационного режима: {e}")
            raise
    
    def _print_setup_instructions(self) -> None:
        """Выводит инструкции по настройке для демонстрационного режима."""
        print("\n=== ВАЖНО ===")
        print("Для демонстрации приложения выполните следующие шаги:")
        print("1. Перейдите в что в настройках API вашего аккаунта разработчика приложения на HeadHunter")
        print("2. Добавьте следующий Redirect URI:")
        print(f"   {self.config.hh.redirect_uri}")
        print("3. Сохраните изменения")
        print("============\n")
    
    async def cleanup(self) -> None:
        """Очищает ресурсы демонстрационного режима."""
        if self.config.environment == Environment.DEMO and self._tunnel:
            ngrok.disconnect()
            logger.info("Ngrok туннель закрыт")