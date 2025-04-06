import aiohttp
import os
import json
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator

# Настраиваем логгер
logger = logging.getLogger(__name__)

class OllamaService:
    """
    Сервис для взаимодействия с API Ollama.
    """
    
    def __init__(self):
        # Получаем базовый URL из переменных окружения или используем значение по умолчанию
        self.base_url = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api")
        logger.info(f"Инициализация OllamaService с base_url: {self.base_url}")
        
    async def list_models(self):
        """
        Получает список доступных моделей из API Ollama.
        """
        url = f"{self.base_url}/tags"
        logger.info(f"Запрос списка моделей: GET {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                logger.info(f"Отправка запроса на получение моделей...")
                async with session.get(url) as response:
                    logger.info(f"Получен ответ от API Ollama, статус: {response.status}")
                    if response.status == 200:
                        text_response = await response.text()
                        logger.info(f"Текст ответа: {text_response[:200]}...")
                        
                        data = await response.json()
                        models = data.get("models", [])
                        logger.info(f"Получено {len(models)} моделей")
                        
                        # Логируем каждую полученную модель
                        for i, model in enumerate(models):
                            logger.info(f"Модель {i+1}: {model.get('name')}")
                        
                        return models
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка при получении моделей: {response.status}, {error_text}")
                        return []
        except Exception as e:
            logger.error(f"Исключение при получении моделей: {str(e)}", exc_info=True)
            return []
    
    async def generate_completion(self, model: str, prompt: str, system_prompt: str = None, 
                                 temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """
        Генерирует завершение промпта с помощью указанной модели.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
            }
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
            
        if system_prompt:
            payload["system"] = system_prompt
        
        url = f"{self.base_url}/generate"
        logger.info(f"Генерация ответа: POST {url}, модель: {model}")
        logger.info(f"Payload: {payload}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        logger.info(f"Content-Type ответа: {content_type}")
                        
                        if 'application/x-ndjson' in content_type:
                            # Обработка потокового ответа
                            full_response = ""
                            async for line in response.content:
                                if line:
                                    try:
                                        data = json.loads(line)
                                        if not data.get("done", False):
                                            chunk = data.get("response", "")
                                            full_response += chunk
                                    except Exception as e:
                                        logger.error(f"Ошибка при обработке строки NDJSON: {str(e)}")
                            return full_response
                        else:
                            # Обычный JSON ответ
                            data = await response.json()
                            return data.get("response", "")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка при генерации ответа: {response.status}, {error_text}")
                        return f"Ошибка: {response.status}, {error_text}"
        except Exception as e:
            logger.error(f"Исключение при генерации ответа: {str(e)}")
            return f"Ошибка: {str(e)}"
    
    async def generate_stream(self, model: str, prompt: str, system_prompt: str = None, 
                            temperature: float = 0.7, max_tokens: int = 1024) -> AsyncGenerator[str, None]:
        """
        Потоково генерирует завершение промпта с помощью указанной модели.
        """
        payload = {
            "model": model,
            "prompt": prompt,
            "options": {
                "temperature": temperature,
            },
            "stream": True
        }
        
        if max_tokens:
            payload["options"]["num_predict"] = max_tokens
            
        if system_prompt:
            payload["system"] = system_prompt
        
        url = f"{self.base_url}/generate"
        logger.info(f"Потоковая генерация: POST {url}, модель: {model}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                try:
                                    data = json.loads(line)
                                    if not data.get("done"):
                                        yield data.get("response", "")
                                except Exception as e:
                                    logger.error(f"Ошибка при обработке потокового ответа: {str(e)}")
                                    print(f"Ошибка при обработке ответа: {e}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка при потоковой генерации: {response.status}, {error_text}")
                        yield f"Ошибка: {response.status}, {error_text}"
        except Exception as e:
            logger.error(f"Исключение при потоковой генерации: {str(e)}")
            yield f"Ошибка: {str(e)}"
    
    async def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о модели"""
        url = f"{self.base_url}/show?name={model_name}"
        logger.info(f"Запрос информации о модели: GET {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка при получении информации о модели: {response.status}, {error_text}")
                        return None
        except Exception as e:
            logger.error(f"Исключение при получении информации о модели: {str(e)}")
            return None 