from pydantic import BaseModel
from typing import List

class GapAnalysisResult(BaseModel):
    matched_skills: List[str]
    missing_skills: List[str]
    irrelevant_blocks: List[str]
    critical_mismatches: List[str]
    
    class Config:
        extra = "forbid"        # <--- Добавляем