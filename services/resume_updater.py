# services/resume_updater.py
from typing import Dict, Any, Optional
import requests
from core.logger import setup_logger
from services.hh_api import HeadHunterAPI
from models.resume_vacancy import ResumeInfo

logger = setup_logger(__name__)

class ResumeUpdaterService:
    """
    Сервис для обновления резюме на HeadHunter.
    
    Обеспечивает обновление существующего резюме на основе
    переписанных данных от LLM.
    """
    
    def __init__(self, hh_api: HeadHunterAPI):
        """
        Инициализация сервиса обновления резюме.
        
        Args:
            hh_api: Экземпляр API клиента HeadHunter
        """
        self.hh_api = hh_api
    
    def _update_resume_fields(
        self,
        existing_resume: Dict[str, Any],
        rewritten_resume: ResumeInfo
    ) -> Dict[str, Any]:
        """
        Обновляет поля существующего резюме данными из переписанного.
        
        Args:
            existing_resume: Оригинальное резюме
            rewritten_resume: Переписанное резюме
            
        Returns:
            Dict[str, Any]: Обновленное резюме
        """
        # Конвертируем Pydantic модель в словарь
        rewritten_data = rewritten_resume.model_dump()
        
        # Обновляем основные поля
        if rewritten_data.get("title"):
            existing_resume["title"] = rewritten_data["title"]
            
        if rewritten_data.get("skills"):
            existing_resume["skills"] = rewritten_data["skills"]
            
        if rewritten_data.get("skill_set"):
            existing_resume["skill_set"] = rewritten_data["skill_set"]
        
        # Обновляем опыт работы
        if rewritten_data.get("experience"):
            logger.info(f"Обновление опыта работы. Найдено {len(rewritten_data['experience'])} записей")
            
            # Проверяем совпадение количества записей
            if len(rewritten_data["experience"]) != len(existing_resume["experience"]):
                logger.warning(
                    f"Количество записей опыта не совпадает: "
                    f"rewritten={len(rewritten_data['experience'])}, "
                    f"existing={len(existing_resume['experience'])}"
                )
                
            # Обновляем только position и description для каждой записи
            for i, new_exp in enumerate(rewritten_data["experience"]):
                if i < len(existing_resume["experience"]):
                    existing_resume["experience"][i]["position"] = new_exp["position"]
                    existing_resume["experience"][i]["description"] = new_exp["description"]
                    logger.debug(
                        f"Обновлена запись {i}: "
                        f"position={new_exp['position']}, "
                        f"description={new_exp['description'][:50]}..."
                    )
        
        # Обработка специальных полей
        if "specialization" in existing_resume:
            existing_resume.pop("specialization")
            
        if "has_vehicle" in existing_resume:
            existing_resume["has_vehicle"] = (
                existing_resume["has_vehicle"] 
                if existing_resume["has_vehicle"] is True 
                else False
            )
        
        return existing_resume
    
    async def update_resume(
        self,
        resume_id: str,
        existing_resume: Dict[str, Any],
        rewritten_resume: ResumeInfo
    ) -> Optional[Dict[str, Any]]:
        """
        Обновляет резюме на HeadHunter.
        
        Args:
            resume_id: Идентификатор резюме
            existing_resume: Оригинальное резюме
            rewritten_resume: Переписанное резюме
            
        Returns:
            Optional[Dict[str, Any]]: Обновленное резюме или None в случае ошибки
        """
        try:
            # Обновляем поля резюме
            updated_resume = self._update_resume_fields(existing_resume, rewritten_resume)
            
            # Отправляем обновленное резюме через API
            response = await self.hh_api.make_api_request(
                endpoint=f'/resumes/{resume_id}',
                method='PUT',
                data=updated_resume
            )
            
            logger.info(f"Резюме {resume_id} успешно обновлено")
            return updated_resume
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении резюме: {e}")
            return None