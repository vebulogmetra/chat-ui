import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect, HTTPException, Form, Body
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database.db import get_db
from app.models.models import Chat, Message, ChatModel, ModelSettings
from app.services.ollama_service import OllamaService

# Настраиваем логгер
logger = logging.getLogger(__name__)

# Создаем модель для запроса на создание чата
class ChatCreate(BaseModel):
    title: str
    model_id: str

# Схема для запроса сообщения
class MessageRequest(BaseModel):
    content: str

router = APIRouter(prefix="/chat", tags=["chat"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: AsyncSession = Depends(get_db)):
    """Главная страница"""
    models = await ChatModel.get_all(db)
    return templates.TemplateResponse("index.html", {"request": request, "models": models})

@router.get("/chats", response_class=HTMLResponse)
async def get_chats_page(request: Request, db: AsyncSession = Depends(get_db)):
    """Страница списка чатов"""
    chats = await Chat.get_all(db)
    models = await ChatModel.get_all(db)
    return templates.TemplateResponse(
        "chats.html", {"request": request, "chats": chats, "models": models}
    )

@router.get("/chats/list")
async def list_chats(db: AsyncSession = Depends(get_db)):
    """Получить список всех чатов"""
    chats = await Chat.get_all(db)
    return [
        {
            "id": chat.id,
            "title": chat.title,
            "created_at": chat.created_at
        } 
        for chat in chats
    ]

@router.post("/chats/new")
async def create_chat(
    request: Request, 
    db: AsyncSession = Depends(get_db),
    chat_data: ChatCreate = None,
    title: str = Form(None),
    model_id: str = Form(None)
):
    """Создать новый чат"""
    logger.info(f"ПОЛУЧЕН ЗАПРОС НА СОЗДАНИЕ ЧАТА")
    logger.info(f"Form данные: title={title}, model_id={model_id}")
    logger.info(f"JSON данные: {chat_data}")
    
    try:
        # Используем Form данные, если они есть, иначе JSON
        if title is not None and model_id is not None:
            chat_create_data = ChatCreate(title=title, model_id=model_id)
        elif chat_data:
            chat_create_data = chat_data
        else:
            raise HTTPException(status_code=400, detail="Не указаны данные для создания чата")
        
        # Логируем полученные данные
        logger.info(f"Получены данные для создания чата: {chat_create_data.dict()}")
        
        # Проверяем, существует ли модель с указанным ID
        try:
            model_id = int(chat_create_data.model_id)
            logger.info(f"Преобразованный ID модели: {model_id}")
        except ValueError as ve:
            logger.error(f"Ошибка преобразования ID модели: {str(ve)}")
            raise HTTPException(status_code=400, detail=f"Неверный ID модели: {chat_create_data.model_id}")
        
        # Получаем модель
        model = await ChatModel.get_by_id(db, model_id)
        logger.info(f"Результат запроса модели: {model}")
        
        if not model:
            logger.error(f"Модель с ID {model_id} не найдена")
            raise HTTPException(status_code=404, detail=f"Модель с ID {model_id} не найдена")
        
        # Создаем новый чат с указанием модели
        logger.info(f"Создание чата с названием: {chat_create_data.title} и моделью: {model_id}")
        chat = await Chat.create(db, chat_create_data.title, model_id)
        
        logger.info(f"Успешно создан чат: ID={chat.id}, title={chat.title}, model_id={chat.model_id}")
        
        # Если запрос был из формы - перенаправляем на страницу чата
        content_type = request.headers.get("content-type", "")
        if "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            return RedirectResponse(url=f"/chat/chats/{chat.id}", status_code=303)
        
        # Для API запросов возвращаем JSON
        return {
            "id": chat.id,
            "title": chat.title,
            "created_at": chat.created_at,
            "model_id": chat.model_id
        }
    except ValueError as e:
        logger.error(f"Ошибка при создании чата (ValueError): {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Неверный ID модели: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при создании чата: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при создании чата: {str(e)}")

@router.get("/chats/{chat_id}", response_class=HTMLResponse)
async def get_chat(chat_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """Получить чат по ID"""
    try:
        logger.info(f"Запрос чата с ID={chat_id}")
        
        # Получаем чат по ID
        chat = await Chat.get_by_id(db, chat_id)
        logger.info(f"Результат запроса чата: {chat}")
        
        if not chat:
            logger.error(f"Чат с ID={chat_id} не найден")
            raise HTTPException(status_code=404, detail=f"Чат с ID={chat_id} не найден")
        
        # Получаем все сообщения чата
        messages = await Message.get_by_chat_id(db, chat_id)
        logger.info(f"Получено {len(messages)} сообщений")
        
        # Получаем список всех моделей
        models = await ChatModel.get_all(db)
        logger.info(f"Получено {len(models)} моделей")
        
        # Возвращаем шаблон с данными
        logger.info(f"Отправка шаблона chat.html с данными чата ID={chat_id}")
        return templates.TemplateResponse(
            "chat.html", {
                "request": request, 
                "chat": chat,  # Имя переменной должно совпадать с используемым в шаблоне
                "current_chat": chat,  # Для совместимости с обоими вариантами
                "messages": messages, 
                "models": models,
                "chats": [chat]  # Для сайдбара, чтобы избежать ошибки с несуществующей переменной
            }
        )
    except Exception as e:
        logger.error(f"Ошибка при получении чата: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при получении чата: {str(e)}")

@router.post("/chats/{chat_id}/messages")
async def add_message(chat_id: int, message: MessageRequest, db: AsyncSession = Depends(get_db)):
    """Добавить сообщение в чат"""
    try:
        # Создаем экземпляр OllamaService
        ollama_service = OllamaService()
        
        # Проверяем, существует ли чат
        chat = await Chat.get_by_id(db, chat_id)
        if not chat:
            raise HTTPException(status_code=404, detail="Чат не найден")
        
        # Получаем модель, связанную с чатом
        model = await ChatModel.get_by_id(db, chat.model_id)
        if not model:
            raise HTTPException(status_code=404, detail="Модель не найдена")
        
        # Получаем настройки модели
        model_settings = await ModelSettings.get_by_model_id(db, model.id)
        if not model_settings:
            logger.warning(f"Настройки для модели {model.name} не найдены, используются значения по умолчанию")
            system_prompt = "Вы полезный помощник по имени Артём."
            temperature = 0.7
            max_tokens = 1024
        else:
            system_prompt = model_settings.system_prompt
            temperature = float(model_settings.temperature) if model_settings.temperature else 0.7
            max_tokens = int(model_settings.max_tokens) if model_settings.max_tokens else 1024
        
        # Добавляем сообщение от пользователя
        user_message = await Message.create(db, chat_id, "user", message.content)
        
        # Получаем все предыдущие сообщения для контекста
        messages = await Message.get_by_chat_id(db, chat_id)
        
        # Формируем контекст из последних 5 сообщений
        context_messages = []
        for msg in messages[-10:]:  # берем последние 10 сообщений для контекста
            context_messages.append(f"{msg.role}: {msg.content}")
        
        # Формируем полный промпт с контекстом
        full_prompt = "\n".join(context_messages)
        
        logger.info(f"Вызов generate_completion с моделью {model.name}, промпт длиной {len(full_prompt)}")
        
        # Генерируем ответ модели
        model_response = await ollama_service.generate_completion(
            model=model.name,
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        logger.info(f"Получен ответ от модели длиной {len(model_response)} символов")
        
        # Добавляем ответ модели в базу данных
        assistant_message = await Message.create(db, chat_id, "assistant", model_response)
        
        return {
            "user_message": {
                "id": user_message.id,
                "content": user_message.content,
                "role": user_message.role,
                "created_at": user_message.created_at
            },
            "assistant_message": {
                "id": assistant_message.id,
                "content": assistant_message.content,
                "role": assistant_message.role,
                "created_at": assistant_message.created_at
            }
        }
    except Exception as e:
        logger.error(f"Ошибка при добавлении сообщения: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ошибка при добавлении сообщения: {str(e)}")

@router.get("/chats/{chat_id}/messages")
async def get_messages(chat_id: int, db: AsyncSession = Depends(get_db)):
    """Получить все сообщения чата"""
    chat = await Chat.get_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    messages = await Message.get_by_chat_id(db, chat_id)
    
    return [
        {
            "id": message.id,
            "content": message.content,
            "role": message.role,
            "created_at": message.created_at
        } 
        for message in messages
    ]

@router.post("/{chat_id}/rename")
async def rename_chat(chat_id: int, title: str = Form(...), db: AsyncSession = Depends(get_db)):
    """Переименовать чат"""
    chat = await Chat.get_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    chat.title = title
    db.add(chat)
    await db.commit()
    await db.refresh(chat)
    
    return {"id": chat.id, "title": chat.title}

@router.delete("/chats/{chat_id}")
async def delete_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    """Удалить чат"""
    result = await Chat.delete(db, chat_id)
    if not result:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    return {"status": "success", "message": "Чат удален"}

@router.websocket("/ws/{chat_id}")
async def websocket_endpoint(websocket: WebSocket, chat_id: int, db: AsyncSession = Depends(get_db)):
    """WebSocket для потоковой передачи ответов модели"""
    await websocket.accept()
    
    try:
        # Проверяем существование чата
        chat = await Chat.get_by_id(db, chat_id)
        if not chat:
            await websocket.send_json({"error": "Чат не найден"})
            await websocket.close()
            return
        
        while True:
            # Ожидаем сообщение от клиента
            data = await websocket.receive_json()
            
            user_message = data.get("message", "")
            model_name = data.get("model", "")
            
            if not user_message or not model_name:
                await websocket.send_json({
                    "error": "Необходимо указать сообщение и модель"
                })
                continue
            
            # Проверяем существование модели
            model = await ChatModel.get_by_name(db, model_name)
            if not model:
                await websocket.send_json({
                    "error": f"Модель '{model_name}' не найдена"
                })
                continue
            
            # Получаем настройки модели
            settings = await ModelSettings.get_by_model_id(db, model.id)
            if not settings:
                temperature = 0.7
                max_tokens = 1024
                system_prompt = "Вы полезный помощник."
            else:
                temperature = settings.temperature
                max_tokens = settings.max_tokens
                system_prompt = settings.system_prompt
            
            # Сохраняем сообщение пользователя
            await Message.create(db, chat_id, "user", user_message)
            
            # Получаем историю сообщений для контекста
            messages = await Message.get_by_chat_id(db, chat_id)
            context = " ".join([msg.content for msg in messages[-5:] if msg.role == "user"])
            
            # Формируем промпт с контекстом предыдущих сообщений
            prompt = f"Контекст предыдущих сообщений (если есть): {context}\n\nСообщение пользователя: {user_message}"
            
            # Создаем экземпляр сервиса Ollama
            ollama_service = OllamaService()
            
            # Инициализируем буфер для полного ответа
            full_response = ""
            
            # Потоковая передача ответа от модели
            async for chunk in ollama_service.generate_stream(
                model=model_name,
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens
            ):
                full_response += chunk
                await websocket.send_json({
                    "chunk": chunk,
                    "done": False
                })
            
            # Сохраняем полный ответ в базу данных
            await Message.create(db, chat_id, "assistant", full_response)
            
            # Отправляем сигнал о завершении потока
            await websocket.send_json({
                "done": True,
                "full_response": full_response
            })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket отключен для чата {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка в WebSocket для чата {chat_id}: {str(e)}", exc_info=True)
        await websocket.send_json({"error": str(e)})
        await websocket.close()

@router.get("/{chat_id}", response_class=HTMLResponse)
async def get_chat_page(chat_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    """Страница конкретного чата"""
    chat = await Chat.get_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    chats = await Chat.get_all(db)
    models = await ChatModel.get_all(db)
    messages = await Message.get_by_chat_id(db, chat_id)
    
    return templates.TemplateResponse(
        "index.html", {
            "request": request, 
            "chats": chats, 
            "models": models,
            "current_chat": chat,
            "messages": messages
        }
    ) 