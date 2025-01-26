# handlers/messages/authorized_state_handler.py
from typing import Any
from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from core.states import UserState
from core.logger import setup_logger
from keyboards.reply import get_main_keyboard
from services.hh_api import HeadHunterAPI
from core.text import (
    EDIT_RESUME_BTN,
    CREATE_RESUME_BTN,
    DEFAULT_RESPONSE,
    ERROR_MSG,
    WAITING_RESUME_LINK
)

logger = setup_logger(__name__)

class AuthorizedStateMessageHandler:
    """Обработчик сообщений в авторизованном состоянии"""
    
    def __init__(self, bot: Bot, hh_api: HeadHunterAPI):
        self.bot = bot
        self.hh_api = hh_api
    
    async def handle_message(self, message: Message, state: FSMContext) -> Any:
        """Обработка входящих сообщений"""
        try:
            if message.text in [EDIT_RESUME_BTN, CREATE_RESUME_BTN]:
                if message.text == EDIT_RESUME_BTN:
                    await self._handle_edit_resume(message, state)
                else:
                    await message.answer(
                        "Функция создания резюме будет доступна в ближайшее время!",
                        reply_markup=get_main_keyboard()
                    )
                logger.info(f"Обработано нажатие кнопки '{message.text}' от пользователя {message.from_user.id}")
            else:
                await message.answer(DEFAULT_RESPONSE, reply_markup=get_main_keyboard())
                logger.info(f"Обработано текстовое сообщение от пользователя {message.from_user.id}")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            await message.answer(ERROR_MSG, reply_markup=get_main_keyboard())
    
    async def _handle_edit_resume(self, message: Message, state: FSMContext) -> None:
        """Обработка нажатия кнопки изменения резюме"""
        await state.set_state(UserState.rewrite_resume)
        await message.answer(WAITING_RESUME_LINK)