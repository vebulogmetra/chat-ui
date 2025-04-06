import uvicorn
import asyncio
import os
from dotenv import load_dotenv
from app.database.db import init_db
from app.database.seed_data import seed_default_prompts
from main import app
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.db import async_session

# Загружаем переменные окружения
load_dotenv()

async def setup():
    # Инициализация базы данных
    await init_db()
    
    # Добавление начальных данных
    async with async_session() as session:
        await seed_default_prompts(session)

if __name__ == "__main__":
    # Запускаем инициализацию
    asyncio.run(setup())
    
    # Определяем порт и хост из переменных окружения или используем значения по умолчанию
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    
    # Запускаем сервер
    uvicorn.run("main:app", host=host, port=port, reload=os.environ.get("DEBUG", "False").lower() == "true") 