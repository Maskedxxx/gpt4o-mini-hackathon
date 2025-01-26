# main.py
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from config.config import load_config, Config
from core.logger import setup_logger
from core.states import UserState
from services.hh_api import HeadHunterAPI
from services.llm_service import LLMService
from services.demo_service import DemoService

from handlers.commands.start import StartCommandHandler
from handlers.commands.auth import AuthCommandHandler

from handlers.messages.initial_state_handler import InitialStateMessageHandler
from handlers.messages.unauthorized_state_handler import UnauthorizedStateMessageHandler
from handlers.messages.authorized_state_handler import AuthorizedStateMessageHandler
from handlers.messages.rewrite_resume_handler import RewriteResumeHandler
from handlers.messages.no_state_handler import no_state_message_handler


logger = setup_logger(__name__)

async def register_command_handlers(dp: Dispatcher, bot: Bot, config: Config, hh_api: HeadHunterAPI) -> None:
    """
    Регистрация обработчиков команд бота.
    
    Args:
        dp: Диспетчер для регистрации обработчиков
        bot: Экземпляр бота для обработчиков
        config: Конфигурация приложения
    """
    
    # Инициализируем обработчики команд
    start_handler = StartCommandHandler(bot)
    auth_handler = AuthCommandHandler(bot, hh_api, config)
    
    # Регистрируем обработчики
    dp.message.register(
        start_handler.handle_start,
        Command(commands=["start"])
    )
    
    dp.message.register(
        auth_handler.handle_auth,
        Command(commands=["auth"])
    )
    
    logger.info("Зарегистрированы обработчики команд")

async def register_message_handlers(dp: Dispatcher, bot: Bot, config: Config, hh_api: HeadHunterAPI) -> None:
    """
    Регистрация обработчиков текстовых сообщений бота.
    
    Args:
        dp: Диспетчер для регистрации обработчиков
        bot: Экземпляр бота для обработчиков
        config: Конфигурация приложения
        hh_api: Экземпляр API клиента HeadHunter
    """
    # Создаем экземпляр LLMService
    llm_service = LLMService(config)
    
    # Инициализируем обработчики сообщений
    initial_state_handler = InitialStateMessageHandler(bot)
    unauthorized_state_handler = UnauthorizedStateMessageHandler(bot)
    authorized_state_handler = AuthorizedStateMessageHandler(bot, hh_api)
    rewrite_resume_handler = RewriteResumeHandler(bot, hh_api, llm_service)

    dp.message.register(
        no_state_message_handler,
        StateFilter(None)  # когда состояние у пользователя не установлено
    )

    # Регистрируем обработчик текстовых сообщений в состоянии initial
    dp.message.register(
        initial_state_handler.handle_message,
        StateFilter(UserState.initial)
    )
    
    dp.message.register(
        unauthorized_state_handler.handle_message,
        StateFilter(UserState.unauthorized)
    )
    
    dp.message.register(
        authorized_state_handler.handle_message,
        StateFilter(UserState.authorized)
    )
    
    # Регистрируем обработчик для состояния rewrite_resume
    dp.message.register(
        rewrite_resume_handler.handle_message,
        StateFilter(UserState.rewrite_resume)
    )
    
    logger.info("Зарегистрированы обработчики сообщений")

async def register_handlers(dp: Dispatcher, bot: Bot, config: Config) -> None:
    """
    Регистрация всех обработчиков бота.
    
    Args:
        dp: Диспетчер для регистрации обработчиков
        bot: Экземпляр бота для обработчиков
    """
    
    hh_api = HeadHunterAPI(
        client_id=config.hh.client_id,
        client_secret=config.hh.client_secret,
        redirect_uri=config.hh.redirect_uri
    )
    
    # Регистрируем обработчики команд
    await register_command_handlers(dp, bot, config, hh_api)
    
    # Регистрируем обработчики сообщений
    await register_message_handlers(dp, bot, config, hh_api)
    
    logger.info("Все обработчики успешно зарегистрированы")

async def main():
    """
    Основная функция запуска бота.
    Инициализирует бота и запускает его с поддержкой FSM.
    """
    # Загружаем конфигурацию
    config = load_config()
    
    demo_service = DemoService(config)
    await demo_service.setup()
    
    # Инициализируем хранилище состояний
    storage = MemoryStorage()
    
    # Инициализируем бота и диспетчер с хранилищем состояний
    bot = Bot(token=config.bot.token)
    dp = Dispatcher(storage=storage)
    
    # Регистрируем все обработчики
    await register_handlers(dp, bot, config)
    
    logger.info(f"Бот запущен в режиме: {config.environment.value}")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}")
    finally:
        await demo_service.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())