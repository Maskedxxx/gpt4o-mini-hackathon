# tests/llm_agent_recomendation.py

import logging
from pydantic import ValidationError
from typing import Optional
from openai import OpenAI
from config.config import Config
from models.resume import ResumeInfo
from models.gap_analysis import GapAnalysisResult
from models.recommendations import RecommendationsResult
from core.logger import setup_logger

logger = setup_logger(__name__)

class LLMService:
    """
    Сервис для взаимодействия с языковой моделью.
    """

    def __init__(self, config: Config):
        self.client = OpenAI(api_key=config.openai.api_key)
        self.model = config.openai.model_name

    # --- Пропускаем существующие методы rewrite_resume(...) и gap_analysis(...)

    def _create_recommendations_prompt(
        self, 
        gap_result: GapAnalysisResult, 
    ) -> str:
            """
            Формирует промпт для запроса к модели, чтобы получить рекомендации
            на основе результатов GAP-анализа.
            """
            return f"""
            Ты — ассистент по составлению резюме. У тебя есть результат GAP-анализа (выявлены matched_skills, missing_skills, irrelevant_blocks, critical_mismatches).
            На их основе и учитывая исходное резюме/вакансию, составь рекомендации:
            1) Что нужно подчеркнуть или улучшить в резюме (to_highlight);
            2) Что нужно удалить или сократить (to_remove);
            3) Какие конкретные части резюме стоит переписать и почему (to_rewrite);
            4) Общие советы по стилю, структуре, подаче (general_advice).

            ### Данные GAP-анализа:
            - matched_skills: {gap_result.matched_skills}
            - missing_skills: {gap_result.missing_skills}
            - irrelevant_blocks: {gap_result.irrelevant_blocks}
            - critical_mismatches: {gap_result.critical_mismatches}


            Сформируй рекомендации в формате **строгого JSON** следующего вида (без лишних полей):
            {{
            "to_highlight": ["string", ...],
            "to_remove": ["string", ...],
            "to_rewrite": ["string", ...],
            "general_advice": ["string", ...]
            }}

            Никаких пояснений вне JSON не давай.
            """

    def make_recommendations(
        self, 
        gap_result: GapAnalysisResult, 
    ) -> Optional[RecommendationsResult]:
        """
        Генерирует рекомендации по улучшению резюме на основе GAP-анализа.
        """
        try:
            prompt = self._create_recommendations_prompt(gap_result)

            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты — эксперт по корректировке резюме."
                            " Возвращай ответы в формате строжайшего JSON, без добавления вне-json текста."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format=RecommendationsResult
            )

            response_text = completion.choices[0].message.content
            logger.debug(f"Ответ от OpenAI (recommendations): {response_text}")

            if not response_text:
                logger.error("Получен пустой ответ от модели при генерации рекомендаций.")
                return None

            try:
                recs = RecommendationsResult.model_validate_json(response_text)
                logger.info("Рекомендации успешно сгенерированы.")
                return recs
            except ValidationError as e:
                logger.error(f"Ошибка валидации рекомендаций: {e}")
                return None

        except Exception as e:
            logger.error(f"Ошибка при обращении к OpenAI API для рекомендаций: {e}")
            return None
