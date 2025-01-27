# tests/llm_agent_final_rewrite.py

import logging
from typing import Optional
from pydantic import ValidationError
from openai import OpenAI

from config.config import Config
from models.resume import ResumeUpdate
from models.gap_analysis import ResumeGapAnalysis
from core.logger import setup_logger

logger = setup_logger(__name__)

class LLMService:
    """
    Сервис для взаимодействия с языковой моделью.
    """
    def __init__(self, config: Config):
        self.client = OpenAI(api_key=config.openai.api_key)
        self.model = config.openai.model_name

    # ... методы gap_analysis, rewrite_resume и т.д. ...

    def _create_final_rewrite_prompt(
        self, 
        parsed_resume: dict, 
        gap_result: ResumeGapAnalysis, 
    ) -> str:
        """
        Формирует промпт для финального рерайта резюме, учитывая результаты GAP-анализа.
        """
        return f"""
        You are tasked with rewriting a resume based on a gap analysis to better match a job description. You will be provided with three inputs:

        Here are the results of the GAP analysis:
            <gap_analysis>
            {gap_result.recommendations} 
            </gap_analysis>

        Here is the candidate's original resume:
            <original_resume>
            title: {parsed_resume.get("title")}
            skills: {parsed_resume.get("skills")}
            skill_set: {parsed_resume.get("skill_set")}
            experience: {parsed_resume.get("experience")}
            employments: {parsed_resume.get("employments")}
            schedules: {parsed_resume.get("schedules")}
            languages: {parsed_resume.get("languages")}
            relocation: {parsed_resume.get("relocation")}
            salary: {parsed_resume.get("salary")}
            professional_roles: {parsed_resume.get("professional_roles")}
            </original_resume>


        Your goal is to rewrite the resume according to the recommendations in the gap analysis while maintaining the overall structure and authenticity of the original resume. Follow these guidelines:

        1. Read through the original resume, gap analysis, and job description carefully.

        2. For each section of the resume mentioned in the gap analysis, rewrite the content to address the recommendations while preserving the essence of the original information.

        3. Pay special attention to the "experience" section. For each experience entry:
        a. Maintain the same number of entries as in the original resume.
        b. Use the original information as a base, but enhance it according to the gap analysis recommendations.
        c. Integrate the recommendations seamlessly, as if they were part of the original experience.
        d. Add specific metrics, achievements, and technical details that align with the job description.
        e. Ensure the rewritten experience sounds natural and authentic, not forced or exaggerated.

        4. For other sections (e.g., skills, education), make adjustments as recommended in the gap analysis, but be careful not to add false information.

        5. Maintain a consistent tone and style throughout the rewritten resume that matches the original.

        6. Do not add entirely new sections or experiences that were not present in the original resume.

        When you have completed the rewrite, present the new resume in the following format:

        <rewritten_resume>
        <<<ResumeUpdate>>>
        </rewritten_resume>

        Remember, the goal is to create a more competitive resume that better matches the job description while remaining truthful to the candidate's actual experience and qualifications.
            """


    def final_resume_rewrite(
        self, 
        parsed_resume: dict, 
        gap_analysis: ResumeGapAnalysis, 
    ) -> Optional[ResumeUpdate]:
        """
        Финальный рерайт резюме с учётом результатов GAP-анализа.
        Возвращает объект ResumeInfo или None при ошибке.
        """
        try:
            prompt = self._create_final_rewrite_prompt(parsed_resume, gap_analysis)

            # Генерируем системное и пользовательское сообщение
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Ты — эксперт HR по созданию индивидуального резюме. "
                        "Учитывай GAP-анализ и требования вакансии. "
                        "Возвращай только валидный JSON с нужной структурой."
                    )
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # Вызываем ChatCompletion с указанием модели
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                temperature = 0.4,
                presence_penalty = 0.9,
                frequency_penalty = 0.5,
                logprobs = True,
                top_logprobs= 2,
                response_format=ResumeUpdate  # <-- pydantic модель для парсинга ответа
            )

            response_text = completion.choices[0].message.content
            logger.debug(f"Ответ от OpenAI (финальный рерайт): {response_text}")

            if not response_text:
                logger.error("Получен пустой ответ при финальном рерайте.")
                return None

            try:
                final_resume = ResumeUpdate.model_validate_json(response_text)
                logger.info("Финальный рерайт выполнен успешно.")
                return final_resume
            except ValidationError as e:
                logger.error(f"Ошибка валидации JSON финального рерайта: {e}")
                return None

        except Exception as e:
            logger.error(f"Ошибка при обращении к OpenAI API (финальный рерайт): {e}")
            return None
