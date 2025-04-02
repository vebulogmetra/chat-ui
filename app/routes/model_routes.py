from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any

from app.database.db import get_db
from app.models.models import ChatModel, ModelSettings, PromptTemplate
from app.services.ollama_service import OllamaService

router = APIRouter(prefix="/models", tags=["models"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def models_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Страница списка моделей"""
    models = await ChatModel.get_all(db)
    return templates.TemplateResponse(
        "models.html", {"request": request, "models": models}
    )

@router.get("/list")
async def list_models(db: AsyncSession = Depends(get_db)):
    """Получить список всех моделей"""
    db_models = await ChatModel.get_all(db)
    return db_models

@router.get("/refresh")
async def refresh_models(db: AsyncSession = Depends(get_db)):
    """Обновить список моделей из Ollama"""
    try:
        # Получить модели из Ollama
        ollama_models = await OllamaService.list_models()
        
        result = []
        for model_data in ollama_models:
            model_name = model_data.get("name")
            model = await ChatModel.get_by_name(db, model_name)
            
            if not model:
                # Создаем новую модель
                model = await ChatModel.create(
                    db,
                    name=model_name,
                    display_name=model_name,
                    description=f"Модель {model_name}"
                )
                
                # Создаем дефолтные настройки для модели
                await ModelSettings.create(
                    db,
                    model_name=model_name,
                    temperature=0.7,
                    max_tokens=1024,
                    is_default=True
                )
            
            result.append({
                "id": model.id, 
                "name": model.name,
                "display_name": model.display_name
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения моделей: {str(e)}")

@router.get("/{model_name}/settings")
async def get_model_settings(model_name: str, db: AsyncSession = Depends(get_db)):
    """Получить настройки модели"""
    model = await ChatModel.get_by_name(db, model_name)
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    settings = await ModelSettings.get_default_for_model(db, model_name)
    if not settings:
        settings = await ModelSettings.create(db, model_name, is_default=True)
    
    return {
        "id": settings.id,
        "model_name": settings.model_name,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "system_prompt": settings.system_prompt,
        "settings": settings.settings
    }

@router.post("/{model_name}/settings")
async def update_model_settings(
    model_name: str,
    temperature: float = Form(0.7),
    max_tokens: int = Form(1024),
    system_prompt: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Обновить настройки модели"""
    model = await ChatModel.get_by_name(db, model_name)
    if not model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    
    settings = await ModelSettings.get_default_for_model(db, model_name)
    if not settings:
        settings = await ModelSettings.create(
            db, 
            model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            is_default=True
        )
    else:
        settings.temperature = temperature
        settings.max_tokens = max_tokens
        settings.system_prompt = system_prompt
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return {
        "id": settings.id,
        "model_name": settings.model_name,
        "temperature": settings.temperature,
        "max_tokens": settings.max_tokens,
        "system_prompt": settings.system_prompt,
        "settings": settings.settings
    }

@router.get("/prompts", response_class=HTMLResponse)
async def prompt_templates_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Страница шаблонов промптов"""
    prompts = await PromptTemplate.get_all(db)
    return templates.TemplateResponse(
        "prompts.html", {"request": request, "prompts": prompts}
    )

@router.get("/prompts/list")
async def list_prompts(db: AsyncSession = Depends(get_db)):
    """Получить список всех шаблонов промптов"""
    prompts = await PromptTemplate.get_all(db)
    return prompts

@router.post("/prompts/create")
async def create_prompt(
    name: str = Form(...),
    system_prompt: str = Form(...),
    description: Optional[str] = Form(None),
    user_prompt: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Создать новый шаблон промпта"""
    prompt = await PromptTemplate.create(
        db,
        name=name,
        system_prompt=system_prompt,
        description=description,
        user_prompt=user_prompt
    )
    
    return {
        "id": prompt.id,
        "name": prompt.name,
        "description": prompt.description,
        "system_prompt": prompt.system_prompt,
        "user_prompt": prompt.user_prompt
    } 