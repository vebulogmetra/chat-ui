from fastapi import APIRouter, Depends, Request, WebSocket, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import json
from typing import List, Dict, Any, Optional

from app.database.db import get_db
from app.models.models import Chat, Message, ChatModel, ModelSettings
from app.services.ollama_service import OllamaService

router = APIRouter(prefix="/chat", tags=["chat"])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def chat_list(request: Request, db: AsyncSession = Depends(get_db)):
    chats = await Chat.get_all(db)
    models = await ChatModel.get_all(db)
    return templates.TemplateResponse(
        "chat_list.html", {"request": request, "chats": chats, "models": models}
    )

@router.post("/create")
async def create_chat(title: str = Form("Новый чат"), db: AsyncSession = Depends(get_db)):
    chat = await Chat.create(db, title)
    return {"id": chat.id, "title": chat.title}

@router.get("/{chat_id}", response_class=HTMLResponse)
async def get_chat(request: Request, chat_id: int, db: AsyncSession = Depends(get_db)):
    chat = await Chat.get_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    messages = await Message.get_by_chat_id(db, chat_id)
    models = await ChatModel.get_all(db)
    return templates.TemplateResponse(
        "chat.html", 
        {"request": request, "chat": chat, "messages": messages, "models": models}
    )

@router.delete("/{chat_id}")
async def delete_chat(chat_id: int, db: AsyncSession = Depends(get_db)):
    success = await Chat.delete(db, chat_id)
    if not success:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return {"status": "success"}

@router.post("/{chat_id}/messages")
async def add_message(
    chat_id: int,
    message: str = Form(...),
    model_name: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    # Проверяем существование чата
    chat = await Chat.get_by_id(db, chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    # Добавляем сообщение пользователя
    user_message = await Message.create(db, chat_id, "user", message)
    
    # Получаем настройки модели
    model_settings = await ModelSettings.get_default_for_model(db, model_name)
    if not model_settings:
        model_settings = await ModelSettings.create(db, model_name)
    
    # Получаем историю чата
    chat_messages = await Message.get_by_chat_id(db, chat_id)
    message_history = [{"role": msg.role, "content": msg.content} for msg in chat_messages]
    
    # Добавляем системный промпт если он есть
    if model_settings.system_prompt:
        message_history.insert(0, {"role": "system", "content": model_settings.system_prompt})
    
    # Генерируем ответ от модели
    completion_text = ""
    async for chunk in OllamaService.generate_completion(
        model=model_name,
        messages=message_history,
        temperature=model_settings.temperature,
        max_tokens=model_settings.max_tokens
    ):
        completion_text += chunk
    
    # Сохраняем ответ модели
    ai_message = await Message.create(db, chat_id, "assistant", completion_text)
    
    return {
        "user_message": {
            "id": user_message.id,
            "content": user_message.content,
            "role": user_message.role
        },
        "ai_message": {
            "id": ai_message.id,
            "content": ai_message.content,
            "role": ai_message.role
        }
    }

@router.websocket("/ws/{chat_id}")
async def chat_websocket(websocket: WebSocket, chat_id: int, db: AsyncSession = Depends(get_db)):
    await websocket.accept()
    
    try:
        # Проверяем существование чата
        chat = await Chat.get_by_id(db, chat_id)
        if not chat:
            await websocket.close(code=1000, reason="Чат не найден")
            return
        
        while True:
            data = await websocket.receive_text()
            try:
                request_data = json.loads(data)
                message = request_data.get("message", "")
                model_name = request_data.get("model", "")
                
                if not message or not model_name:
                    await websocket.send_json({"error": "Отсутствуют обязательные поля"})
                    continue
                
                # Добавляем сообщение пользователя
                user_message = await Message.create(db, chat_id, "user", message)
                await websocket.send_json({
                    "type": "user_message",
                    "id": user_message.id,
                    "content": user_message.content
                })
                
                # Получаем настройки модели
                model_settings = await ModelSettings.get_default_for_model(db, model_name)
                if not model_settings:
                    model_settings = await ModelSettings.create(db, model_name)
                
                # Получаем историю чата
                chat_messages = await Message.get_by_chat_id(db, chat_id)
                message_history = [{"role": msg.role, "content": msg.content} for msg in chat_messages]
                
                # Добавляем системный промпт если он есть
                if model_settings.system_prompt:
                    message_history.insert(0, {"role": "system", "content": model_settings.system_prompt})
                
                # Создаем пустое сообщение для ответа AI
                ai_message = await Message.create(db, chat_id, "assistant", "")
                ai_response = ""
                
                # Отправляем начало ответа
                await websocket.send_json({
                    "type": "assistant_start", 
                    "id": ai_message.id
                })
                
                # Генерируем и отправляем ответ от модели по частям
                async for chunk in OllamaService.generate_completion(
                    model=model_name,
                    messages=message_history,
                    temperature=model_settings.temperature,
                    max_tokens=model_settings.max_tokens
                ):
                    ai_response += chunk
                    await websocket.send_json({
                        "type": "assistant_chunk",
                        "id": ai_message.id,
                        "chunk": chunk
                    })
                
                # Обновляем сообщение AI в базе данных
                ai_message.content = ai_response
                db.add(ai_message)
                await db.commit()
                
                # Отправляем завершение ответа
                await websocket.send_json({
                    "type": "assistant_end",
                    "id": ai_message.id,
                    "content": ai_response
                })
                
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Некорректный формат JSON"})
            except Exception as e:
                await websocket.send_json({"error": str(e)})
    
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        try:
            await websocket.close()
        except:
            pass 