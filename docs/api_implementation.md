# Примеры реализации API-слоя

В этом документе представлены примеры реализации API-слоя, который возвращает данные в формате JSON вместо HTML-шаблонов. Эти примеры помогут разработчикам при переходе от текущей архитектуры к архитектуре с разделением фронтенда и бэкенда.

## Структура API-слоя

```
app/
├── api/
│   ├── __init__.py
│   ├── router.py  # Основной маршрутизатор API
│   └── routes/
│       ├── __init__.py
│       ├── chat_api.py
│       ├── model_api.py
│       └── template_api.py
```

## Пример API-маршрута для чатов

Ниже представлен пример того, как можно реализовать API-маршруты для чатов:

```python
# app/api/routes/chat_api.py

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.schemas.chat import ChatCreate, ChatResponse, MessageRequest, MessageResponse
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
```

## Пример сервиса для чатов

Реализация сервиса, который используется как API, так и веб-представлениями:

```python
# app/services/chat_service.py

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Chat, Message, ChatModel, ModelSettings
from app.services.ollama_service import OllamaService

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ollama_service = OllamaService()
    
    async def get_all_chats(self) -> List[Dict[str, Any]]:
        """Получить все чаты"""
        chats = await Chat.get_all(self.db)
        return [
            {
                "id": chat.id,
                "title": chat.title,
                "created_at": chat.created_at,
                "model_id": chat.model_id
            } 
            for chat in chats
        ]
    
    async def get_chat_by_id(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """Получить чат по ID"""
        chat = await Chat.get_by_id(self.db, chat_id)
        if not chat:
            return None
        
        return {
            "id": chat.id,
            "title": chat.title,
            "created_at": chat.created_at,
            "model_id": chat.model_id
        }
    
    async def create_chat(self, title: str, model_id: int) -> Dict[str, Any]:
        """Создать новый чат"""
        # Проверить существование модели
        model = await ChatModel.get_by_id(self.db, model_id)
        if not model:
            raise ValueError(f"Модель с ID {model_id} не найдена")
        
        # Создать чат
        chat = await Chat.create(self.db, title, model_id)
        
        return {
            "id": chat.id,
            "title": chat.title,
            "created_at": chat.created_at,
            "model_id": chat.model_id
        }
    
    async def get_chat_messages(self, chat_id: int) -> List[Dict[str, Any]]:
        """Получить сообщения чата"""
        messages = await Message.get_by_chat_id(self.db, chat_id)
        return [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at
            }
            for msg in messages
        ]
    
    async def add_message_and_get_response(
        self, 
        chat_id: int, 
        content: str
    ) -> Dict[str, Any]:
        """Добавить сообщение пользователя и получить ответ от модели"""
        # Проверить существование чата
        chat = await Chat.get_by_id(self.db, chat_id)
        if not chat:
            raise ValueError(f"Чат с ID {chat_id} не найден")
        
        # Получить модель и ее настройки
        model = await ChatModel.get_by_id(self.db, chat.model_id)
        if not model:
            raise ValueError(f"Модель для чата не найдена")
        
        model_settings = await ModelSettings.get_by_model_id(self.db, model.id)
        
        # Добавить сообщение пользователя
        user_message = await Message.create(
            self.db, 
            chat_id=chat_id, 
            role="user", 
            content=content
        )
        
        # Получить историю сообщений
        messages = await Message.get_by_chat_id(self.db, chat_id)
        message_history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Подготовить системный промпт
        system_prompt = "Вы полезный помощник."
        if model_settings:
            system_prompt = model_settings.system_prompt
        
        # Получить ответ от модели
        response_content = await self.ollama_service.chat_completion(
            model=model.name,
            messages=[
                {"role": "system", "content": system_prompt},
                *message_history
            ],
            temperature=float(model_settings.temperature) if model_settings else 0.7,
            max_tokens=int(model_settings.max_tokens) if model_settings else 1024
        )
        
        # Сохранить ответ модели
        assistant_message = await Message.create(
            self.db,
            chat_id=chat_id,
            role="assistant",
            content=response_content
        )
        
        return {
            "id": assistant_message.id,
            "role": assistant_message.role,
            "content": assistant_message.content,
            "created_at": assistant_message.created_at
        }
    
    async def delete_chat(self, chat_id: int) -> bool:
        """Удалить чат"""
        return await Chat.delete(self.db, chat_id)
```

## Интеграция API-слоя

В main.py нужно включить новый API-маршрутизатор:

```python
# app/main.py

# ... существующий код ...
from app.api.router import api_router

# ... существующий код ...

# Включение API-маршрутов
app.include_router(api_router)

# ... существующий код ...
```

## Создание главного API-маршрутизатора

```python
# app/api/router.py

from fastapi import APIRouter
from app.api.routes import chat_api, model_api, template_api

api_router = APIRouter()

api_router.include_router(chat_api.router)
api_router.include_router(model_api.router)
api_router.include_router(template_api.router)
```

## Пример использования API из веб-представления

```python
# app/views/routes/chat_views.py

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db
from app.services.chat_service import ChatService
from app.services.model_service import ModelService

router = APIRouter(prefix="/chat", tags=["chat_views"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    """Главная страница"""
    model_service = ModelService(db)
    models = await model_service.get_all_models()
    return templates.TemplateResponse("index.html", {"request": request, "models": models})

@router.get("/chats", response_class=HTMLResponse)
async def get_chats_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Страница списка чатов"""
    chat_service = ChatService(db)
    model_service = ModelService(db)
    
    chats = await chat_service.get_all_chats()
    models = await model_service.get_all_models()
    
    return templates.TemplateResponse(
        "chats.html", {"request": request, "chats": chats, "models": models}
    )
```

## Схемы данных (Pydantic-модели)

```python
# app/schemas/chat.py

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class ChatBase(BaseModel):
    title: str

class ChatCreate(ChatBase):
    model_id: int

class ChatResponse(ChatBase):
    id: int
    created_at: datetime
    model_id: int

class MessageBase(BaseModel):
    content: str

class MessageRequest(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    role: str
    created_at: datetime
``` 