# handlers/commands/start.py
from typing import Any
from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from core.states import UserState
from core.logger import setup_logger
from keyboards.reply import get_initial_keyboard, get_unauthorized_keyboard

logger = setup_logger(__name__)

class StartCommandHandler:
    """
    Обработчик команды /start.
    
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
    
    async def handle_start(self, message: Message, state: FSMContext) -> Any:
        """
        Обработка команды /start.
        
        Args:
            message: Входящее сообщение
            state: Состояние пользователя
            
        Returns:
            None
        """
        # Получаем текущее состояние
        current_state = await state.get_state()
        
        # Устанавливаем начальное состояние
        await state.set_state(UserState.initial)
        
        # Формируем приветственное сообщение
        greeting_text = (
            f"👋 Здравствуйте, {message.from_user.full_name}!\n\n"
            "Я бот для создания персонализированных резюме. "
            "Я помогу вам создать профессиональное резюме, "
            "которое выделит вас среди других кандидатов.\n\n"
        )
        
        # Добавляем информацию об авторизации (если юзер нажал start в процессе авторизации)
        if current_state == UserState.unauthorized:
            greeting_text += (
                "🔄 Процесс авторизации был прерван.\n"
                "Для продолжения работы необходимо пройти авторизацию заново."
            )
        else:
            greeting_text += "Для начала работы вам необходимо пройти авторизацию."
        
        # Отправляем приветственное сообщение
        # Отправляем сообщение + клавиатура
        try:
            await message.answer(
                greeting_text,
                reply_markup=get_unauthorized_keyboard()
            )
            logger.info(f"Отправлено приветственное сообщение пользователю {message.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке приветственного сообщения: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")