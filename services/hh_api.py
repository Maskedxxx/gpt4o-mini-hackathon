# services/hh_api.py
from typing import Dict, Optional, Any
import requests
from urllib.parse import quote
from core.logger import setup_logger

logger = setup_logger(__name__)

class HeadHunterAPI:
    """
    Класс для работы с API HeadHunter.
    
    Обеспечивает полный цикл авторизации и взаимодействия с API HeadHunter,
    включая управление токенами и их обновление.
    """

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """Инициализация клиента API HeadHunter."""
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.base_url = 'https://api.hh.ru'
        self.token_url = 'https://hh.ru/oauth/token'
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None

    @property
    def access_token(self) -> Optional[str]:
        """Получение текущего access token."""
        return self._access_token

    @property
    def is_authenticated(self) -> bool:
        """Проверка наличия действующего токена."""
        return bool(self._access_token and self._refresh_token)

    def get_auth_url(self) -> str:
        """Генерация URL для авторизации пользователя."""
        auth_url = (
            f'https://hh.ru/oauth/authorize?'
            f'response_type=code&'
            f'client_id={self.client_id}&'
            f'redirect_uri={self.redirect_uri}'
        )
        logger.info("Сгенерирован URL авторизации")
        return auth_url

    async def exchange_code_for_tokens(self, authorization_code: str) -> Dict[str, str]:
        """
        Обмен кода авторизации на токены доступа.
        """
        try:
            payload = {
                'grant_type': 'authorization_code',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': authorization_code,
                'redirect_uri': self.redirect_uri
            }
            
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json"
            }
            
            # Добавляем логирование запроса
            logger.info(f"Отправка запроса на получение токенов. URL: {self.token_url}")
            logger.info(f"Параметры запроса: {payload}")
            
            response = requests.post(self.token_url, data=payload, headers=headers)
            
            # Логируем ответ сервера
            logger.info(f"Статус ответа: {response.status_code}")
            logger.info(f"Тело ответа: {response.text}")
            
            response.raise_for_status()
            
            tokens = response.json()
            self._access_token = tokens.get('access_token')
            self._refresh_token = tokens.get('refresh_token')
            
            logger.info("Успешно получены токены доступа")
            return tokens
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"Ошибка при получении токенов: {e}")
            logger.error(f"Детали ошибки: {e.response.text if hasattr(e, 'response') else 'Нет деталей'}")
            raise

    async def refresh_access_token(self) -> Dict[str, str]:
        """
        Обновление access_token с использованием refresh_token.
        
        Returns:
            Dict[str, str]: Новые токены доступа
            
        Raises:
            ValueError: Если отсутствует refresh_token
            requests.exceptions.HTTPError: При ошибке запроса к API
        """
        if not self._refresh_token:
            logger.error("Попытка обновления токена без refresh_token")
            raise ValueError("Refresh token отсутствует. Необходима повторная авторизация.")

        try:
            payload = {
                'grant_type': 'refresh_token',
                'refresh_token': self._refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.post(self.token_url, data=payload)
            response.raise_for_status()
            
            tokens = response.json()
            self._access_token = tokens.get('access_token')
            self._refresh_token = tokens.get('refresh_token')
            
            logger.info("Токены успешно обновлены")
            return tokens
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Ошибка при обновлении токенов: {e}")
            self._access_token = None
            self._refresh_token = None
            raise

    async def make_api_request(
        self, 
        endpoint: str, 
        method: str = 'GET', 
        data: Optional[Dict] = None, 
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Выполнение запроса к API HeadHunter с автоматическим обновлением токена.
        
        Args:
            endpoint: Конечная точка API
            method: HTTP метод (GET, POST, PUT, DELETE)
            data: Данные для отправки в теле запроса
            params: Параметры строки запроса
            
        Returns:
            Dict[str, Any]: Ответ от API в формате JSON
            
        Raises:
            ValueError: Если отсутствует access_token
            requests.exceptions.HTTPError: При ошибке запроса к API
        """
        if not self._access_token:
            logger.error("Попытка выполнения запроса без access_token")
            raise ValueError("Access token отсутствует. Необходима авторизация.")

        headers = {
            'Authorization': f'Bearer {self._access_token}',
            'User-Agent': 'ResumeBot/1.0'
        }
        url = f'{self.base_url}{endpoint}'

        try:
            response = None
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Неподдерживаемый HTTP метод: {method}")
            
            logger.info(f"Статус ответа: {response.status_code}")
            logger.info(f"Текст ответа: {response.url}")

            # Если токен истёк, пробуем обновить и повторить запрос
            if response.status_code == 401:
                logger.info("Токен истёк, выполняется обновление")
                await self.refresh_access_token()
                return await self.make_api_request(endpoint, method, data, params)

            response.raise_for_status()

            # Если статус 204, тело пустое => возвращаем пустой словарь
            if response.status_code == 204:
                logger.info("Резюме успешно обновлено на HH!")
                return {}

            # Если текст пустой, тоже возвращаем пустой словарь, чтобы не упасть на JSONDecodeError
            if not response.text.strip():
                logger.info("Получен пустой ответ, возвращаем пустой словарь.")
                return {}

            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"Ошибка при выполнении запроса к API: {e}")
            raise