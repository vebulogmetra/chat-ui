from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

# Базовые модели для моделей чата
class ChatModelBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None

class ChatModelCreate(ChatModelBase):
    pass

class ChatModelResponse(ChatModelBase):
    id: int
    
    class Config:
        from_attributes = True

# Модели для настроек модели
class ModelSettingsBase(BaseModel):
    temperature: str = Field(default="0.7")
    top_p: str = Field(default="0.9")
    top_k: str = Field(default="40")
    max_tokens: str = Field(default="1024")
    system_prompt: str = Field(default="Вы полезный помощник.")

class ModelSettingsCreate(ModelSettingsBase):
    model_id: int

class ModelSettingsUpdate(ModelSettingsBase):
    temperature: Optional[str] = None
    top_p: Optional[str] = None
    top_k: Optional[str] = None
    max_tokens: Optional[str] = None
    system_prompt: Optional[str] = None

class ModelSettingsResponse(ModelSettingsBase):
    id: int
    model_id: int
    
    class Config:
        from_attributes = True

# Полная модель с настройками
class ChatModelWithSettings(ChatModelResponse):
    settings: Optional[ModelSettingsResponse] = None 