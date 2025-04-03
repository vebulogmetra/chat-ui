import os
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# Получаем DATABASE_URL из переменных окружения, или используем SQLite по умолчанию
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "sqlite+aiosqlite:///./sqlite_app.db"
)
logger.info(f"Используется база данных: {DATABASE_URL}")

# Создаем движок базы данных
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    future=True
)

# Создаем сессии
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Создаем базовый класс для моделей
Base = declarative_base()

# Инициализация базы данных
async def init_db():
    """Инициализирует базу данных, создавая все таблицы."""
    async with engine.begin() as conn:
        # Полностью удаляем все существующие таблицы и создаем заново
        try:
            # Получаем список всех таблиц
            await conn.execute(text("PRAGMA foreign_keys = OFF"))
            
            # Удаляем таблицы вручную для обеспечения правильного порядка
            await conn.execute(text("DROP TABLE IF EXISTS model_settings"))
            await conn.execute(text("DROP TABLE IF EXISTS messages"))
            await conn.execute(text("DROP TABLE IF EXISTS chats"))
            await conn.execute(text("DROP TABLE IF EXISTS prompt_templates"))
            await conn.execute(text("DROP TABLE IF EXISTS models"))
            
            logger.info("Существующие таблицы удалены для обновления схемы")
        except Exception as e:
            logger.error(f"Ошибка при удалении таблиц: {e}")
        
        # Создаем все таблицы заново
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA foreign_keys = ON"))
    
    logger.info("База данных инициализирована с обновленной схемой")

# Функция для получения сессии базы данных
async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close() 