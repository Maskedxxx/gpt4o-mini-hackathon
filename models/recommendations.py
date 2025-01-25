# models/recommendations.py

from pydantic import BaseModel
from typing import List

class RecommendationsResult(BaseModel):
    to_highlight: List[str]
    to_remove: List[str]
    to_rewrite: List[str]
    general_advice: List[str]

    class Config:
        extra = "forbid"        # <--- Добавляем