# handlers/messages/rewrite_resume_handler.py
from typing import Any, Dict, Optional
import json
import os
from datetime import datetime
from pathlib import Path
from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from core.states import UserState
from core.logger import setup_logger
from models.gap_analysis import GapAnalysisResult
from models.resume import ResumeUpdate
from services.entity_extractor import EntityExtractor
from services.hh_api import HeadHunterAPI
from services.llm_service import LLMService
from services.resume_updater import ResumeUpdaterService 
from core.text import (
    ERROR_MSG,
    INVALID_RESUME_LINK,
    RESUME_FOUND,
    RESUME_PARSED,
    INVALID_VACANCY_LINK,
    VACANCY_FOUND,
    VACANCY_PARSED,
    
)

logger = setup_logger(__name__)

class RewriteResumeHandler:
    """Обработчик состояния изменения резюме"""
    
    def __init__(self, bot: Bot, hh_api: HeadHunterAPI, llm_service: LLMService):
        """
        Инициализация обработчика.
        
        Args:
            bot: Экземпляр бота
            hh_api: Клиент API HeadHunter
            llm_service: Сервис для работы с языковой моделью
        """
        self.bot = bot
        self.hh_api = hh_api
        self.entity_extractor = EntityExtractor()
        self.llm_service = llm_service  # Добавляем сервис LLM
        self.resume_updater = ResumeUpdaterService(hh_api)  # Добавляем сервис обновления резюме
    
    async def handle_message(self, message: Message, state: FSMContext) -> Any:
        """Обработка сообщений в состоянии rewrite_resume"""
        
        logger.info(f"Получено сообщение в состоянии rewrite_resume от пользователя {message.from_user.id}: {message.text}")
        
        try:
            # Получаем текущие данные состояния
            data = await state.get_data()
            resume_processed = data.get("resume_processed", False)
            
            if not resume_processed:
                # Сначала ждём ссылку на резюме
                await self._process_resume(message, state)
            else:
                # Резюме уже обработано, ждём ссылку на вакансию
                await self._process_vacancy(message, state)
                
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            await message.answer(ERROR_MSG)
    
    async def _process_resume(self, message: Message, state: FSMContext) -> None:
        """Обработка ссылки на резюме"""
        if "hh.ru/resume/" not in message.text:
            await message.answer(INVALID_RESUME_LINK)
            return
            
        resume_id = message.text.split('/')[-1].split('?')[0]
        
        try:
            # Получаем данные резюме через API
            resume_data = await self.hh_api.make_api_request(f'/resumes/{resume_id}')
            await message.answer(RESUME_FOUND)
            
            # Парсим резюме
            parsed_resume = self.entity_extractor.extract_resume_info(resume_data)
            if not parsed_resume:
                raise ValueError("Не удалось обработать резюме")
                
            # Сохраняем данные в состояние
            await state.update_data(
            resume_id=resume_id,
            original_resume=resume_data,
            parsed_resume=parsed_resume.model_dump(exclude_none=True),
            resume_processed=True
        )
            
            await message.answer(RESUME_PARSED)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке резюме: {e}")
            await message.answer(ERROR_MSG)
    
    async def _process_vacancy(self, message: Message, state: FSMContext) -> None:
        """Обработка ссылки на вакансию"""
        if "hh.ru/vacancy/" not in message.text:
            await message.answer(INVALID_VACANCY_LINK)
            return
            
        vacancy_id = message.text.split('/')[-1].split('?')[0]
        
        try:
            # Получаем данные вакансии через API
            vacancy_data = await self.hh_api.make_api_request(f'/vacancies/{vacancy_id}')
            await message.answer(VACANCY_FOUND)
            
            # Парсим вакансию
            parsed_vacancy = self.entity_extractor.extract_vacancy_info(vacancy_data)
            if not parsed_vacancy:
                raise ValueError("Не удалось обработать вакансию")
                
            # Сохраняем данные в состояние
            await state.update_data(
                vacancy_id=vacancy_id,
                original_vacancy=vacancy_data,
                parsed_vacancy=parsed_vacancy.model_dump(exclude_none=True)
        )
            
            await message.answer(VACANCY_PARSED)
            
            # После успешной обработки вакансии вызываем финальный рерайт
            await self._finalize_processing(message, state)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке вакансии: {e}")
            await message.answer(ERROR_MSG)
            
            
    async def _finalize_processing(self, message: Message, state: FSMContext) -> None:
        """
        Завершает обработку резюме и вакансии.
        1) Запуск GAP-анализа
        2) Отправка результатов GAP-анализа (если нужно)
        3) Финальный рерайт резюме
        4) Обновление резюме через API
        5) Возврат пользователя в состояние authorized
        """
        try:
            # Получаем данные из состояния
            data = await state.get_data()
            parsed_resume = data.get('parsed_resume')
            parsed_vacancy = data.get('parsed_vacancy')
            original_resume = data.get('original_resume')
            resume_id = data.get('resume_id')
            
            if not parsed_resume or not parsed_vacancy:
                await message.answer("Внутренняя ошибка: отсутствуют данные резюме или вакансии.")
                return
            
            # 1. Запускаем GAP-анализ
            gap_result = self.llm_service.gap_analysis(parsed_resume, parsed_vacancy)
            if not gap_result:
                logger.error("GAP-анализ вернул None.")
                await message.answer("Произошла ошибка при GAP-анализе. Попробуйте позже.")
                return

            # 2. Финальный рерайт (учитывает результаты GAP-анализа)
            final_resume = self.llm_service.final_resume_rewrite(parsed_resume, gap_result)
            if not final_resume:
                await message.answer("Произошла ошибка при финальном рерайте. Попробуйте позже.")
                return
            
            # 3. Логируем всё в отдельную папку
            self._save_process_logs(
                resume_id=resume_id,
                original_resume=original_resume,
                parsed_resume=parsed_resume,
                parsed_vacancy=parsed_vacancy,
                gap_result=gap_result,
                final_resume=final_resume
            )
            

            # Обновляем резюме через API (например, patch-запросом)
            updated_resume = await self.resume_updater.update_resume(
                resume_id=resume_id,
                existing_resume=original_resume,
                rewritten_resume=final_resume
            )

            if not updated_resume:
                await message.answer("Произошла ошибка при обновлении резюме на сайте.")
                return

            # Формируем ссылку на обновлённое резюме и выводим её пользователю
            resume_url = f"https://hh.ru/resume/{resume_id}"
            success_message = (
                "✅ Резюме успешно обновлено!\n\n"
                "Посмотреть обновлённое резюме можно по ссылке:\n"
                f"{resume_url}"
            )

            await message.answer(success_message)

            # Возвращаемся в состояние authorized
            await state.set_state(UserState.authorized)

        except Exception as e:
            logger.error(f"Ошибка при финализации обработки: {e}")
            await message.answer(
                "Произошла ошибка при обновлении резюме. Пожалуйста, попробуйте позже."
            )
            
    def _save_process_logs(
        self,
        resume_id: str,
        original_resume: dict,
        parsed_resume: dict,
        parsed_vacancy: dict,
        gap_result: GapAnalysisResult, 
        final_resume: ResumeUpdate
    ) -> None:
        """
        Сохраняет все промежуточные и финальные данные в отдельную папку:
         - LOG/<yyyy-mm-dd_HH-MM-SS>_<resume_id>/
             original_resume.json
             parsed_resume.json
             original_vacancy.json
             parsed_vacancy.json
             gap_analysis.json
             final_resume.json
        """
        try:
            # 1) Определяем директорию для логов
            log_root = Path("LOG")
            log_root.mkdir(exist_ok=True)
            
            # 2) Формируем название подпапки с датой/временем и resume_id (или UUID)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            folder_name = f"{timestamp}_{resume_id}"
            folder_path = log_root / folder_name
            folder_path.mkdir(exist_ok=True)
            
            # 3) Сохраняем каждый объект в отдельный JSON-файл
            self._write_json(folder_path / "original_resume.json", original_resume)
            self._write_json(folder_path / "parsed_resume.json", parsed_resume)
            
            # Если есть "original_vacancy" (сырые данные вакансии),
            # можете так же сохранить:
            # self._write_json(folder_path / "original_vacancy.json", original_vacancy)

            # parsed_vacancy — это уже разбор вакансии
            self._write_json(folder_path / "parsed_vacancy.json", parsed_vacancy)
            
            # gap_result — pydantic-модель, преобразуем в dict
            gap_dict = gap_result.model_dump(exclude_none=True)
            self._write_json(folder_path / "gap_analysis.json", gap_dict)
            
            # финальное резюме тоже pydantic-модель
            final_resume_dict = final_resume.model_dump(exclude_none=True)
            self._write_json(folder_path / "final_resume.json", final_resume_dict)

            logger.info(
                f"Данные рерайта (ID {resume_id}) сохранены в папку: {folder_path}"
            )

        except Exception as log_exc:
            logger.error(f"Ошибка при сохранении логов в папку: {log_exc}")

    def _write_json(self, file_path: Path, data: dict) -> None:
        """Утилита для записи словаря в JSON-файл с отступами."""
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)