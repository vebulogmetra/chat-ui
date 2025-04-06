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
        if model_settings and model_settings.system_prompt:
            system_prompt = model_settings.system_prompt
        
        # Получить настройки модели
        temperature = 0.7
        max_tokens = 1024
        
        if model_settings:
            temperature = float(model_settings.temperature) if model_settings.temperature else 0.7
            max_tokens = int(model_settings.max_tokens) if model_settings.max_tokens else 1024
        
        # Получить ответ от модели
        response_content = await self.ollama_service.chat_completion(
            model=model.name,
            messages=[
                {"role": "system", "content": system_prompt},
                *message_history
            ],
            temperature=temperature,
            max_tokens=max_tokens
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