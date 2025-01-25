# services/llm_service.py

import logging
from typing import Optional

from openai import OpenAI
from pydantic import ValidationError

from config.config import Config
from models.gap_analysis import GapAnalysisResult, ResumeGapAnalysis  # Модель для результата GAP-анализа
from models.resume import ResumeUpdate            # Модель для финального переписанного резюме
from core.logger import setup_logger

logger = setup_logger(__name__)

class LLMService:
    """
    Сервис для взаимодействия с языковой моделью (OpenAI).
    Содержит методы для:
      1) GAP-анализа резюме относительно вакансии.
      2) Финального рерайта (Final Resume Rewrite) с учётом результатов GAP-анализа.
    """

    def __init__(self, config: Config):
        """
        Инициализация клиента OpenAI.
        
        Args:
            config: Объект конфигурации, содержащий API ключ и т.д.
        """
        self.client = OpenAI(api_key=config.openai.api_key)
        self.model = config.openai.model_name
    
    def gap_analysis(self, parsed_resume: dict, parsed_vacancy: dict) -> Optional[ResumeGapAnalysis]:
        """
        Выполняет GAP-анализ резюме относительно вакансии.
        
        Args:
            parsed_resume: Словарь с распарсенными данными резюме.
            parsed_vacancy: Словарь с распарсенными данными вакансии.
        
        Returns:
            Объект GapAnalysisResult, если удалось распарсить корректный JSON-ответ.
            Иначе None.
        """
        try:
            # 1. Сформировать промпт для GAP-анализа
            prompt_text = self._create_gap_analysis_prompt(parsed_resume, parsed_vacancy)
            
            # 2. Подготовить сообщения для chat-completion
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Ты — эксперт, который анализирует соответствие резюме и вакансии. "
                        "Возвращай только валидный JSON по заданной структуре (GapAnalysisResult)."
                    )
                },
                {
                    "role": "user",
                    "content": prompt_text
                }
            ]
            
            # 3. Вызвать OpenAI API (chat.completions.parse) с явной моделью GapAnalysisResult
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                temperature=0,
                response_format=ResumeGapAnalysis
            )

            # 4. Извлечь ответ
            raw_response_text = completion.choices[0].message.content
            if not raw_response_text:
                logger.error("Пустой ответ от модели при GAP-анализе.")
                return None
            
            # 5. Попробовать распарсить JSON в модель GapAnalysisResult
            gap_result = ResumeGapAnalysis.model_validate_json(raw_response_text)
            logger.info("GAP-анализ успешно выполнен.")
            return gap_result

        except ValidationError as ve:
            logger.error(f"Ошибка валидации GAP-анализа: {ve}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при GAP-анализе: {e}")
            return None
    
    def final_resume_rewrite(
        self, 
        parsed_resume: dict, 
        gap_result: ResumeGapAnalysis
    ) -> Optional[ResumeUpdate]:
        """
        Выполняет финальный рерайт резюме, используя результаты GAP-анализа.
        
        Args:
            parsed_resume: Исходные данные резюме (dict).
            gap_result: Результат GAP-анализа (Recommendation).
        
        Returns:
            Объект ResumeUpdate, если всё OK, иначе None.
        """
        try:
            # 1. Формируем промпт с учётом gap_result
            prompt_text = self._create_final_rewrite_prompt(parsed_resume, gap_result)

            # 2. Подготавливаем сообщения для chat-completion
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Ты — эксперт HR. Учитывай GAP-анализ и требования вакансии. "
                        "Возвращай только валидный JSON (Recommendation)."
                    )
                },
                {
                    "role": "user",
                    "content": prompt_text
                }
            ]

            # 3. Запрашиваем у OpenAI финальный рерайт
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                temperature=0.2,
                response_format=ResumeUpdate  # парсим сразу в модель ResumeUpdate
            )

            # 4. Извлекаем текст ответа
            raw_response_text = completion.choices[0].message.content
            if not raw_response_text:
                logger.error("Пустой ответ при финальном рерайте.")
                return None

            # 5. Парсим JSON в модель ResumeUpdate
            final_resume = ResumeUpdate.model_validate_json(raw_response_text)
            logger.info("Финальный рерайт выполнен успешно.")
            return final_resume

        except ValidationError as ve:
            logger.error(f"Ошибка валидации JSON финального рерайта: {ve}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при обращении к OpenAI API (финальный рерайт): {e}")
            return None

    # =========================================================================
    # ВНУТРЕННИЕ (private) МЕТОДЫ ДЛЯ СОЗДАНИЯ ПРОМПТОВ
    # =========================================================================

    def _create_gap_analysis_prompt(self, parsed_resume: dict, parsed_vacancy: dict) -> str:
        """
        Формирует промпт для GAP-анализа.
        Здесь можно вставить ваш кастомный текст.
        """
        return f"""
        You are an AI assistant specializing in resume optimization. 
        Your task is to analyze a candidate's resume, compare it to a specific job description, 
        and provide detailed, actionable recommendations on how to tailor the resume to better 
        match the job requirements.

        First, carefully read and analyze the following resume:
        
        <resume>
        <title>{parsed_resume.get("title")}</title>
        <skills>{parsed_resume.get("skills")}</skills>
        <skill_set>{parsed_resume.get("skill_set")}</skill_set>
        <experience>{parsed_resume.get("experience")}</experience>
        <professional_roles>{parsed_resume.get("professional_roles")}</professional_roles>
        </resume>

        Now, here is the job description to compare against:

        <job_description>
        <description>{parsed_vacancy.get("description")}</description>
        <key_skills>{parsed_vacancy.get("key_skills")}</key_skills>
        <employment_form>{parsed_vacancy.get("employment_form")}</employment_form>
        <experience>{parsed_vacancy.get("experience")}</experience>
        <schedule>{parsed_vacancy.get("schedule")}</schedule>
        <employment>{parsed_vacancy.get("employment")}</employment>
        <professional_roles>{parsed_vacancy.get("professional_roles")}</professional_roles>
        </job_description>

        
        Your goal is to help the candidate create a highly personalized resume that closely matches the requirements of the position they're applying for. Follow these steps:

        1. Extract key requirements from the job description, including required skills, qualifications, experience, responsibilities, and industry-specific knowledge or certifications.

        2. Identify relevant experiences and skills from the resume.

        3. Compare the resume to the job description by explicitly matching resume elements to job requirements.

        4. Identify gaps, mismatches, or areas where the resume could be improved to better align with the job requirements.

        5. Generate specific, actionable recommendations on how to enhance the resume.

        Before providing your final analysis and recommendations, break down your thought process in <resume_job_comparison> tags:

        - List key requirements from the job description
        - For each requirement, find matching elements in the resume
        - Note any gaps or mismatches between the job requirements and the resume
        
        <VERY IMPORTANT NOTE>:
        If you choose the “experience” section, be sure to go through all the objects in the array and specify what to change or update. 
        For example: “section”: “Experience[0]”, -> ‘section’: “Experience[1]”, and so on
        And if you choose the “skills” section, then in this section list all the things that need to be added or updated.
        </VERY IMPORTANT NOTE>
        
        It's OK for this section to be quite long. This will ensure a thorough interpretation of both the resume and job description.

        Present your final analysis and recommendations using the following Pydantic model structure:
        <<<ResumeGapAnalysis>>>

        Remember to provide comprehensive analysis in the <resume_job_comparison> section before presenting the final recommendations in the structured JSON format.
        """
    
    def _create_final_rewrite_prompt(
        self,
        parsed_resume: dict,
        gap_result: ResumeGapAnalysis
    ) -> str:
        """
        Формирует промпт для финального рерайта резюме, учитывая результаты GAP-анализа.
        """
        return f"""
        You are an expert HR professional specializing in creating personalized resumes. 
        Your task is to tailor a candidate's resume to a specific job vacancy using the original 
        resume and GAP analysis results. Your goal is to create the most effective and personalized
        resume possible without fabricating any information.

        Here are the results of the GAP analysis:
            <gap_analysis>
            recommendations: {gap_result.recommendations} 
            </gap_analysis>

        Here is the candidate's original resume:
            <original_resume>
            title: {parsed_resume.get("title")}
            skills: {parsed_resume.get("skills")}
            skill_set: {parsed_resume.get("skill_set")}
            experience: {parsed_resume.get("experience")}
            professional_roles: {parsed_resume.get("professional_roles")}
            </original_resume>

            Please follow these steps to create a personalized resume:

            **Analyze the original resume and GAP analysis results.**
            1.  a. Compare each section of the original resume to the GAP analysis recommendations, noting major discrepancies and areas for improvement.
                b. Implement specific changes from the GAP analysis, to each section of the summary.
                c.  The number of experience entries on the rewritten resume should match the number of entries on the original resume.
            2. Update each section of the resume to better reflect the candidate's abilities and their alignment with the job vacancy. The sections are:
            - title
            - skills
            - skill_set
            - experience
            - professional_roles
            
            4. Pay special attention to the “skills” and “experience” (VERY IMPORTANT “experience”) sections to maximize their relevance to the job requirements. For the “experience” section:
                - Confirm that each work experience record will be rewritten to address the recommendations of the GAP analysis, while retaining the essence and key skills from the original experience.
                - Carefully rewrite each entry to include references from the GAP analysis, while keeping the essence of the original experience.
                - Keep descriptions full length, avoiding abbreviations.
                - Don't just add a few words at the end of each entry, but change the very structure of the <experience> key text to fulfill the recommendations from the GAP analysis.
                - Make sure the number of items in the Experience section remains the same as in the original resume.
                - Do not modify the 'position' field in the experience array.

            5. Consider the following aspects of the GAP analysis when updating your resume:
                - Skills that need to be emphasized or enhanced THIS IS IMPORTANT.
                - Missing skills that can be abstractly included or implied without misrepresenting experience
                - Information that may not be relevant to the position and how to rephrase it
                - Critical inconsistencies in experience, seniority, or language skills and how to address them.

            6. Review the entire updated resume section by section:
                - Make sure each section is optimized for the specific job opening.
                - Make sure no false information has been added to the resume
                - Make sure the resume is attractive to HR for that particular job opening.

            After completing your analysis and updates, provide the personalized resume in a valid JSON format with the following structure:
            <<<ResumeUpdate>>>

            Make sure all fields are included in the JSON, even if they are empty or unchanged from the original resume. The 'experience' array should contain the same number of objects as in the original resume.

            Your task is to directly, without any intermediate steps or explanations, create the final, customized resume in the specified JSON format. Focus on taking into account the detailed recommendations from the GAP analysis to create a high-quality, personalized resume that effectively highlights the candidate's qualifications for a specific job opening.
            """
