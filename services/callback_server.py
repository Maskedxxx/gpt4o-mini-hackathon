# services/callback_server.py
from aiohttp import web
from typing import Optional, Callable
from core.logger import setup_logger
import requests
import os

logger = setup_logger(__name__)

class CallbackServer:
    """
    Веб-сервер для обработки callback от OAuth2 авторизации HeadHunter.
    
    Запускает сервер, который ожидает получения кода авторизации
    и передает его в обработчик.
    """
    
    def __init__(self, host: str = '0.0.0.0', port: int = None):
        self.host = host
        # Получаем порт из переменной окружения Render или используем 8000
        self.port = int(os.environ.get('PORT', 8000))
        self.app = web.Application()
        self.callback_handler: Optional[Callable] = None
        self._setup_routes()
        self._is_running: bool = False
        self._runner: Optional[web.AppRunner] = None
        
    def _setup_routes(self):
        """Настройка маршрутов веб-сервера."""
        self.app.router.add_get('/', self._handle_callback)
    
    async def _handle_callback(self, request: web.Request) -> web.Response:
        """Обработчик callback запроса от OAuth2."""
        try:
            code = request.query.get('code')
            logger.info(f"Получен код авторизации: {code}")
            
            if code and self.callback_handler:
                logger.info("Начинаем обработку полученного кода")
                await self.callback_handler(code)
                return web.Response(
                    text="Авторизация успешно завершена. Вы можете закрыть это окно и вернуться в бот.",
                    content_type='text/html'
                )
            
            logger.error("Код авторизации отсутствует в запросе")
            return web.Response(
                text="Ошибка авторизации. Пожалуйста, попробуйте снова.",
                status=400
            )
        except Exception as e:
            logger.error(f"Ошибка при обработке callback: {e}")
            return web.Response(text="Произошла ошибка", status=500)
    
    async def start(self, callback_handler: Callable) -> bool:
        """
        Запуск сервера, если он еще не запущен.
        
        Args:
            callback_handler: Функция для обработки полученного кода авторизации
            
        Returns:
            bool: True если сервер был запущен или уже работает, False в случае ошибки
        """
        if self._is_running:
            logger.info("Callback сервер уже запущен")
            self.callback_handler = callback_handler
            return True
            
        try:
            self.callback_handler = callback_handler
            self._runner = web.AppRunner(self.app)
            await self._runner.setup()
            # Используем self.host вместо хардкода localhost
            site = web.TCPSite(self._runner, self.host, self.port)
            await site.start()
            self._is_running = True
            logger.info(f"Callback сервер запущен на {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при запуске callback сервера: {e}")
            return False
            
    async def stop(self):
        """Остановка сервера."""
        if self._is_running and self._runner:
            await self._runner.cleanup()
            self._is_running = False
            logger.info("Callback сервер остановлен")