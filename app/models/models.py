from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
import json
import datetime
import logging

from app.database.db import Base

logger = logging.getLogger(__name__)


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    model_id = Column(Integer, ForeignKey("models.id"))
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    model = relationship("ChatModel")

    @classmethod
    async def get_all(cls, db: AsyncSession):
        result = await db.execute(select(cls).order_by(cls.created_at.desc()))
        return result.scalars().all()
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, chat_id: int):
        result = await db.execute(select(cls).filter(cls.id == chat_id))
        return result.scalars().first()

    @classmethod
    async def create(cls, db: AsyncSession, title: str, model_id: int = None):
        chat = cls(title=title, model_id=model_id)
        db.add(chat)
        await db.commit()
        await db.refresh(chat)
        return chat
    
    @classmethod
    async def update(cls, db: AsyncSession, chat_id: int, title: str):
        chat = await cls.get_by_id(db, chat_id)
        if chat:
            chat.title = title
            await db.commit()
            await db.refresh(chat)
        return chat
    
    @classmethod
    async def delete(cls, db: AsyncSession, chat_id: int):
        chat = await cls.get_by_id(db, chat_id)
        if chat:
            await db.delete(chat)
            await db.commit()
            return True
        return False


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    role = Column(String(50))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    chat = relationship("Chat", back_populates="messages")

    @classmethod
    async def get_by_chat_id(cls, db: AsyncSession, chat_id: int):
        result = await db.execute(
            select(cls).filter(cls.chat_id == chat_id).order_by(cls.created_at)
        )
        return result.scalars().all()

    @classmethod
    async def create(cls, db: AsyncSession, chat_id: int, role: str, content: str):
        message = cls(chat_id=chat_id, role=role, content=content)
        db.add(message)
        await db.commit()
        await db.refresh(message)
        return message


class ChatModel(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    display_name = Column(String(100))
    description = Column(String(255))
    
    # Добавляем отношение к ModelSettings
    settings = relationship("ModelSettings", back_populates="model", uselist=False, cascade="all, delete-orphan")
    
    @classmethod
    async def get_all(cls, db: AsyncSession):
        result = await db.execute(select(cls))
        return result.scalars().all()
    
    @classmethod
    async def get_by_name(cls, db: AsyncSession, name: str):
        result = await db.execute(select(cls).filter(cls.name == name))
        return result.scalars().first()
    
    @classmethod
    async def create(cls, db: AsyncSession, name: str, display_name: str = None, description: str = None):
        if not display_name:
            display_name = name
        
        model = cls(name=name, display_name=display_name, description=description)
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return model
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, model_id: int):
        result = await db.execute(select(cls).filter(cls.id == model_id))
        return result.scalars().first()
    
    async def save(self, db: AsyncSession):
        """Сохраняет модель в базе данных."""
        db.add(self)
        await db.commit()
        await db.refresh(self)
        return self


class ModelSettings(Base):
    __tablename__ = "model_settings"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), unique=True)
    temperature = Column(String(10), default="0.7")
    top_p = Column(String(10), default="0.9")
    top_k = Column(String(10), default="40")
    max_tokens = Column(String(10), default="1024")
    system_prompt = Column(Text, default="Вы полезный помощник.")
    
    model = relationship("ChatModel", back_populates="settings")
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, settings_id: int):
        result = await db.execute(select(cls).filter(cls.id == settings_id))
        return result.scalars().first()
    
    @classmethod
    async def get_by_model_id(cls, db: AsyncSession, model_id: int):
        result = await db.execute(select(cls).filter(cls.model_id == model_id))
        settings = result.scalars().first()
        
        # Если настройки не найдены, создаем их с дефолтными значениями
        if not settings:
            settings = await cls.create(db, model_id)
        
        return settings
    
    @classmethod
    async def get_default_for_model(cls, db: AsyncSession, model_name: str):
        result = await db.execute(
            select(cls).filter(
                cls.model_name == model_name,
                cls.is_default == True
            )
        )
        return result.scalars().first()
    
    @classmethod
    async def create(cls, db: AsyncSession, model_id: int, temperature: str = "0.7", top_p: str = "0.9", top_k: str = "40", max_tokens: str = "1024", system_prompt: str = "Вы полезный помощник."):
        settings = cls(model_id=model_id, temperature=temperature, top_p=top_p, top_k=top_k, max_tokens=max_tokens, system_prompt=system_prompt)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
        return settings
        
    async def save(self, db: AsyncSession):
        """Сохраняет настройки модели в базе данных."""
        db.add(self)
        await db.commit()
        await db.refresh(self)
        return self


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), index=True)
    system_prompt = Column(Text)
    description = Column(String(255))
    user_prompt = Column(Text)
    
    @classmethod
    async def get_all(cls, db: AsyncSession):
        result = await db.execute(select(cls).order_by(cls.name))
        return result.scalars().all()
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, template_id: int):
        result = await db.execute(select(cls).filter(cls.id == template_id))
        return result.scalars().first()
        
    @classmethod
    async def delete(cls, db: AsyncSession, template_id: int):
        template = await cls.get_by_id(db, template_id)
        if template:
            await db.delete(template)
            await db.commit()
            return True
        return False
    
    @classmethod
    async def create(cls, db: AsyncSession, name: str, system_prompt: str, description: str = None, user_prompt: str = None):
        template = cls(
            name=name, 
            system_prompt=system_prompt, 
            description=description or "",
            user_prompt=user_prompt or ""
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template
        
    async def save(self, db: AsyncSession):
        """Сохраняет шаблон промпта в базе данных."""
        db.add(self)
        await db.commit()
        await db.refresh(self)
        return self 