from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ModelSettings(BaseModel):
    id: int
    model_id: int
    temperature: float = 0.7
    max_tokens: int = 1024
    system_prompt: Optional[str] = None
    
    class Config:
        orm_mode = True

class ModelResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    
    class Config:
        orm_mode = True

class ModelWithSettings(ModelResponse):
    settings: Optional[ModelSettings] = None
    
    class Config:
        orm_mode = True 