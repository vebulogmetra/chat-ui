import logging
import asyncio
from app.services.ollama_service import OllamaService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

async def test_ollama_connection():
    """Тестирование соединения с Ollama API"""
    
    service = OllamaService()
    print('Тестирование запроса к Ollama API...')
    
    try:
        models = await service.list_models()
        print(f'Результат запроса к API: {models}')
        
        if models:
            print(f"\nНайдено {len(models)} моделей:")
            for model in models:
                print(f"- {model.get('name')}: {model.get('parameter_size') or 'неизвестно'}")
        else:
            print("\nНе удалось получить список моделей или список пуст.")
    except Exception as e:
        print(f"Ошибка при тестировании: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_ollama_connection()) 