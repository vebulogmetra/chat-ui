import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import PromptTemplate

logger = logging.getLogger(__name__)

class TemplateService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all_templates(self) -> List[Dict[str, Any]]:
        """Получить все шаблоны промптов"""
        templates = await PromptTemplate.get_all(self.db)
        return [
            {
                "id": template.id,
                "name": template.name,
                "system_prompt": template.system_prompt,
                "description": template.description,
                "user_prompt": template.user_prompt,
                "created_at": template.created_at
            }
            for template in templates
        ]
    
    async def get_template_by_id(self, template_id: int) -> Optional[Dict[str, Any]]:
        """Получить шаблон промпта по ID"""
        template = await PromptTemplate.get_by_id(self.db, template_id)
        if not template:
            return None
        
        return {
            "id": template.id,
            "name": template.name,
            "system_prompt": template.system_prompt,
            "description": template.description,
            "user_prompt": template.user_prompt,
            "created_at": template.created_at
        }
    
    async def create_template(
        self, 
        name: str, 
        system_prompt: str, 
        description: str, 
        user_prompt: str
    ) -> Dict[str, Any]:
        """Создать новый шаблон промпта"""
        template = await PromptTemplate.create(
            self.db,
            name=name,
            system_prompt=system_prompt,
            description=description,
            user_prompt=user_prompt
        )
        
        return {
            "id": template.id,
            "name": template.name,
            "system_prompt": template.system_prompt,
            "description": template.description,
            "user_prompt": template.user_prompt,
            "created_at": template.created_at
        }
    
    async def update_template(
        self, 
        template_id: int, 
        name: str, 
        system_prompt: str, 
        description: str, 
        user_prompt: str
    ) -> Optional[Dict[str, Any]]:
        """Обновить шаблон промпта"""
        # Проверяем существование шаблона
        template = await PromptTemplate.get_by_id(self.db, template_id)
        if not template:
            return None
        
        # Обновляем шаблон
        await PromptTemplate.update(
            self.db,
            template_id,
            name=name,
            system_prompt=system_prompt,
            description=description,
            user_prompt=user_prompt
        )
        
        # Получаем обновленный шаблон
        updated_template = await PromptTemplate.get_by_id(self.db, template_id)
        
        return {
            "id": updated_template.id,
            "name": updated_template.name,
            "system_prompt": updated_template.system_prompt,
            "description": updated_template.description,
            "user_prompt": updated_template.user_prompt,
            "created_at": updated_template.created_at
        }
    
    async def delete_template(self, template_id: int) -> bool:
        """Удалить шаблон промпта"""
        return await PromptTemplate.delete(self.db, template_id) 