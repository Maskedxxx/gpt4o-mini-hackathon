# services/entity_extractor.py
import re
import logging
from typing import Dict, Any, Optional
# from models.resume_vacancy import ResumeInfo, VacancyInfo
# from models.resume_vacancy import VacancyInfo
from models.vacancy import Employment, ExperienceVac, Schedule, EmploymentForm, VacancyInfo
from models.resume import ResumeInfo as ResumeInfoOld, Experience, Language, Level, Relocation, RelocationType, Salary, ProfessionalRole
from core.logger import setup_logger

logger = setup_logger(__name__)

class EntityExtractor:
    """Класс для извлечения информации из данных резюме и вакансий"""
    
    def __init__(self):
        self._clean_tag_pattern = re.compile(r"<.*?>")
    
    def _remove_html_tags(self, text: Optional[str]) -> str:
        """Удаляет HTML-теги из текста"""
        if not text:
            return ""
        return re.sub(self._clean_tag_pattern, "", text).strip()
    
    def extract_resume_info(self, data: Dict[str, Any]) -> Optional[ResumeInfoOld]:
        """
        Извлекает информацию из резюме.
        
        Args:
            data: Словарь с данными резюме
            
        Returns:
            Optional[ResumeInfo]: Объект с данными резюме или None в случае ошибки
        """
        if not isinstance(data, dict):
            logger.error(f"Некорректный формат данных резюме: {type(data)}")
            return None
            
        try:
            # Обработка опыта работы
            experience = []
            for exp in data.get("experience", []):
                if isinstance(exp, dict):
                    experience.append(Experience(
                        description=self._remove_html_tags(exp.get("description", "")),
                        position=exp.get("position", ""),
                        start=exp.get("start"),  # Добавляем извлечение start
                        end=exp.get("end")       # Добавляем извлечение end
                    ))
            
            # Обработка языков
            languages = []
            for lang in data.get("language", []):
                if isinstance(lang, dict):
                    languages.append(Language(
                        name=lang.get("name", ""),
                        level=Level(name=lang.get("level", {}).get("name", ""))
                    ))
            
            # Обработка релокации
            relocation_data = data.get("relocation")
            relocation = None
            if isinstance(relocation_data, dict) and relocation_data.get("type"):
                relocation = Relocation(
                    type=RelocationType(
                        name=relocation_data.get("type", {}).get("name", "")
                    )
                )
            
            # Обработка зарплаты
            salary_data = data.get("salary")
            salary = None
            if isinstance(salary_data, dict) and salary_data.get("amount") is not None:
                salary = Salary(amount=salary_data.get("amount"))
                
            
            # Добавляем обработку профессиональных ролей
            professional_roles = []
            for role in data.get("professional_roles", []):
                if isinstance(role, dict):
                    professional_roles.append(ProfessionalRole(
                        name=role.get("name", "")
                    ))
                
            return ResumeInfoOld(
                title=data.get("title", ""),
                skills=data.get("skills", ""),
                skill_set=data.get("skill_set", []),
                experience=experience,
                employments=[emp.get("name", "") for emp in data.get("employments", [])],
                schedules=[sch.get("name", "") for sch in data.get("schedules", [])],
                languages=languages,
                relocation=relocation,
                salary=salary,
                professional_roles=professional_roles
            )
        except Exception as e:
            logger.error(f"Ошибка при разборе данных резюме: {e}")
            logger.exception("Полный traceback ошибки:")
            return None

    def extract_vacancy_info(self, data: Dict[str, Any]) -> Optional[VacancyInfo]:
        """
        Извлекает информацию из вакансии.
        
        Args:
            data: Словарь с данными вакансии
            
        Returns:
            Optional[VacancyInfo]: Объект с данными вакансии или None в случае ошибки
        """
        if not isinstance(data, dict):
            logger.error(f"Некорректный формат данных вакансии: {type(data)}")
            return None
            
        try:
            # Обработка формы занятости
            employment_form_data = data.get("employment_form")
            employment_form = (
                EmploymentForm(id=employment_form_data.get("id", ""))
                if isinstance(employment_form_data, dict) else None
            )
            
            # Обработка опыта работы
            experience_data = data.get("experience")
            experience = (
                ExperienceVac(id=experience_data.get("id", ""))
                if isinstance(experience_data, dict) else None
            )
            
            # Обработка графика работы
            schedule_data = data.get("schedule")
            schedule = (
                Schedule(id=schedule_data.get("id", ""))
                if isinstance(schedule_data, dict) else None
            )
            
            # Обработка типа занятости
            employment_data = data.get("employment")
            employment = (
                Employment(id=employment_data.get("id", ""))
                if isinstance(employment_data, dict) else None
            )
            
            return VacancyInfo(
                description=self._remove_html_tags(data.get("description", "")),
                key_skills=[
                    skill.get("name", "") 
                    for skill in data.get("key_skills", [])
                    if isinstance(skill, dict)
                ],
                employment_form=employment_form,
                experience=experience,
                schedule=schedule,
                employment=employment
            )
        except Exception as e:
            logger.error(f"Ошибка при разборе данных вакансии: {e}")
            logger.exception("Полный traceback ошибки:")
            return None