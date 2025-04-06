from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import logging

from app.database.db import get_db
from app.models.models import ChatModel, ModelSettings, PromptTemplate
from app.services.ollama_service import OllamaService
from app.schemas.model_schema import ChatModelResponse

# Настраиваем логгер
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["models"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def get_models_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Страница списка моделей"""
    models = await ChatModel.get_all(db)
    return templates.TemplateResponse(
        "models.html", {"request": request, "models": models}
    )

@router.get("/list")
async def list_models(db: AsyncSession = Depends(get_db)):
    """Получить список всех моделей"""
    try:
        logger.info("Запрос на получение списка моделей")
        models = await ChatModel.get_all(db)
        
        # Если моделей нет в БД, обновляем их из Ollama API и делаем повторную попытку
        if not models:
            logger.info("В базе данных нет моделей. Автоматическое обновление из Ollama API.")
            await refresh_models(db)  # Обновляем список моделей
            
            # Повторно запрашиваем модели из БД
            models = await ChatModel.get_all(db)
            
            # Если и после обновления моделей нет, возвращаем пустой список
            if not models:
                logger.warning("После обновления модели всё еще не найдены в БД.")
                return []
        
        logger.info(f"Получено {len(models)} моделей")
        
        result = [
            {
                "id": model.id,
                "name": model.name,
                "display_name": model.display_name or model.name,
                "description": model.description
            } 
            for model in models
        ]
        
        logger.info(f"Возвращаемый результат: {result}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении списка моделей: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении списка моделей: {str(e)}")

@router.get("/refresh", response_model=List[ChatModelResponse])
async def refresh_models(db: AsyncSession = Depends(get_db)):
    """
    Обновить список моделей из Ollama API и вернуть обновленный список
    """
    try:
        logger.info("Начало обновления списка моделей")
        
        # Создаем экземпляр сервиса Ollama для получения списка моделей
        ollama_service = OllamaService()
        
        # Получаем список моделей из API Ollama
        api_models = await ollama_service.list_models()
        logger.info(f"Получено {len(api_models)} моделей из API Ollama")
        
        if not api_models:
            logger.warning("Не получены модели от Ollama API. Проверьте соединение с сервером Ollama.")
            return await ChatModel.get_all(db)
        
        # Перебираем модели из API и создаем/обновляем их в базе данных
        for api_model in api_models:
            model_name = api_model.get("name")
            if not model_name:
                logger.warning(f"Пропуск модели без имени: {api_model}")
                continue
                
            logger.info(f"Обработка модели '{model_name}'")
            
            model = await ChatModel.get_by_name(db, model_name)
            
            # Получаем дополнительную информацию о модели
            details = api_model.get("details", {})
            parameter_size = details.get("parameter_size", "Неизвестно")
            
            # Если модель не существует в базе, создаем новую
            if not model:
                logger.info(f"Создание новой модели '{model_name}' в базе данных")
                model = ChatModel(
                    name=model_name,
                    display_name=model_name,
                    description=f"Модель {model_name} ({parameter_size})",
                )
                await model.save(db)
                
                # Создаем настройки по умолчанию для новой модели
                default_system_prompt = "Вы полезный помощник по имени Артём. Вы всегда вежливы и дружелюбны."
                
                await ModelSettings.create(
                    db,
                    model_id=model.id,
                    temperature="0.7",
                    top_p="0.9",
                    top_k="40",
                    max_tokens="1024",
                    system_prompt=default_system_prompt
                )
        
        # Получаем обновленный список моделей из базы данных
        models = await ChatModel.get_all(db)
        logger.info(f"Обновленный список моделей содержит {len(models)} записей")
        
        # Преобразуем модели в ответ API
        result = [
            {
                "id": model.id,
                "name": model.name,
                "display_name": model.display_name or model.name,
                "description": model.description or f"Модель {model.name}"
            } 
            for model in models
        ]
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при обновлении списка моделей: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении списка моделей: {str(e)}")

@router.get("/{model_id}/settings")
async def get_model_settings(model_id: str, db: AsyncSession = Depends(get_db)):
    """Получить настройки модели по ID или имени"""
    try:
        # Проверяем, является ли model_id числом или строкой
        try:
            model_id_int = int(model_id)
            model = await ChatModel.get_by_id(db, model_id_int)
        except ValueError:
            # Если не число, то это имя модели
            model = await ChatModel.get_by_name(db, model_id)
        
        if not model:
            logger.error(f"Модель '{model_id}' не найдена")
            raise HTTPException(status_code=404, detail="Модель не найдена")
        
        settings = await ModelSettings.get_by_model_id(db, model.id)
        if not settings:
            # Если нет настроек, создаем их с дефолтными значениями
            settings = await ModelSettings.create(db, model.id)
        
        return {
            "id": settings.id,
            "model_id": settings.model_id,
            "model_name": model.name,
            "temperature": settings.temperature,
            "top_p": settings.top_p,
            "top_k": settings.top_k,
            "max_tokens": settings.max_tokens,
            "system_prompt": settings.system_prompt
        }
    except Exception as e:
        logger.error(f"Ошибка при получении настроек модели: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении настроек модели: {str(e)}")

@router.post("/{model_id}/settings")
async def update_model_settings(
    model_id: str,
    temperature: str = Form(None),
    top_p: str = Form(None),
    top_k: str = Form(None),
    max_tokens: str = Form(None),
    system_prompt: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Обновить настройки модели"""
    try:
        # Проверяем, является ли model_id числом или строкой
        try:
            model_id_int = int(model_id)
            model = await ChatModel.get_by_id(db, model_id_int)
        except ValueError:
            # Если не число, то это имя модели
            model = await ChatModel.get_by_name(db, model_id)
        
        if not model:
            logger.error(f"Модель '{model_id}' не найдена")
            raise HTTPException(status_code=404, detail="Модель не найдена")
        
        settings = await ModelSettings.get_by_model_id(db, model.id)
        
        if not settings:
            # Если нет настроек, создаем их
            settings = await ModelSettings.create(
                db, model.id,
                temperature=temperature or "0.7",
                top_p=top_p or "0.9",
                top_k=top_k or "40",
                max_tokens=max_tokens or "1024",
                system_prompt=system_prompt or "Вы полезный помощник."
            )
        else:
            # Обновляем существующие настройки
            if temperature is not None:
                settings.temperature = temperature
            if top_p is not None:
                settings.top_p = top_p
            if top_k is not None:
                settings.top_k = top_k
            if max_tokens is not None:
                settings.max_tokens = max_tokens
            if system_prompt is not None:
                settings.system_prompt = system_prompt
                
            await db.commit()
            await db.refresh(settings)
        
        return {
            "id": settings.id,
            "model_id": settings.model_id,
            "temperature": settings.temperature,
            "top_p": settings.top_p,
            "top_k": settings.top_k,
            "max_tokens": settings.max_tokens,
            "system_prompt": settings.system_prompt
        }
    except Exception as e:
        logger.error(f"Ошибка при обновлении настроек модели: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении настроек модели: {str(e)}")

@router.get("/prompts/list")
async def list_prompt_templates(db: AsyncSession = Depends(get_db)):
    """Получить список всех шаблонов промптов"""
    templates = await PromptTemplate.get_all(db)
    return templates

@router.post("/prompts/add")
async def add_prompt_template(
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
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "system_prompt": template.system_prompt,
            "user_prompt": template.user_prompt
        }
    except Exception as e:
        logger.error(f"Ошибка при добавлении шаблона: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении шаблона: {str(e)}")

@router.get("/prompts/{template_id}")
async def get_prompt_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Получить шаблон промпта по ID"""
    template = await PromptTemplate.get_by_id(db, template_id)
    if not template:
        logger.error(f"Шаблон промпта с ID {template_id} не найден")
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "system_prompt": template.system_prompt,
        "user_prompt": template.user_prompt
    }

@router.post("/prompts/{template_id}/update")
async def update_prompt_template(
    template_id: int,
    name: str = Form(...),
    description: str = Form(None),
    system_prompt: str = Form(...),
    user_prompt: str = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Обновить шаблон промпта"""
    template = await PromptTemplate.get_by_id(db, template_id)
    if not template:
        logger.error(f"Шаблон промпта с ID {template_id} не найден")
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    try:
        template.name = name
        template.description = description
        template.system_prompt = system_prompt
        template.user_prompt = user_prompt
        
        await template.save(db)
        
        return {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "system_prompt": template.system_prompt,
            "user_prompt": template.user_prompt
        }
    except Exception as e:
        logger.error(f"Ошибка при обновлении шаблона: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении шаблона: {str(e)}")

@router.delete("/prompts/{template_id}")
async def delete_prompt_template(template_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить шаблон промпта"""
    result = await PromptTemplate.delete(db, template_id)
    if not result:
        logger.error(f"Шаблон промпта с ID {template_id} не найден")
        raise HTTPException(status_code=404, detail="Шаблон не найден")
    
    return {"status": "success", "message": "Шаблон удален"} 