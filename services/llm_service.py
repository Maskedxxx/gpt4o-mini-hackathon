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
                temperature = 0.4,
                presence_penalty = 0.9,
                frequency_penalty = 0.5,
                logprobs = True,
                top_logprobs= 2,
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
                        "Ты — эксперт HR. Учитывайте GAP-анализ и требования вакансии выпереписываете резюме. "
                        "Выполните изменение резюме тех разделов что указаны в gap-анализе. "
                        "ЦЕЛЬ результата: переписанные секции резюме выполненные по рекомендациям из gap-анализа. "
                        "ALWAYS ANSWER IN RUSSIAN, IT'S IMPORTANT! "
                        "ALWAYS CONSIDER CHANGES IN ALL OBJECTS <experience>"
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
                temperature = 0.4,
                presence_penalty = 0.9,
                frequency_penalty = 0.5,
                logprobs = True,
                top_logprobs= 2,
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
        You are an AI assistant tasked with performing a comprehensive gap analysis between a resume and a job description. Your goal is to provide detailed recommendations on how to improve the resume to better match the job requirements.

        First, you will be given the parsed data from a resume:
        
        <resume>
        <title>{parsed_resume.get("title")}</title>
        <skills>{parsed_resume.get("skills")}</skills>
        <skill_set>{parsed_resume.get("skill_set")}</skill_set>
        <experience>{parsed_resume.get("experience")}</experience>
        <professional_roles>{parsed_resume.get("professional_roles")}</professional_roles>
        </resume>

        Next, you will be presented with the parsed data from the job description that the user wants to apply for:

        <job_description>
        <description>{parsed_vacancy.get("description")}</description>
        <key_skills>{parsed_vacancy.get("key_skills")}</key_skills>
        <employment_form>{parsed_vacancy.get("employment_form")}</employment_form>
        <experience>{parsed_vacancy.get("experience")}</experience>
        <schedule>{parsed_vacancy.get("schedule")}</schedule>
        <employment>{parsed_vacancy.get("employment")}</employment>
        <professional_roles>{parsed_vacancy.get("professional_roles")}</professional_roles>
        </job_description>

        
        Your task is to conduct a thorough gap analysis comparing the resume to the job description. You will then fill out a ResumeGapAnalysis schema based on your findings. Here's the structure of the schema <ResumeGapAnalysis>

        Follow the following guidelines when completing the schema:

        1. Analyze each section of the resume (job title, skills, skill set_skills, experience, professional_roles) and compare it to the corresponding information in the job description.

        2. In the skills section, list all the skills you believe are necessary for the resume to match the job description.

        3. For the Experience section, create as many Recommendations objects as there are experience entries on the resume. For example, if there are 4 experience entries on the resume, you should create 4 recommendation objects for the Experience section.

        IMPORTANT: Each experience entry in the resume must have its own separate recommendation object in the output. The number of 'experience' recommendations must exactly match the number of experience entries in the original resume. Each recommendation should specifically reference the position it's addressing and provide tailored improvements for that specific role.

        4. Make sure you address all the sections mentioned in the enumeration for the 'section' field: title, skills, skill_set, experience and professional_roles.

        5. When filling in the 'Details' field for each recommendation, give a clear step-by-step description of what needs to be done to improve that section of the resume. Use natural language and be as specific as possible. The steps should be easy to understand and follow. And the text itself you are addressing to the next agent who will perform the final revision of the text on your assignment, so state the text as an assignment for the next agent what he needs to do

        6. For each recommendation, select the appropriate “recommendation_type” (add, update, or delete) based on your analysis.

        Here is an example of what a completed ResumeGapAnalysis might look like:

        {{
        "recommendations": [
            {{
                "section": "title",
                "recommendation_type": "update",
                "details": "1. We need to revise the current job title 'Software Developer'. 2. We should change it to 'Senior Full Stack Developer' to better match the job description."
            }},
            {{
                "section": "skills",
                "recommendation_type": "add",
                "details": "1. We should revise the current list of skills. 2. Need to add the following skills that are mentioned in the job description but are missing from your resume: Docker, Kubernetes, CI/CD pipelines"
            }},
            {{
                "section": "experience[0]",
                "recommendation_type": "update",
                "details": "1. For position 'Senior Software Engineer': Add cloud technology details and AWS projects. 2. Quantify accomplishments with metrics."
            }},
            {{
                "section": "experience[1]",
                "recommendation_type": "update",
                "details": "1. For position 'Software Engineer': Highlight database optimization work. 2. Add specific examples of performance improvements."
            }},
            {{
                "section": "experience[2]",
                "recommendation_type": "update",
                "details": "1. For position 'Junior Developer': Emphasize team collaboration and technical growth. 2. Include specific technologies used."
            }},
            {{
                "section": "professional_roles",
                "recommendation_type": "add",
                "details": "1. We need to analyze current professional roles. 2. We should add 'DevOps Engineer' to the list of roles."
            }}
        ]
    }}

        After completing your analysis, output the filled ResumeGapAnalysis schema in JSON format. Ensure that your recommendations are detailed, specific, and provide clear step-by-step instructions for improving each section of the resume.
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
            professional_roles: {parsed_resume.get("professional_roles")}
            </original_resume>


        Your goal is to rewrite the resume according to the recommendations in the gap analysis while maintaining the overall structure and authenticity of the original resume. Follow these guidelines:

        1. Read through the original resume, gap analysis, and job description carefully.

        2. For each section of the resume mentioned in the gap analysis, rewrite the content to address the recommendations while preserving the essence of the original information.

        3. Pay special attention to the "experience" section. For each experience entry:
        a. Maintain the same number of entries !!objects!! as in the original resume PS: So if there are 6 objects, then you have to rewrite all 6 objects..
        b. Use the original information as a base, but REWRITE!! it according to the gap analysis recommendations.
        c. Integrate the recommendations seamlessly, as if they were part of the original experience.
        d. Add specific metrics, achievements, and technical details, NUMBERS!! that align with the job description.
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
