import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.template_schema import TemplateCreate, TemplateUpdate, TemplateResponse
from app.services.template_service import TemplateService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/template", tags=["template_api"])

@router.get("/templates", response_model=List[TemplateResponse])
async def list_templates(db: AsyncSession = Depends(get_db)):
    """Получить список всех шаблонов промптов"""
    template_service = TemplateService(db)
    templates = await template_service.get_all_templates()
    return templates

@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Получить шаблон промпта по ID"""
    template_service = TemplateService(db)
    template = await template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Шаблон с ID={template_id} не найден")
    return template

@router.post("/templates", response_model=TemplateResponse)
async def create_template(template: TemplateCreate, db: AsyncSession = Depends(get_db)):
    """Создать новый шаблон промпта"""
    try:
        template_service = TemplateService(db)
        created_template = await template_service.create_template(
            name=template.name,
            system_prompt=template.system_prompt,
            description=template.description,
            user_prompt=template.user_prompt
        )
        return created_template
    except Exception as e:
        logger.error(f"Ошибка при создании шаблона: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при создании шаблона: {str(e)}")

@router.put("/templates/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: int, 
    template: TemplateUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Обновить шаблон промпта"""
    try:
        template_service = TemplateService(db)
        template_data = template.dict(exclude_unset=True)
        
        # Получаем текущий шаблон для незаполненных полей
        current_template = await template_service.get_template_by_id(template_id)
        if not current_template:
            raise HTTPException(status_code=404, detail=f"Шаблон с ID={template_id} не найден")
        
        # Заполняем отсутствующие поля текущими значениями
        name = template_data.get('name', current_template['name'])
        system_prompt = template_data.get('system_prompt', current_template['system_prompt'])
        description = template_data.get('description', current_template['description'])
        user_prompt = template_data.get('user_prompt', current_template['user_prompt'])
        
        updated_template = await template_service.update_template(
            template_id=template_id,
            name=name,
            system_prompt=system_prompt,
            description=description,
            user_prompt=user_prompt
        )
        
        if not updated_template:
            raise HTTPException(status_code=404, detail=f"Шаблон с ID={template_id} не найден")
            
        return updated_template
    except Exception as e:
        logger.error(f"Ошибка при обновлении шаблона: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении шаблона: {str(e)}")

@router.delete("/templates/{template_id}")
async def delete_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить шаблон промпта"""
    template_service = TemplateService(db)
    success = await template_service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Шаблон с ID={template_id} не найден")
    return {"status": "success", "message": f"Шаблон {template_id} успешно удален"} 