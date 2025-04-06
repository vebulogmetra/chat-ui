import logging
from typing import List, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.services.chat_service import ChatService
from app.services.model_service import ModelService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat_views"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    """Главная страница"""
    model_service = ModelService(db)
    models = await model_service.get_all_models()
    return templates.TemplateResponse("index.html", {"request": request, "models": models})

@router.get("/chat/chats", response_class=HTMLResponse)
async def get_chats_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Страница списка чатов"""
    chat_service = ChatService(db)
    model_service = ModelService(db)
    
    chats = await chat_service.get_all_chats()
    models = await model_service.get_all_models()
    
    return templates.TemplateResponse(
        "chats.html", {"request": request, "chats": chats, "models": models}
    )

@router.post("/chat/chats/new")
async def create_chat(
    request: Request, 
    db: AsyncSession = Depends(get_db),
    title: str = Form(...),
    model_id: str = Form(...)
):
    """Создать новый чат"""
    try:
        chat_service = ChatService(db)
        
        # Преобразуем model_id в int
        model_id_int = int(model_id)
        
        # Создаем чат
        chat = await chat_service.create_chat(title, model_id_int)
        
        # Перенаправляем на страницу чата
        return RedirectResponse(url=f"/chat/chats/{chat['id']}", status_code=303)
    except ValueError as e:
        logger.error(f"Ошибка при создании чата: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при создании чата: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при создании чата: {str(e)}")

@router.get("/chat/chats/{chat_id}", response_class=HTMLResponse)
async def get_chat(chat_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """Получить чат по ID"""
    try:
        chat_service = ChatService(db)
        model_service = ModelService(db)
        
        # Получаем данные чата
        chat = await chat_service.get_chat_by_id(chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail=f"Чат с ID={chat_id} не найден")
        
        # Получаем сообщения чата
        messages = await chat_service.get_chat_messages(chat_id)
        
        # Получаем список моделей
        models = await model_service.get_all_models()
        
        # Получаем список всех чатов для сайдбара
        chats = await chat_service.get_all_chats()
        
        return templates.TemplateResponse(
            "chat.html", {
                "request": request, 
                "chat": chat,
                "current_chat": chat,
                "messages": messages, 
                "models": models,
                "chats": chats
            }
        )
    except Exception as e:
        logger.error(f"Ошибка при получении чата: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении чата: {str(e)}")

@router.post("/chat/chats/{chat_id}/messages")
async def add_message(
    chat_id: int, 
    request: Request,
    content: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """Добавить сообщение в чат и получить ответ"""
    try:
        chat_service = ChatService(db)
        
        # Добавляем сообщение и получаем ответ
        await chat_service.add_message_and_get_response(chat_id, content)
        
        # Перенаправляем обратно в чат
        return RedirectResponse(url=f"/chat/chats/{chat_id}", status_code=303)
    except ValueError as e:
        logger.error(f"Ошибка при добавлении сообщения: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при добавлении сообщения: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении сообщения: {str(e)}")

@router.get("/chat/chats/{chat_id}/delete")
async def delete_chat_page(chat_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить чат и перенаправить на страницу со списком чатов"""
    try:
        chat_service = ChatService(db)
        success = await chat_service.delete_chat(chat_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Чат с ID={chat_id} не найден")
        
        # Перенаправляем на страницу со списком чатов
        return RedirectResponse(url="/chat/chats", status_code=303)
    except Exception as e:
        logger.error(f"Ошибка при удалении чата: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении чата: {str(e)}") 