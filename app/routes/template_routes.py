import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Form
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import get_db
from app.models.models import PromptTemplate

# Настраиваем логгер
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/templates", tags=["templates"])

@router.get("/list")
async def list_templates(db: AsyncSession = Depends(get_db)):
    """Получить список всех шаблонов промптов"""
    try:
        templates = await PromptTemplate.get_all(db)
        logger.info(f"Получено {len(templates)} шаблонов промптов")
        return templates
    except Exception as e:
        logger.error(f"Ошибка при получении шаблонов промптов: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении шаблонов: {str(e)}")

@router.get("/{template_id}")
async def get_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Получить шаблон промпта по ID"""
    template = await PromptTemplate.get_by_id(db, template_id)
    if not template:
        logger.error(f"Шаблон с ID {template_id} не найден")
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "system_prompt": template.system_prompt,
        "user_prompt": template.user_prompt
    }

@router.post("/add")
async def add_template(
    name: str = Form(...),
    description: str = Form(None),
    system_prompt: str = Form(...),
    user_prompt: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Добавить новый шаблон промпта"""
    try:
        template = await PromptTemplate.create(
            db, name, system_prompt, description, user_prompt
        )
        logger.info(f"Создан новый шаблон промпта '{name}' с ID {template.id}")
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "system_prompt": template.system_prompt,
            "user_prompt": template.user_prompt
        }
    except Exception as e:
        logger.error(f"Ошибка при создании шаблона: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при создании шаблона: {str(e)}")

@router.delete("/{template_id}")
async def delete_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить шаблон промпта"""
    result = await PromptTemplate.delete(db, template_id)
    if not result:
        logger.error(f"Шаблон с ID {template_id} не найден при попытке удаления")
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    logger.info(f"Удален шаблон промпта с ID {template_id}")
    return {"status": "success", "message": "Шаблон удален"} 