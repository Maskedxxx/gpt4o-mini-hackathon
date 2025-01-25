from pydantic import BaseModel, Field
from typing import List

class GapAnalysisResult(BaseModel):
    recomendation_analyzing: str = Field(..., description="Рекомендации по улучшению резюме")

    
    class Config:
        extra = "forbid"        # <--- Добавляем
        
class Recommendation(BaseModel):
    section: str = Field(..., description = "Название секции, к которой относится рекомендация (enum: 'title', 'skills', 'skill_set', 'experience', 'professional_roles')") 
    recommendation_type: str = Field(..., description = "Тип рекомендации (enum: 'add', 'update', 'remove')")  
    details: str = Field(..., description = "Детальное описание необходимых изменений")
    
    class Config:
        extra = "forbid"        # <--- Добавляем

class ResumeGapAnalysis(BaseModel):
    recommendations: List[Recommendation] = Field(..., description = "Cписок рекомендаций по улучшению резюме")
    
    class Config:
        extra = "forbid"        # <--- Добавляем