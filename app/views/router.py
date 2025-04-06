from fastapi import APIRouter
from app.views.routes import chat_views

# Создаем основной маршрутизатор для веб-представлений
views_router = APIRouter()

# Подключаем все маршруты веб-представлений
views_router.include_router(chat_views.router) 