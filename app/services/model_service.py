import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ChatModel, ModelSettings, PromptTemplate
from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

class ModelService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ollama_service = OllamaService()
    
    async def get_all_models(self) -> List[Dict[str, Any]]:
        """Получить все модели чатов"""
        models = await ChatModel.get_all(self.db)
        return [
            {
                "id": model.id,
                "name": model.name,
                "display_name": model.display_name,
                "description": model.description
            }
            for model in models
        ]
    
    async def get_model_by_id(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Получить модель по ID"""
        model = await ChatModel.get_by_id(self.db, model_id)
        if not model:
            return None
        
        return {
            "id": model.id,
            "name": model.name,
            "display_name": model.display_name,
            "description": model.description
        }
    
    async def get_model_settings(self, model_id: int) -> Optional[Dict[str, Any]]:
        """Получить настройки модели по ID модели"""
        settings = await ModelSettings.get_by_model_id(self.db, model_id)
        if not settings:
            return None
        
        return {
            "id": settings.id,
            "model_id": settings.model_id,
            "temperature": settings.temperature,
            "top_p": settings.top_p,
            "top_k": settings.top_k,
            "max_tokens": settings.max_tokens,
            "system_prompt": settings.system_prompt
        }
    
    async def update_model_settings(
        self, 
        model_id: int, 
        settings_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Обновить настройки модели"""
        # Проверяем существование модели
        model = await ChatModel.get_by_id(self.db, model_id)
        if not model:
            return None
        
        # Получаем текущие настройки или создаем новые
        settings = await ModelSettings.get_by_model_id(self.db, model_id)
        
        if settings:
            # Обновляем существующие настройки
            await ModelSettings.update(
                self.db,
                settings.id,
                **settings_data
            )
            
            # Получаем обновленные настройки
            updated_settings = await ModelSettings.get_by_model_id(self.db, model_id)
        else:
            # Создаем новые настройки
            settings_data['model_id'] = model_id
            updated_settings = await ModelSettings.create(
                self.db,
                **settings_data
            )
        
        return {
            "id": updated_settings.id,
            "model_id": updated_settings.model_id,
            "temperature": updated_settings.temperature,
            "top_p": updated_settings.top_p,
            "top_k": updated_settings.top_k,
            "max_tokens": updated_settings.max_tokens,
            "system_prompt": updated_settings.system_prompt
        }
    
    async def refresh_models_from_api(self) -> List[Dict[str, Any]]:
        """Обновить список моделей из Ollama API"""
        # Получаем список моделей из API
        api_models = await self.ollama_service.list_models()
        
        # Обрабатываем полученные модели
        result = []
        
        for api_model in api_models:
            model_name = api_model.get("name")
            if not model_name:
                continue
            
            # Проверяем, существует ли модель в БД
            model = await ChatModel.get_by_name(self.db, model_name)
            
            # Получаем информацию о размере параметров
            details = api_model.get("details", {})
            parameter_size = details.get("parameter_size", "Неизвестно")
            
            # Если модель не существует, создаем ее
            if not model:
                model = await ChatModel.create(
                    self.db,
                    name=model_name,
                    display_name=model_name,
                    description=f"Модель {model_name} ({parameter_size})"
                )
                
                # Создаем настройки по умолчанию
                # Получаем шаблон "Личный ассистент Артём"
                artem_template = None
                templates = await PromptTemplate.get_all(self.db)
                for template in templates:
                    if template.name == "Личный ассистент Артём":
                        artem_template = template
                        break
                
                system_prompt = "Вы полезный помощник по имени Артём. Отвечайте на вопросы пользователя дружелюбно и информативно."
                if artem_template:
                    system_prompt = artem_template.system_prompt
                
                await ModelSettings.create(
                    self.db,
                    model_id=model.id,
                    temperature="0.7",
                    top_p="0.9",
                    top_k="40",
                    max_tokens="1024",
                    system_prompt=system_prompt
                )
            
            result.append({
                "id": model.id,
                "name": model.name,
                "display_name": model.display_name,
                "description": model.description
            })
        
        return result 