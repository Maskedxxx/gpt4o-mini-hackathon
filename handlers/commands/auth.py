# handlers/commands/auth.py

from typing import Any, Optional
from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import os

from core.states import UserState
from services.hh_api import HeadHunterAPI
from services.callback_server import CallbackServer
from core.logger import setup_logger
from keyboards.reply import get_main_keyboard
from core.text import (
    ERROR_MSG,
    CHOOSE_ACTION_MSG,
    AUTH_SUCCESS_MSG,
    AUTH_ERROR_MSG,
    AUTH_INTRO_MSG,
    AUTH_SERVER_ERROR_MSG
)
from config.config import Config, Environment

logger = setup_logger(__name__)

class AuthCommandHandler:
    def __init__(self, bot: Bot, hh_api: HeadHunterAPI, config: Config):
        self.bot = bot
        self.hh_api = hh_api
        self.config = config
        
        # Определяем хост и порт в зависимости от окружения
        host = '0.0.0.0'  # Всегда используем 0.0.0.0 для привязки ко всем интерфейсам
        port = int(os.environ.get('PORT', 8000))  # Получаем порт из переменной окружения
        
        self.callback_server = CallbackServer(
            host=host,
            port=port
        )
        self._current_user_id: Optional[int] = None
        self._current_state: Optional[FSMContext] = None
    
    async def _handle_auth_code(self, code: str):
        try:
            if self._current_user_id and self._current_state:
                # Обмениваем код на токены
                tokens = await self.hh_api.exchange_code_for_tokens(code)
                # Устанавливаем состояние authorized
                await self._current_state.set_state(UserState.authorized)
                
                # Отправляем сообщение с клавиатурой
                await self.bot.send_message(
                    self._current_user_id,
                    AUTH_SUCCESS_MSG + CHOOSE_ACTION_MSG,
                    reply_markup=get_main_keyboard()
                )
                logger.info(f"Пользователь {self._current_user_id} успешно авторизован")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке кода авторизации: {e}")
            if self._current_user_id:
                await self.bot.send_message(
                    self._current_user_id,
                    AUTH_ERROR_MSG
                )
    
    async def handle_auth(self, message: Message, state: FSMContext) -> Any:
        """Обработчик команды авторизации."""
        try:
            self._current_user_id = message.from_user.id
            self._current_state = state
            await state.set_state(UserState.unauthorized)
            
            # Запускаем сервер для обработки callback
            server_started = await self.callback_server.start(self._handle_auth_code)
            
            if not server_started:
                await message.answer(AUTH_SERVER_ERROR_MSG)
                return
            
            # В демо режиме используем URL из конфигурации
            if self.config.environment == Environment.DEMO:
                domain = os.environ.get('RENDER_EXTERNAL_URL')
                if domain:
                    self.hh_api.redirect_uri = f"{domain}/callback"
                    logger.info(f"Установлен redirect_uri: {self.hh_api.redirect_uri}")
            
            # Получаем URL для авторизации
            auth_url = self.hh_api.get_auth_url()
            
            # Сообщение для пользователя
            auth_message = AUTH_INTRO_MSG + auth_url
            
            await message.answer(auth_message)
            logger.info(f"Пользователь {message.from_user.id} начал процесс авторизации")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке команды auth: {e}")
            await message.answer(ERROR_MSG)
