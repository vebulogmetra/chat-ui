from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import relationship
import json

from app.database.db import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="Новый чат")
    created_at = Column(DateTime, server_default=func.now())
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")

    @classmethod
    async def get_all(cls, db: AsyncSession):
        result = await db.execute(select(cls).order_by(cls.created_at.desc()))
        return result.scalars().all()
    
    @classmethod
    async def get_by_id(cls, db: AsyncSession, chat_id: int):
        result = await db.execute(select(cls).filter(cls.id == chat_id))
        return result.scalars().first()

    @classmethod
    async def create(cls, db: AsyncSession, title: str = "Новый чат"):
        chat = cls(title=title)
        db.add(chat)
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
    role = Column(String)  # 'user' или 'assistant'
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    
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
    name = Column(String, unique=True, index=True)
    display_name = Column(String)
    description = Column(Text, nullable=True)
    
    @classmethod
    async def get_all(cls, db: AsyncSession):
        result = await db.execute(select(cls))
        return result.scalars().all()
    
    @classmethod
    async def get_by_name(cls, db: AsyncSession, name: str):
        result = await db.execute(select(cls).filter(cls.name == name))
        return result.scalars().first()
    
    @classmethod
    async def create(cls, db: AsyncSession, name: str, display_name: str, description: str = None):
        model = cls(name=name, display_name=display_name, description=description)
        db.add(model)
        await db.commit()
        await db.refresh(model)
        return model


class ModelSettings(Base):
    __tablename__ = "model_settings"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, ForeignKey("models.name"))
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=1024)
    system_prompt = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)
    
    settings_json = Column(Text, default="{}")
    
    @property
    def settings(self):
        return json.loads(self.settings_json)
    
    @settings.setter
    def settings(self, value):
        self.settings_json = json.dumps(value)
    
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
    async def create(cls, db: AsyncSession, model_name: str, temperature: float = 0.7, 
                    max_tokens: int = 1024, system_prompt: str = None, 
                    is_default: bool = False, settings: dict = None):
        settings_data = settings or {}
        setting = cls(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            system_prompt=system_prompt,
            is_default=is_default,
            settings_json=json.dumps(settings_data)
        )
        db.add(setting)
        await db.commit()
        await db.refresh(setting)
        return setting


class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text)
    user_prompt = Column(Text, nullable=True)
    
    @classmethod
    async def get_all(cls, db: AsyncSession):
        result = await db.execute(select(cls))
        return result.scalars().all()
    
    @classmethod
    async def create(cls, db: AsyncSession, name: str, system_prompt: str, 
                     description: str = None, user_prompt: str = None):
        template = cls(
            name=name, 
            description=description,
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template 