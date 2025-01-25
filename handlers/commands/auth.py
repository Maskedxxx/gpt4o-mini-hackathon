# handlers/commands/auth.py
from typing import Any, Optional
from aiogram import Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from core.states import UserState
from services.hh_api import HeadHunterAPI
from services.callback_server import CallbackServer
from core.logger import setup_logger
from keyboards.reply import get_main_keyboard
from core.text import CHOOSE_ACTION_MSG
from config.config import Config, Environment

logger = setup_logger(__name__)

class AuthCommandHandler:
    def __init__(self, bot: Bot, hh_api: HeadHunterAPI, config: Config):
        """
        Инициализация обработчика команды авторизации.
        
        Args:
            bot: Экземпляр бота
            hh_api: Клиент API HeadHunter
            config: Конфигурация приложения
        """
        self.bot = bot
        self.hh_api = hh_api
        self.config = config
        # Создаем колбек-сервер с учетом режима работы
        self.callback_server = CallbackServer(
            host='0.0.0.0' if config.environment == Environment.DEMO else 'localhost'
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
                    "✅ Авторизация успешно завершена!\n\n" + CHOOSE_ACTION_MSG,
                    reply_markup=get_main_keyboard()
                )
                logger.info(f"Пользователь {self._current_user_id} успешно авторизован")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке кода авторизации: {e}")
            if self._current_user_id:
                await self.bot.send_message(
                    self._current_user_id,
                    "❌ Произошла ошибка при авторизации. Пожалуйста, попробуйте снова позже."
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
                await message.answer(
                    "Произошла ошибка при запуске сервера авторизации. "
                    "Пожалуйста, попробуйте позже."
                )
                return
            
            # Обновляем redirect_uri в API клиенте если мы в демо-режиме
            if self.config.environment == Environment.DEMO:
                self.hh_api.redirect_uri = self.config.hh.redirect_uri
            
            # Получаем URL для авторизации
            auth_url = self.hh_api.get_auth_url()
            
            auth_message = (
                "🔐 Для доступа к функциям бота необходима авторизация.\n\n"
                "1. Перейдите по ссылке ниже\n"
                "2. Разрешите доступ приложению\n"
                "3. Дождитесь сообщения об успешной авторизации\n\n"
                f"{auth_url}"
            )
            
            await message.answer(auth_message)
            logger.info(f"Пользователь {message.from_user.id} начал процесс авторизации")
            
        except Exception as e:
            logger.error(f"Ошибка при обработке команды auth: {e}")
            await message.answer("Произошла ошибка. Пожалуйста, попробуйте позже.")