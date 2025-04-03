import pytest
import os
import sys
import asyncio
from typing import AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.db import Base, get_db
from main import app

# Используем SQLite в памяти для тестов
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Создаем движок базы данных для тестов
engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

# Создаем сессии для тестов
async_session_test = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Переопределяем зависимость get_db
async def override_get_db():
    """Переопределение зависимости для тестов"""
    async with async_session_test() as session:
        try:
            yield session
        finally:
            await session.close()

# Переопределяем зависимость в приложении для тестов
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для использования в асинхронных тестах."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_test_db():
    """Создает и подготавливает тестовую базу данных."""
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Удаляем таблицы после использования
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(setup_test_db) -> AsyncGenerator[AsyncSession, None]:
    """Дает сессию базы данных для каждого теста."""
    async with async_session_test() as session:
        yield session
        # Сбрасываем изменения после каждого теста
        await session.rollback()

@pytest.fixture
def test_client() -> TestClient:
    """Создает тестовый клиент для FastAPI."""
    return TestClient(app) 