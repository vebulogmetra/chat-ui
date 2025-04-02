import aiohttp
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator

OLLAMA_HOST = "http://localhost:11434"

class OllamaService:
    @staticmethod
    async def list_models():
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_HOST}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("models", [])
                else:
                    return []
    
    @staticmethod
    async def generate_completion(
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = True
    ) -> AsyncGenerator[str, None]:
        """
        Генерирует ответ от модели с использованием API Ollama.
        
        Args:
            model: Название модели
            messages: Список сообщений в формате [{role: "user", content: "..."}]
            temperature: Температура генерации (0.0 - 1.0)
            max_tokens: Максимальное количество токенов
            stream: Использовать ли потоковую передачу
            
        Yields:
            Фрагменты текста ответа при потоковой передаче
        """
        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            },
            "stream": stream
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{OLLAMA_HOST}/api/chat", json=payload) as response:
                if stream:
                    buffer = ""
                    async for line in response.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    chunk = data["message"]["content"]
                                    buffer += chunk
                                    yield chunk
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                continue
                else:
                    if response.status == 200:
                        data = await response.json()
                        if "message" in data and "content" in data["message"]:
                            yield data["message"]["content"]
    
    @staticmethod
    async def get_model_info(model_name: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о модели"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{OLLAMA_HOST}/api/show?name={model_name}") as response:
                if response.status == 200:
                    return await response.json()
                return None 