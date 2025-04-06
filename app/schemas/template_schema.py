from datetime import datetime
from typing import Optional
from pydantic import BaseModel

# Базовые модели для шаблонов промптов
class TemplateBase(BaseModel):
    name: str
    system_prompt: str
    description: str
    user_prompt: str

class TemplateCreate(TemplateBase):
    pass

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    system_prompt: Optional[str] = None
    description: Optional[str] = None
    user_prompt: Optional[str] = None

class TemplateResponse(TemplateBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True 