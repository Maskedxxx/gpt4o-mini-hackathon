# tests/llm_agent_gap.py
import logging
from pydantic import ValidationError
from typing import Optional
from openai import OpenAI
from config.config import Config
from models.resume import ResumeInfo
from models.gap_analysis import GapAnalysisResult, ResumeGapAnalysis  # <-- импортируем нашу модель для GAP-анализа
from core.logger import setup_logger

logger = setup_logger(__name__)

class LLMService:
    """
    Сервис для взаимодействия с языковой моделью.
    """

    def __init__(self, config: Config):
        """
        Инициализация сервиса LLM.
        
        Args:
            config: Конфигурация приложения с API ключом
        """
        self.client = OpenAI(api_key=config.openai.api_key)
        self.model = config.openai.model_name

    def _create_gap_analysis_prompt(self, parsed_resume: dict, parsed_vacancy: dict) -> str:
        """
        Создаёт промпт для шага GAP-анализа.
        
        Задача: сравнить ключевые навыки/требования вакансии 
        с данными резюме и выделить четыре категории:
        
        - matched_skills: навыки/требования, которые есть и в резюме, и в вакансии
        - missing_skills: навыки, которые требуются вакансией, но не упомянуты в резюме
        - irrelevant_blocks: части (блоки) в резюме, не актуальные для данной вакансии
        - critical_mismatches: критические несоответствия (например, уровень языка ниже требуемого и т.д.)
        """
        # Можно передавать всё резюме и вакансию, но для краткости часто самое важное:
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
    
    def gap_analysis(self, parsed_resume: dict, parsed_vacancy: dict) -> Optional[ResumeGapAnalysis]:
        """
        Выполняет GAP-анализ между резюме и вакансией, возвращая результат в формате pydantic-модели.
        
        Returns:
            GapAnalysisResult или None, если не смогли распарсить
        """
        try:
            prompt = self._create_gap_analysis_prompt(parsed_resume, parsed_vacancy)

            # Вызов ChatCompletion с указанием, что мы ожидаем строго JSON
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                temperature = 0.2,
                presence_penalty = 0.9,
                frequency_penalty = 0.5,
                logprobs = True,
                top_logprobs= 2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Ты — эксперт, который анализирует соответствие резюме к целевой вакансии. "
                            "Возвращай только валидный JSON по заданной структуре gap_анализа."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                # Здесь указываем модель-валидатор, чтобы parse сразу пытался привести к GapAnalysisResult
                response_format=ResumeGapAnalysis
            )

            response_text = completion.choices[0].message.content
            logger.debug(f"Ответ от OpenAI (GAP-анализ): {response_text}")

            if not response_text:
                logger.error("Получен пустой ответ от модели при GAP-анализе.")
                return None

            try:
                gap_result = ResumeGapAnalysis.model_validate_json(response_text)
                logger.info("GAP-анализ успешно выполнен.")
                return gap_result
            except ValidationError as e:
                logger.error(f"Ошибка валидации при GAP-анализе: {e}")
                return None

        except Exception as e:
            logger.error(f"Ошибка при обращении к OpenAI API для GAP-анализа: {e}")
            return None
