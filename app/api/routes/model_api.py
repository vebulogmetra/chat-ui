import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.model_schema import (
    ChatModelResponse, ChatModelWithSettings, 
    ModelSettingsCreate, ModelSettingsUpdate, ModelSettingsResponse
)
from app.services.model_service import ModelService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/model", tags=["model_api"])

@router.get("/models", response_model=List[ChatModelResponse])
async def list_models(db: AsyncSession = Depends(get_db)):
    """Получить список всех моделей"""
    model_service = ModelService(db)
    models = await model_service.get_all_models()
    return models

@router.get("/models/{model_id}", response_model=ChatModelResponse)
async def get_model(model_id: int, db: AsyncSession = Depends(get_db)):
    """Получить модель по ID"""
    model_service = ModelService(db)
    model = await model_service.get_model_by_id(model_id)
    if not model:
        raise HTTPException(status_code=404, detail=f"Модель с ID={model_id} не найдена")
    return model

@router.get("/models/{model_id}/settings", response_model=ModelSettingsResponse)
async def get_model_settings(model_id: int, db: AsyncSession = Depends(get_db)):
    """Получить настройки модели по ID модели"""
    model_service = ModelService(db)
    settings = await model_service.get_model_settings(model_id)
    if not settings:
        raise HTTPException(status_code=404, detail=f"Настройки для модели с ID={model_id} не найдены")
    return settings

@router.put("/models/{model_id}/settings", response_model=ModelSettingsResponse)
async def update_model_settings(
    model_id: int, 
    settings: ModelSettingsUpdate, 
    db: AsyncSession = Depends(get_db)
):
    """Обновить настройки модели"""
    try:
        model_service = ModelService(db)
        settings_dict = settings.dict(exclude_unset=True)
        updated_settings = await model_service.update_model_settings(model_id, settings_dict)
        if not updated_settings:
            raise HTTPException(status_code=404, detail=f"Модель с ID={model_id} не найдена")
        return updated_settings
    except Exception as e:
        logger.error(f"Ошибка при обновлении настроек модели: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении настроек модели: {str(e)}")

@router.post("/refresh", response_model=List[ChatModelResponse])
async def refresh_models(db: AsyncSession = Depends(get_db)):
    """Обновить список моделей из Ollama API"""
    try:
        model_service = ModelService(db)
        models = await model_service.refresh_models_from_api()
        return models
    except Exception as e:
        logger.error(f"Ошибка при обновлении списка моделей: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении списка моделей: {str(e)}") 