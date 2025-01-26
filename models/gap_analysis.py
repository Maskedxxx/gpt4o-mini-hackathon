from pydantic import BaseModel, Field
from typing import List

class GapAnalysisResult(BaseModel):
    recomendation_analyzing: str = Field(..., description="Рекомендации по улучшению резюме")

    
    class Config:
        extra = "forbid"        # <--- Добавляем
        
class Recommendation(BaseModel):
    section: str = Field(..., description = "Name of the section to which the recommendation applies (enum: 'title', 'skills', 'skill_set', 'experience', 'professional_roles')")
    recommendation_type: str = Field(..., description = "Type of recommendation (enum: 'add', 'update', 'remove')")
    details: str = Field(..., description = "Detailed and precise description of step-by-step necessary changes (updates) in the summary, according to the GAP-analysis instructions")
    
    class Config:
        extra = "forbid"        # <--- Добавляем

class ResumeGapAnalysis(BaseModel):
    recommendations: List[Recommendation] = Field(..., description = "Cписок рекомендаций по улучшению резюме (Колличевство обьектов если section --> 'Experience' равно их общему количевству представленных в резюме.)")
    
    class Config:
        extra = "forbid"        # <--- Добавляем