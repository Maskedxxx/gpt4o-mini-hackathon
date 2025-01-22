from typing import List, Optional
from pydantic import BaseModel, Field

class Level(BaseModel):
    """Модель уровня владения языком"""
    name: str = Field(..., description="Название уровня владения языком")

    class Config:
        extra = "forbid"        # <--- Добавляем

class Language(BaseModel):
    """Модель языка и уровня владения им"""
    name: str = Field(..., description="Название языка")
    level: Level = Field(..., description="Уровень владения языком")

    class Config:
        extra = "forbid"        # <--- Добавляем

class RelocationType(BaseModel):
    """Модель типа релокации"""
    name: str = Field(..., description="Название типа релокации")

    class Config:
        extra = "forbid"        # <--- Добавляем

class Relocation(BaseModel):
    """Модель информации о релокации"""
    type: RelocationType = Field(..., description="Тип релокации")

    class Config:
        extra = "forbid"        # <--- Добавляем

class Salary(BaseModel):
    """Модель зарплатных ожиданий"""
    amount: int = Field(..., description="Сумма зарплатных ожиданий")

    class Config:
        extra = "forbid"        # <--- Добавляем

class Experience(BaseModel):
    """Модель опыта работы"""
    description: str = Field(..., description="Описание опыта работы")
    position: str = Field(..., description="Должность")

    class Config:
        extra = "forbid"        # <--- Добавляем
        
class ProfessionalRole(BaseModel):
    """Модель профессиональной роли"""
    name: str = Field(..., description="Название профессиональной роли")

    class Config:
        extra = "forbid"

class ResumeInfo(BaseModel):
    """
    Модель данных резюме.
    
    Attributes:
        title: Желаемая должность
        skills: Дополнительная информация, описание навыков
        skill_set: Ключевые навыки (список уникальных строк)
        experience: Список опыта работы
        employments: Список предпочитаемых типов занятости
        schedules: Список предпочитаемых графиков работы
        languages: Список языков и уровней владения
        relocation: Информация о релокации
        salary: Зарплатные ожидания
        professional_roles: Список профессиональных ролей
    """
    title: str = Field(..., description="Желаемая должность")
    skills: str = Field(..., description="Дополнительная информация, описание навыков в свободной подробной форме")
    skill_set: List[str] = Field(..., description="Ключевые навыки (список уникальных строк)")
    experience: List[Experience] = Field(..., description="Список опыта работы")
    employments: List[str] = Field(..., description="Список предпочитаемых типов занятости")
    schedules: List[str] = Field(..., description="Список предпочитаемых графиков работы")
    languages: List[Language] = Field(..., description="Список языков и уровней владения")
    relocation: Optional[Relocation] = Field(None, description="Информация о релокации")
    salary: Optional[Salary] = Field(None, description="Зарплатные ожидания")
    professional_roles: List[ProfessionalRole] = Field(..., description="Список профессиональных ролей")

    class Config:
        extra = "forbid"        # <--- Добавляем
        title = "ResumeInfo"    # (можно явно указать заголовок для схемы)
