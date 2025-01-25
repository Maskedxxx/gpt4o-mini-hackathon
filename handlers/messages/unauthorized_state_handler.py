# handlers/messages/unauthorized_state_handler.py
from typing import Any
from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from core.states import UserState
from core.logger import setup_logger

logger = setup_logger(__name__)

class UnauthorizedStateMessageHandler:
    """
    Обработчик текстовых сообщений в состоянии unauthorized.
    
    Обрабатывает все текстовые сообщения, когда пользователь находится
    в состоянии unauthorized и ожидает завершения процесса авторизации.
    
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
        Обработка входящих текстовых сообщений в состоянии unauthorized.
        
        Args:
            message: Входящее сообщение
            state: Состояние пользователя
            
        Returns:
            None
        """
        auth_reminder = (
            "🔒 Для продолжения работы необходимо завершить авторизацию.\n\n"
            "Пожалуйста, перейдите по ссылке, которая была отправлена ранее, "
            "и подтвердите доступ к вашему аккаунту HeadHunter."
        )
        
        try:
            await message.answer(auth_reminder)
            logger.info(f"Отправлено напоминание об авторизации пользователю {message.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке напоминания об авторизации: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")