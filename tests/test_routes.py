import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import ChatModel, ModelSettings, PromptTemplate

# Тесты для маршрутов чатов
@pytest.mark.asyncio
async def test_create_chat(test_client: TestClient, db_session: AsyncSession):
    """Тест создания нового чата"""
    response = test_client.post("/chat/create")
    assert response.status_code == 200
    
    # Проверяем, что в ответе есть id и title
    data = response.json()
    assert "id" in data
    assert "title" in data
    assert data["title"] == "Новый чат"  # Значение по умолчанию

@pytest.mark.asyncio
async def test_list_chats(test_client: TestClient, db_session: AsyncSession):
    """Тест получения списка чатов"""
    # Сначала создаем чат
    test_client.post("/chat/create", json={"title": "Тестовый чат"})
    
    # Получаем список чатов
    response = test_client.get("/chat/list")
    assert response.status_code == 200
    
    # Проверяем, что в списке есть созданный чат
    chats = response.json()
    assert isinstance(chats, list)
    assert len(chats) > 0

@pytest.mark.asyncio
async def test_delete_chat(test_client: TestClient, db_session: AsyncSession):
    """Тест удаления чата"""
    # Сначала создаем чат
    create_response = test_client.post("/chat/create")
    chat_id = create_response.json()["id"]
    
    # Затем удаляем его
    response = test_client.delete(f"/chat/{chat_id}")
    assert response.status_code == 200
    
    # Проверяем ответ API
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Чат удален"

@pytest.mark.asyncio
async def test_get_messages(test_client: TestClient, db_session: AsyncSession):
    """Тест получения сообщений чата"""
    # Создаем чат
    create_response = test_client.post("/chat/create")
    chat_id = create_response.json()["id"]
    
    # Получаем сообщения (пока их нет)
    response = test_client.get(f"/chat/{chat_id}/messages")
    assert response.status_code == 200
    assert response.json() == []

# Тесты для маршрутов промптов
@pytest.mark.asyncio
async def test_list_prompt_templates(test_client: TestClient, db_session: AsyncSession):
    """Тест получения списка шаблонов промптов"""
    # Создаем шаблон для тестирования
    template = PromptTemplate(
        name="Тестовый шаблон",
        description="Описание тестового шаблона",
        system_prompt="Тестовый системный промпт",
        user_prompt="Тестовый пользовательский промпт"
    )
    db_session.add(template)
    await db_session.commit()
    
    # Получаем список шаблонов
    response = test_client.get("/models/prompts/list")
    assert response.status_code == 200
    
    # Проверяем, что в списке есть созданный шаблон
    templates = response.json()
    assert isinstance(templates, list)
    assert len(templates) > 0
    assert any(t["name"] == "Тестовый шаблон" for t in templates)

@pytest.mark.asyncio
async def test_add_prompt_template(test_client: TestClient, db_session: AsyncSession):
    """Тест добавления нового шаблона промпта"""
    prompt_data = {
        "name": "Новый тестовый шаблон",
        "description": "Описание нового тестового шаблона",
        "system_prompt": "Новый тестовый системный промпт",
        "user_prompt": "Новый тестовый пользовательский промпт"
    }
    
    response = test_client.post("/models/prompts/add", data=prompt_data)
    assert response.status_code == 200
    
    # Проверяем, что в ответе есть id и правильные данные
    data = response.json()
    assert "id" in data
    assert data["name"] == prompt_data["name"]
    assert data["description"] == prompt_data["description"]
    assert data["system_prompt"] == prompt_data["system_prompt"]
    assert data["user_prompt"] == prompt_data["user_prompt"]

@pytest.mark.asyncio
async def test_get_model_settings(test_client: TestClient, db_session: AsyncSession):
    """Тест получения настроек модели"""
    # Создаем модель и настройки перед тестом
    model = ChatModel(
        name="test-model-api",
        display_name="Test Model API",
        description="Тестовая модель для API"
    )
    db_session.add(model)
    await db_session.commit()
    
    settings = ModelSettings(
        model_id=model.id,
        temperature=0.7,
        max_tokens=1024,
        system_prompt="Тестовый системный промпт"
    )
    db_session.add(settings)
    await db_session.commit()
    
    # Получаем настройки через API
    response = test_client.get(f"/models/test-model-api/settings")
    assert response.status_code == 200
    
    # Проверяем данные ответа
    data = response.json()
    assert data["temperature"] == 0.7
    assert data["max_tokens"] == 1024
    assert data["system_prompt"] == "Тестовый системный промпт"

@pytest.mark.asyncio
async def test_save_model_settings(test_client: TestClient, db_session: AsyncSession):
    """Тест сохранения настроек модели"""
    # Создаем модель перед тестом
    model = ChatModel(
        name="test-model-save",
        display_name="Test Model Save",
        description="Тестовая модель для сохранения настроек"
    )
    db_session.add(model)
    await db_session.commit()
    
    # Данные для настроек
    settings_data = {
        "temperature": 0.8,
        "max_tokens": 2048,
        "system_prompt": "Новый системный промпт для тестов"
    }
    
    # Сохраняем настройки через API
    response = test_client.post(f"/models/test-model-save/settings", data=settings_data)
    assert response.status_code == 200
    
    # Проверяем успешный ответ
    data = response.json()
    assert data["status"] == "success"
    assert data["message"] == "Настройки сохранены"
    
    # Проверяем, что настройки были действительно сохранены в базе
    settings = await ModelSettings.get_by_model_id(db_session, model.id)
    assert settings is not None
    assert settings.temperature == 0.8
    assert settings.max_tokens == 2048
    assert settings.system_prompt == "Новый системный промпт для тестов" 