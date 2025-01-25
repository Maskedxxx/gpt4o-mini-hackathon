# handlers/messages/initial_state_handler.py
from typing import Any
from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from core.states import UserState
from core.logger import setup_logger

logger = setup_logger(__name__)

class InitialStateMessageHandler:
    """
    Обработчик текстовых сообщений в начальном состоянии.
    
    Обрабатывает все текстовые сообщения, когда пользователь находится
    в состоянии initial и не прошел авторизацию.
    
    Attributes:
        bot: Экземпляр бота для отправки сообщений
    """
    
    def __init__(self, bot: Bot):
        """
        Инициализация обработчика.
        
        Args:
            bot: Экземпляр бота
        """
        self.bot = bot
    
    async def handle_message(self, message: Message, state: FSMContext) -> Any:
        """
        Обработка входящих текстовых сообщений в состоянии initial.
        
        Args:
            message: Входящее сообщение
            state: Состояние пользователя
            
        Returns:
            None
        """
        auth_message = (
            "⚠️ Для использования бота необходимо пройти авторизацию.\n\n"
            "Пожалуйста, нажмите кнопку '/auth' ниже."
        )
        
        try:
            # В будущем здесь можно добавить кнопку для авторизации
            await message.answer(auth_message)
            logger.info(f"Отправлено сообщение о необходимости авторизации пользователю {message.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения об авторизации: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")