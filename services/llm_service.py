# services/llm_service.py
import logging
from pydantic import ValidationError
from typing import Optional
from openai import OpenAI
from config.config import Config
from models.resume_vacancy import ResumeInfo
from core.logger import setup_logger

logger = setup_logger(__name__)

class LLMService:
    """
    Сервис для взаимодействия с языковой моделью.
    
    Обеспечивает переписывание резюме с учетом требований вакансии,
    используя OpenAI GPT API.
    """
    
    def __init__(self, config: Config):
        """
        Инициализация сервиса LLM.
        
        Args:
            config: Конфигурация приложения с API ключом
        """
        self.client = OpenAI(api_key=config.openai.api_key)
        self.model = config.openai.model_name
    
    def _create_prompt(self, parsed_resume: dict, parsed_vacancy: dict) -> str:
        """
        Создает промпт для языковой модели.
        
        Args:
            parsed_resume: Данные резюме
            parsed_vacancy: Данные вакансии
            
        Returns:
            str: Подготовленный промпт
        """
        return f"""Вы — профессиональный HR-специалист, который адаптирует резюме под конкретную вакансию.

        Исходное резюме:
        1. Заголовок: {parsed_resume.get('title')}
        2. Ключевые навыки: {parsed_resume.get('skills')}
        3. Набор навыков: {parsed_resume.get('skill_set')}
        4. Опыт работы: {parsed_resume.get('descriptions')}

        Требования вакансии:
        1. Описание: {parsed_vacancy.get('description')}
        2. Требуемые навыки: {parsed_vacancy.get('key_skills')}

        Задача:
        1. Переписать резюме, подчеркивая релевантный опыт и навыки для данной вакансии
        2. Использовать ключевые слова из описания вакансии
        3. Сохранить профессиональный тон
        4. Добавить конкретные достижения, связанные с требованиями
        5. Убедиться, что все навыки из вакансии, которыми обладает кандидат, отражены в резюме

        Верните JSON строго по следующей схеме:
        {{
            "title": "string или null",
            "skills": "string или null",
            "skill_set": ["string", ...] или null,
            "descriptions": ["string", ...] или null (строго 5 элементов с описанием опыта)
        }}

        Важно: сохраняйте только фактическую информацию из резюме, не добавляйте выдуманный опыт."""
    
    def rewrite_resume(self, parsed_resume: dict, parsed_vacancy: dict) -> Optional[ResumeInfo]:
        """
        Переписывает резюме с учетом требований вакансии.
        
        Args:
            parsed_resume: Данные резюме
            parsed_vacancy: Данные вакансии
            
        Returns:
            Optional[ResumeInfo]: Переписанное резюме или None в случае ошибки
        """
        try:
            prompt = self._create_prompt(parsed_resume, parsed_vacancy)
            
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Вы — профессиональный HR-специалист, который адаптирует резюме под требования вакансии."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format=ResumeInfo
            )
            
            response_text = completion.choices[0].message.content
            logger.debug(f"Получен ответ от OpenAI: {response_text}")  # Добавляем логирование
            
            if not response_text:
                logger.error("Получен пустой ответ от OpenAI")
                return None
                
            try:
                rewritten_resume = ResumeInfo.model_validate_json(response_text)
                logger.info("Резюме успешно переписано")
                return rewritten_resume
            except ValidationError as e:
                logger.error(f"Ошибка валидации данных: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при обращении к OpenAI API: {e}")
            return None