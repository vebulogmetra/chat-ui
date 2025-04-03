import json
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import Chat, Message, ChatModel, ModelSettings, PromptTemplate

@pytest.mark.asyncio
async def test_chat_model(db_session: AsyncSession):
    """Тест модели Chat"""
    # Создаем новый чат
    chat = Chat(title="Тестовый чат")
    db_session.add(chat)
    await db_session.commit()
    
    # Получаем чат по ID
    chat_from_db = await Chat.get_by_id(db_session, chat.id)
    assert chat_from_db is not None
    assert chat_from_db.title == "Тестовый чат"
    
    # Получаем все чаты
    chats = await Chat.get_all(db_session)
    assert len(chats) > 0
    assert any(c.title == "Тестовый чат" for c in chats)
    
    # Удаляем чат
    result = await Chat.delete(db_session, chat.id)
    assert result is True
    
    # Проверяем, что чат удален
    chat_from_db = await Chat.get_by_id(db_session, chat.id)
    assert chat_from_db is None

@pytest.mark.asyncio
async def test_message_model(db_session: AsyncSession):
    """Тест модели Message"""
    # Сначала создаем чат
    chat = Chat(title="Тестовый чат для сообщений")
    db_session.add(chat)
    await db_session.commit()
    
    # Создаем сообщение
    message = await Message.create(
        db_session, 
        chat_id=chat.id, 
        role="user", 
        content="Тестовое сообщение"
    )
    
    # Проверяем, что сообщение создано
    assert message.chat_id == chat.id
    assert message.role == "user"
    assert message.content == "Тестовое сообщение"
    
    # Получаем сообщения чата
    messages = await Message.get_by_chat_id(db_session, chat.id)
    assert len(messages) == 1
    assert messages[0].content == "Тестовое сообщение"
    
    # Очистка - удаляем чат (и его сообщения каскадно)
    await Chat.delete(db_session, chat.id)

@pytest.mark.asyncio
async def test_chat_model_model(db_session: AsyncSession):
    """Тест модели ChatModel"""
    # Создаем модель
    model = ChatModel(
        name="test-model",
        display_name="Test Model",
        description="Тестовая модель"
    )
    db_session.add(model)
    await db_session.commit()
    
    # Проверяем, что модель создана
    model_from_db = await ChatModel.get_by_name(db_session, "test-model")
    assert model_from_db is not None
    assert model_from_db.name == "test-model"
    assert model_from_db.display_name == "Test Model"
    assert model_from_db.description == "Тестовая модель"
    
    # Получаем все модели
    models = await ChatModel.get_all(db_session)
    assert len(models) > 0
    assert any(m.name == "test-model" for m in models)

@pytest.mark.asyncio
async def test_model_settings(db_session: AsyncSession):
    """Тест модели ModelSettings"""
    # Сначала создаем модель
    model = ChatModel(
        name="test-model-settings",
        display_name="Test Model Settings",
        description="Тестовая модель для настроек"
    )
    db_session.add(model)
    await db_session.commit()
    
    # Создаем настройки для модели
    settings = ModelSettings(
        model_id=model.id,
        temperature="0.7",
        top_p="0.9",
        top_k="40",
        system_prompt="Тестовый системный промпт"
    )
    db_session.add(settings)
    await db_session.commit()
    
    # Получаем настройки по ID модели
    settings_from_db = await ModelSettings.get_by_model_id(db_session, model.id)
    assert settings_from_db is not None
    assert settings_from_db.temperature == "0.7"
    assert settings_from_db.top_p == "0.9"
    assert settings_from_db.top_k == "40"
    assert settings_from_db.system_prompt == "Тестовый системный промпт"
    
    # Обновляем настройки
    settings.temperature = "0.8"
    await db_session.commit()
    
    settings_from_db = await ModelSettings.get_by_model_id(db_session, model.id)
    assert settings_from_db.temperature == "0.8"

@pytest.mark.asyncio
async def test_prompt_template_model(db_session: AsyncSession):
    """Тест модели PromptTemplate"""
    # Создаем шаблон промпта
    template = PromptTemplate(
        name="Тестовый шаблон",
        description="Описание тестового шаблона",
        system_prompt="Тестовый системный промпт",
        user_prompt="Тестовый пользовательский промпт"
    )
    db_session.add(template)
    await db_session.commit()
    
    # Получаем шаблон по ID
    template_from_db = await PromptTemplate.get_by_id(db_session, template.id)
    assert template_from_db is not None
    assert template_from_db.name == "Тестовый шаблон"
    assert template_from_db.description == "Описание тестового шаблона"
    assert template_from_db.system_prompt == "Тестовый системный промпт"
    assert template_from_db.user_prompt == "Тестовый пользовательский промпт"
    
    # Получаем все шаблоны
    templates = await PromptTemplate.get_all(db_session)
    assert len(templates) > 0
    assert any(t.name == "Тестовый шаблон" for t in templates)
    
    # Удаляем шаблон
    result = await PromptTemplate.delete(db_session, template.id)
    assert result is True
    
    # Проверяем, что шаблон удален
    template_from_db = await PromptTemplate.get_by_id(db_session, template.id)
    assert template_from_db is None 