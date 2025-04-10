from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import get_db, init_db, async_session
from app.database.seed_data import seed_default_prompts
from app.models.models import ChatModel
from app.routes import chat_routes, model_routes

app = FastAPI(title="LLM Chat UI")

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

app.include_router(chat_routes.router)
app.include_router(model_routes.router)


@app.on_event("startup")
async def startup_event():
    # Инициализация базы данных
    await init_db()
    # Добавление начальных данных
    async with async_session() as session:
        await seed_default_prompts(session)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: AsyncSession = Depends(get_db)):
    models = await ChatModel.get_all(db)
    return templates.TemplateResponse(
        "index.html", {"request": request, "models": models}
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 