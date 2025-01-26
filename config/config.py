# config/config.py

from dataclasses import dataclass
from os import getenv
from enum import Enum
from core.logger import setup_logger
from dotenv import load_dotenv
load_dotenv(dotenv_path="./.env", override=True)

logger = setup_logger(__name__)

class Environment(Enum):
    """Окружения для работы приложения."""
    DEVELOPMENT = "development"
    DEMO = "demo"


@dataclass
class OpenAIConfig:
    """Конфигурация OpenAI."""
    api_key: str
    model_name: str = "gpt-4o-mini-2024-07-18"


@dataclass
class HHConfig:
    """Конфигурация для HeadHunter API."""
    client_id: str
    client_secret: str
    redirect_uri: str
    base_redirect_path: str = "/callback"
    
    def update_redirect_uri(self, new_base_url: str):
        """Обновляет redirect_uri с новым базовым URL."""
        self.redirect_uri = f"{new_base_url}{self.base_redirect_path}"


@dataclass
class BotConfig:
    """Конфигурация бота."""
    token: str


@dataclass
class Config:
    """Общая конфигурация приложения."""
    bot: BotConfig
    hh: HHConfig
    openai: OpenAIConfig
    environment: Environment
    
    @classmethod
    def get_environment(cls) -> Environment:
        """
        Определяет текущее окружение из переменной окружения.
        Очищает значение от возможных комментариев и лишних пробелов.
        """
        raw_env = getenv("APP_ENVIRONMENT", "development")
        clean_env = raw_env.split()[0].strip().lower()
        return Environment.DEMO if clean_env == "demo" else Environment.DEVELOPMENT


def load_config() -> Config:
    """Загружает конфигурацию из переменных окружения."""
    environment = Config.get_environment()
    logger.info(f"Приложение запускается в режиме: {environment.value}")
    
    # Проверяем наличие критических переменных окружения
    critical_vars = ["BOT_TOKEN", "HH_CLIENT_ID", "HH_CLIENT_SECRET"]
    missing_vars = [var for var in critical_vars if not getenv(var)]
    
    if missing_vars:
        logger.error(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")
        raise ValueError("Не все обязательные переменные окружения установлены")
    
    default_redirect_uri = (
        "http://localhost:8000/callback" 
        if environment == Environment.DEVELOPMENT 
        else None
    )
    
    config = Config(
        bot=BotConfig(token=getenv("BOT_TOKEN")),
        hh=HHConfig(
            client_id=getenv("HH_CLIENT_ID"),
            client_secret=getenv("HH_CLIENT_SECRET"),
            redirect_uri=default_redirect_uri
        ),
        openai=OpenAIConfig(
            api_key=getenv("OPENAI_API_KEY"),
            model_name=OpenAIConfig.model_name
        ),
        environment=environment
    )
    
    return config