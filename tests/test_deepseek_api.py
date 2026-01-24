"""
Тест подключения к DeepSeek API
"""
import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

async def test_deepseek():
    api_key = os.getenv('DEEPSEEK_API_KEY')
    api_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
    
    print("=" * 50)
    print("ТЕСТ DEEPSEEK API")
    print("=" * 50)
    print(f"API URL: {api_url}")
    print(f"API Key: {api_key[:20]}..." if api_key else "API Key: НЕ НАСТРОЕН")
    print()
    
    if not api_key:
        print("❌ DEEPSEEK_API_KEY не настроен!")
        return False
    
    try:
        print("🔄 Отправляю тестовый запрос к DeepSeek API...")
        
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "Ты помощник."
                    },
                    {
                        "role": "user",
                        "content": "Скажи 'Привет, я работаю!'"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 100
            }
            
            async with session.post(
                f"{api_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                print(f"📊 Статус ответа: {response.status}")
                
                if response.status == 200:
                    result = await response.json()
                    answer = result['choices'][0]['message']['content']
                    print(f"✅ API работает!")
                    print(f"📝 Ответ от ИИ: {answer}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Ошибка API: {response.status}")
                    print(f"📄 Текст ошибки: {error_text}")
                    return False
    
    except aiohttp.ClientError as e:
        print(f"❌ Ошибка соединения: {e}")
        return False
    except asyncio.TimeoutError:
        print(f"❌ Превышено время ожидания (timeout)")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_deepseek())
    
    print()
    print("=" * 50)
    if result:
        print("✅ DEEPSEEK API РАБОТАЕТ!")
    else:
        print("❌ DEEPSEEK API НЕ РАБОТАЕТ!")
    print("=" * 50)

