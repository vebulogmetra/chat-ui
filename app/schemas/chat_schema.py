from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

# Базовые модели для чатов
class ChatBase(BaseModel):
    title: str

class ChatCreate(ChatBase):
    model_id: int

class ChatResponse(ChatBase):
    id: int
    created_at: datetime
    model_id: int
    
    class Config:
        from_attributes = True

# Базовые модели для сообщений
class MessageBase(BaseModel):
    content: str

class MessageRequest(MessageBase):
    pass

class MessageResponse(MessageBase):
    id: int
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Модель для ответа с историей сообщений
class ChatWithMessages(ChatResponse):
    messages: List[MessageResponse] = [] 