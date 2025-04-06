from fastapi import APIRouter
from app.api.routes import chat_api, model_api, template_api

# Создаем основной маршрутизатор для API
api_router = APIRouter()

# Подключаем все маршруты
api_router.include_router(chat_api.router)
api_router.include_router(model_api.router)
api_router.include_router(template_api.router)
