import os
import logging
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.database.db import init_db
from app.routes import chat_routes, model_routes, template_routes

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI()

# Добавление поддержки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Настройка шаблонов
templates = Jinja2Templates(directory="app/templates")

# Включение маршрутов
app.include_router(chat_routes.router)
app.include_router(model_routes.router)
app.include_router(template_routes.router)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.on_event("startup")
async def startup_db_client():
    logger.info("Инициализация базы данных при запуске...")
    await init_db()
    
    # Создание начальных шаблонов промптов, если их еще нет
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database.db import async_session
    from app.models.models import PromptTemplate, ChatModel, ModelSettings
    
    async with async_session() as session:
        # Создаем шаблоны промптов
        templates = await PromptTemplate.get_all(session)
        
        if not templates:
            logger.info("Создание начальных шаблонов промптов...")
            
            # Личный ассистент Артём
            artem_template = await PromptTemplate.create(
                session,
                name="Личный ассистент Артём",
                system_prompt="Ты дружелюбный персональный ассистент по имени Артём. Ты помогаешь пользователю с различными задачами, от ответов на вопросы до помощи в планировании и организации. Ты вежлив, внимателен и ориентирован на потребности пользователя.",
                description="Дружелюбный ассистент, который всегда готов помочь с различными задачами и ответить на вопросы.",
                user_prompt="Привет, Артём! Расскажи, чем ты можешь мне помочь?"
            )
            
            # Python разработчик
            await PromptTemplate.create(
                session,
                name="Python разработчик",
                system_prompt="Ты опытный Python разработчик с глубокими знаниями языка программирования Python, его библиотек и фреймворков. Ты помогаешь разрабатывать качественный, эффективный и хорошо документированный код. В своих ответах ты предлагаешь оптимальные решения и объясняешь ключевые концепции.",
                description="Эксперт по Python, который поможет с кодом, библиотеками и лучшими практиками.",
                user_prompt="Как бы ты написал функцию для обработки JSON данных из API?"
            )
            
            # IT наставник
            await PromptTemplate.create(
                session,
                name="IT наставник",
                system_prompt="Ты IT наставник, помогающий изучать программирование и компьютерные науки. Ты терпеливо объясняешь сложные концепции, используя понятные примеры и аналогии. Ты подстраиваешься под уровень знаний собеседника и поддерживаешь его стремление учиться.",
                description="Опытный наставник, который поможет освоить программирование и IT концепции.",
                user_prompt="Можешь объяснить, что такое рекурсия в программировании?"
            )
            
            # Юморист
            await PromptTemplate.create(
                session,
                name="Юморист",
                system_prompt="Ты собеседник с отличным чувством юмора. В разговоре ты часто используешь шутки, каламбуры и интересные истории, чтобы сделать общение более веселым и непринужденным. Ты остроумен, но деликатен и никогда не шутишь за счет собеседника.",
                description="Веселый собеседник с хорошим чувством юмора.",
                user_prompt="Расскажи что-нибудь смешное о программистах."
            )
            
            logger.info("Начальные шаблоны промптов созданы.")
            
        # Обновляем информацию о моделях через Ollama API
        try:
            # Создаем экземпляр OllamaService
            from app.services.ollama_service import OllamaService
            ollama_service = OllamaService()
            
            # Получаем список моделей из API
            api_models = await ollama_service.list_models()
            logger.info(f"Получено {len(api_models)} моделей из Ollama API")
            
            # Обрабатываем модели
            for api_model in api_models:
                model_name = api_model.get("name")
                if not model_name:
                    continue
                
                # Проверяем, существует ли модель в БД
                model = await ChatModel.get_by_name(session, model_name)
                
                # Получаем информацию о размере параметров
                details = api_model.get("details", {})
                parameter_size = details.get("parameter_size", "Неизвестно")
                
                # Если модель не существует, создаем ее
                if not model:
                    model = await ChatModel.create(
                        session,
                        name=model_name,
                        display_name=model_name,
                        description=f"Модель {model_name} ({parameter_size})"
                    )
                    
                    # Создаем настройки по умолчанию
                    # Получаем шаблон "Личный ассистент Артём"
                    artem_template = None
                    templates = await PromptTemplate.get_all(session)
                    for template in templates:
                        if template.name == "Личный ассистент Артём":
                            artem_template = template
                            break
                    
                    if artem_template:
                        await ModelSettings.create(
                            session,
                            model_id=model.id,
                            temperature="0.7",
                            top_p="0.9",
                            top_k="40",
                            max_tokens="1024",
                            system_prompt=artem_template.system_prompt
                        )
                    else:
                        await ModelSettings.create(
                            session,
                            model_id=model.id,
                            temperature="0.7",
                            top_p="0.9",
                            top_k="40",
                            max_tokens="1024",
                            system_prompt="Ты полезный помощник по имени Артём. Отвечай на вопросы пользователя дружелюбно и информативно."
                        )
            
            logger.info("Модели успешно обновлены из Ollama API")
        except Exception as e:
            logger.error(f"Ошибка при обновлении моделей: {str(e)}", exc_info=True)
    
    logger.info("Инициализация базы данных завершена") 