from typing import Any
from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from core.logger import setup_logger
from core.states import UserState
from keyboards.reply import get_initial_keyboard

logger = setup_logger(__name__)

async def no_state_message_handler(message: Message, state: FSMContext) -> Any:
    """
    Обработчик сообщений, когда у пользователя нет никакого состояния (State = None).
    Переводит пользователя в состояние initial и просит нажать /start.
    """
    try:
        await state.set_state(UserState.initial)
        await message.answer(
            "Бот был перезапущен или ваше состояние сброшено.\n"
            "Теперь вы в начальном состоянии. Пожалуйста, нажмите /start.",
            reply_markup=get_initial_keyboard()
        )
        logger.info(
            f"[no_state_message_handler] Пользователь {message.from_user.id} переведён в состояние initial (из None)."
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения в no_state_message_handler: {e}")
        await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")
