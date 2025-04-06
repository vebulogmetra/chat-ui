# Решения для обнаруженных проблем

## Проблемы с маршрутизацией API

### Проблема
При запуске приложения API-эндпоинты не отвечают по ожидаемым URL. Запросы к `/api/chat/chats` и другим API-эндпоинтам возвращают ошибку "Not Found".

### Решения

#### Вариант 1: Исправление префиксов маршрутов
В файлах API-маршрутов (`chat_api.py`, `model_api.py`, `template_api.py`) префиксы уже включают `/api/`. Возможно, происходит дублирование префиксов.

Как исправить:
1. Изменить префиксы в API-маршрутах:

```python
# Было
router = APIRouter(prefix="/api/chat", tags=["chat_api"])

# Стало
router = APIRouter(prefix="/chat", tags=["chat_api"])
```

2. Добавить общий префикс в главном маршрутизаторе API:

```python
# app/api/router.py
from fastapi import APIRouter
from app.api.routes import chat_api, model_api, template_api

# Создаем основной маршрутизатор для API с префиксом /api
api_router = APIRouter(prefix="/api")

# Подключаем все маршруты
api_router.include_router(chat_api.router)
api_router.include_router(model_api.router)
api_router.include_router(template_api.router)
```

#### Вариант 2: Проверка путей через отладку

Добавить логирование в `main.py` для просмотра доступных путей приложения:

```python
@app.on_event("startup")
async def startup_event():
    # ... существующий код ...
    
    # Вывод всех доступных путей
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": route.methods if hasattr(route, "methods") else None
        })
    logger.info(f"Доступные маршруты: {routes}")
```

#### Вариант 3: Временный обходной путь

Создать дополнительные маршруты-перенаправления для API-эндпоинтов:

```python
# В конце main.py
@app.get("/api/{path:path}")
async def api_redirect(path: str, request: Request):
    """Временное решение для перенаправления API-запросов"""
    logger.info(f"Получен запрос к API: /api/{path}")
    # Перенаправление на правильный обработчик
    return await app.routes[path](request)
```

## Решение проблемы с существующими маршрутами

### Проблема
Существующие маршруты (из `app/routes/`) и новые маршруты (из `app/api/` и `app/views/`) могут конфликтовать.

### Решения

#### Постепенная миграция на новые маршруты
1. Создать временный файл с отображением старых маршрутов на новые:
```python
# app/routes_migration.py
ROUTE_MAPPING = {
    "/chat/chats": "/api/chat/chats",  # Старый путь -> Новый путь
    # ... и так далее
}
```

2. Добавить промежуточное ПО для перенаправления со старых путей на новые:
```python
@app.middleware("http")
async def route_migration_middleware(request: Request, call_next):
    """Перенаправление со старых маршрутов на новые"""
    path = request.url.path
    if path in ROUTE_MAPPING:
        logger.info(f"Перенаправление с {path} на {ROUTE_MAPPING[path]}")
        return RedirectResponse(url=ROUTE_MAPPING[path])
    
    response = await call_next(request)
    return response
```

#### Организация временного сосуществования
Использовать разные префиксы для старых и новых маршрутов:
```python
# Старые маршруты
app.include_router(chat_routes.router, prefix="/legacy")
app.include_router(model_routes.router, prefix="/legacy")
app.include_router(template_routes.router, prefix="/legacy")

# Новые API-маршруты
app.include_router(api_router, prefix="/api")

# Новые веб-маршруты (без префикса, заменяют старые)
app.include_router(views_router)
```

## Организация тестирования API-эндпоинтов

### Создание тестов с использованием TestClient

```python
# tests/api/test_chat_api.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_chats():
    response = client.get("/api/chat/chats")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_chat():
    data = {"title": "Test Chat", "model_id": 1}
    response = client.post("/api/chat/chats", json=data)
    assert response.status_code == 200
    assert response.json()["title"] == "Test Chat"
```

### Создание шаблона для тестов API

```python
# tests/api/template.py
from fastapi.testclient import TestClient
from main import app
import pytest

@pytest.fixture
def api_client():
    """Фикстура для TestClient с автоматической очисткой DB после тестов"""
    client = TestClient(app)
    # Здесь можно добавить код для настройки тестовой базы данных
    yield client
    # Здесь можно добавить код для очистки после тестов

def test_api_endpoint(api_client, endpoint, method="get", data=None, expected_status=200):
    """Шаблон для тестирования API-эндпоинтов"""
    if method.lower() == "get":
        response = api_client.get(endpoint)
    elif method.lower() == "post":
        response = api_client.post(endpoint, json=data)
    elif method.lower() == "put":
        response = api_client.put(endpoint, json=data)
    elif method.lower() == "delete":
        response = api_client.delete(endpoint)
    
    assert response.status_code == expected_status
    return response.json()
``` 