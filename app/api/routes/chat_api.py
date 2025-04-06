import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.chat_schema import ChatCreate, ChatResponse, MessageRequest, MessageResponse, ChatWithMessages
from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat_api"])

@router.get("/chats", response_model=List[ChatResponse])
async def list_chats(db: AsyncSession = Depends(get_db)):
    """Получить список всех чатов"""
    chat_service = ChatService(db)
    chats = await chat_service.get_all_chats()
    return chats

@router.post("/chats", response_model=ChatResponse)
async def create_chat(chat_data: ChatCreate, db: AsyncSession = Depends(get_db)):
    """Создать новый чат"""
    try:
        chat_service = ChatService(db)
        chat = await chat_service.create_chat(chat_data.title, chat_data.model_id)
        return chat
    except ValueError as e:
        logger.error(f"Ошибка при создании чата: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при создании чата: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при создании чата: {str(e)}")

@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    """Получить чат по ID"""
    chat_service = ChatService(db)
    chat = await chat_service.get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail=f"Чат с ID={chat_id} не найден")
    return chat

@router.post("/chats/{chat_id}/messages", response_model=MessageResponse)
async def add_message(
    chat_id: int, 
    message: MessageRequest, 
    db: AsyncSession = Depends(get_db)
):
    """Добавить сообщение в чат и получить ответ от модели"""
    try:
        chat_service = ChatService(db)
        response = await chat_service.add_message_and_get_response(
            chat_id, 
            message.content
        )
        return response
    except ValueError as e:
        logger.error(f"Ошибка при добавлении сообщения: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Ошибка при добавлении сообщения: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении сообщения: {str(e)}")

@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_messages(chat_id: int, db: AsyncSession = Depends(get_db)):
    """Получить все сообщения чата"""
    chat_service = ChatService(db)
    messages = await chat_service.get_chat_messages(chat_id)
    return messages

@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить чат"""
    chat_service = ChatService(db)
    success = await chat_service.delete_chat(chat_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Чат с ID={chat_id} не найден")
    return {"status": "success", "message": f"Чат {chat_id} успешно удален"} 