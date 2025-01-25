# models/resume.py
from typing import List
from pydantic import BaseModel, Field

class ResumeInfo(BaseModel):
    """
    Модель данных резюме.
    
    Attributes:
        title: Желаемая должность
        skills: Дополнительная информация, описание навыков в свободной форме
        skill_set: Ключевые навыки (список уникальных строк)
        descriptions: Список описаний опыта работы, Обязанности, функции, достижения
    """
    title: str = Field(..., description="Желаемая должность")
    skills: str = Field(..., description="Дополнительная информация, описание навыков в свободной форме")
    skill_set: List[str] = Field(..., description="Ключевые навыки (список уникальных строк)")
    descriptions: List[str] = Field(..., description="Список описаний опыта работы, Обязанности, функции, достижения")

class VacancyInfo(BaseModel):
    """
    Модель данных вакансии.
    
    Attributes:
        description: Описание вакансии
        key_skills: Список ключевых навыков
    """
    description: str = Field(..., description="Описание вакансии в html")
    key_skills: List[str] = Field(..., description="Список ключевых навыков")