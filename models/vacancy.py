from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class Employment(BaseModel):
    """Модель типа занятости"""
    id: str = Field(..., description="Идентификатор типа занятости")

class ExperienceVac(BaseModel):
    """Модель требуемого опыта"""
    id: str = Field(..., description="Идентификатор требуемого опыта")

class Schedule(BaseModel):
    """Модель графика работы"""
    id: str = Field(..., description="Идентификатор графика работы")

class EmploymentForm(BaseModel):
    """Модель формы занятости"""
    id: str = Field(..., description="Идентификатор формы занятости")

class VacancyInfo(BaseModel):
    """
    Модель данных вакансии.
    
    Attributes:
        description: Описание вакансии в html
        key_skills: Список ключевых навыков
        employment_form: Форма занятости
        experience: Требуемый опыт работы
        schedule: График работы
        employment: Тип занятости
    """
    description: str = Field(..., description="Описание вакансии в html")
    key_skills: List[str] = Field(..., description="Список ключевых навыков")
    employment_form: Optional[EmploymentForm] = Field(None, description="Форма занятости")
    experience: Optional[ExperienceVac] = Field(None, description="Требуемый опыт работы")
    schedule: Optional[Schedule] = Field(None, description="График работы")
    employment: Optional[Employment] = Field(None, description="Тип занятости")