import uvicorn
import asyncio
from app.database.db import init_db
from main import app

async def setup():
    # Инициализация базы данных
    await init_db()

if __name__ == "__main__":
    # Запускаем инициализацию
    asyncio.run(setup())
    
    # Запускаем сервер
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 