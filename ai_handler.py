"""
Модуль для работы с ИИ (DeepSeek API)
Анализ даров и генерация трактовок
"""
import aiohttp
from config import Config
from database import Database
from gifts_knowledge import get_gift_info, get_gifts_by_kun, format_gift_description, format_multiple_gifts

class AIHandler:
    """Класс для работы с ИИ"""
    
    def __init__(self):
        self.api_key = Config.DEEPSEEK_API_KEY
        self.api_url = Config.DEEPSEEK_API_URL
        self.db = Database()
    
    async def get_gift_interpretation(self, gift_data: dict, user_context: str = "") -> str:
        """
        Получение трактовки дара от ИИ на основе базы знаний
        
        Args:
            gift_data: Данные о рассчитанных дарах (содержит gift_code в формате "ма-жи-кун")
            user_context: Дополнительный контекст о пользователе
        
        Returns:
            Трактовка от ИИ
        """
        if not self.api_key:
            return self._get_basic_interpretation(gift_data)
        
        # Формируем запрос к ИИ
        prompt = self._build_prompt(gift_data, user_context)
        
        try:
            # Отправляем запрос к DeepSeek API
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": """Ты эксперт по древнеславянской системе даров рождения Ма-Жи-Кун. Твоя задача - давать глубокие, точные и лаконичные трактовки даров человека на основе расчетов по дате рождения.

ВАЖНО! Твой ответ будет отправлен в Telegram, поэтому используй ТОЛЬКО Telegram-форматирование:

✅ Правильное форматирование для Telegram:
• *жирный текст* (одна звездочка с каждой стороны)
• _курсив_ (одно подчеркивание)
• `код или цитата` (обратные кавычки)
• Используй эмодзи для структуры: 🎁 💫 ✨ 🔮 💡 ⚡ 🌟
• Разделяй разделы пустыми строками для читаемости

❌ НЕ используй:
• ** (двойные звездочки)
• ### или # (заголовки markdown)
• Другие markdown-символы, которые не работают в Telegram

Структура ответа:
1. Краткое приветствие с эмодзи
2. Значение дара с использованием *жирного текста*
3. Сильные стороны (с эмодзи)
4. Рекомендации (с эмодзи)
5. Заключение

Отвечай только на русском языке. Будь глубоким, но лаконичным."""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
                
                async with session.post(
                    f"{self.api_url}/chat/completions",
                    headers=headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content']
                    else:
                        return self._get_basic_interpretation(gift_data)
        
        except Exception as e:
            print(f"Ошибка при обращении к ИИ: {e}")
            return self._get_basic_interpretation(gift_data)
    
    def _build_prompt(self, gift_data: dict, user_context: str) -> str:
        """Построение промпта для ИИ"""
        gift_code = gift_data.get('gift_code', '')
        birth_date = gift_data.get('birth_date', '')
        ma = gift_data.get('ma', 0)
        ji = gift_data.get('ji', 0)
        kun = gift_data.get('kun', 0)
        
        # Получаем информацию о даре из базы знаний
        gift_info = get_gift_info(gift_code)
        
        prompt = f"""Проанализируй дар человека по дате рождения {birth_date}:

🔢 Расчет по системе Ма-Жи-Кун:
• Ма (день+месяц): {ma}
• Жи (год): {ji}  
• Кун (ма+жи): {kun}
• Код дара: {gift_code}

"""
        
        # Если дар найден в базе, добавляем его информацию
        if gift_info:
            prompt += f"""📚 Информация о даре из базы знаний:
• Название: {gift_info.get('name', 'Неизвестно')}
• Описание: {gift_info.get('description', 'Нет описания')}

"""
        else:
            # Если точного дара нет, ищем дары с таким же кун
            kun_gifts = get_gifts_by_kun(kun)
            if kun_gifts:
                prompt += f"📚 Точного дара {gift_code} не найдено, но есть дары с таким же Кун ({kun}):\n\n"
                for kg in kun_gifts[:3]:  # Берем первые 3 дара
                    prompt += f"• {kg.get('name', 'Неизвестно')} ({kg.get('code', '')})\n"
                    prompt += f"  {kg.get('description', '')[:100]}...\n\n"
        
        if user_context:
            prompt += f"Дополнительный контекст: {user_context}\n\n"
        
        prompt += """На основе этой информации дай полную трактовку дара:
1. Значение дара и его энергетика
2. Сильные стороны и таланты
3. Жизненные задачи и предназначение
4. Рекомендации по раскрытию потенциала

Ответ должен быть глубоким, структурированным и практичным."""
        
        return prompt
    
    def _get_basic_interpretation(self, gift_data: dict) -> str:
        """Базовая трактовка без ИИ (резервный вариант) - форматирование для Telegram"""
        birth_date = gift_data.get('birth_date', '')
        gift_code = gift_data.get('gift_code', '')
        ma = gift_data.get('ma', 0)
        ji = gift_data.get('ji', 0)
        kun = gift_data.get('kun', 0)
        
        result = f"🔮 *Анализ дара по дате рождения {birth_date}*\n\n"
        
        # Показываем расчеты
        if 'calculation_details' in gift_data:
            result += "🔢 *Расчет:*\n"
            result += f"• {gift_data['calculation_details']['ma']}\n"
            result += f"• {gift_data['calculation_details']['ji']}\n"
            result += f"• {gift_data['calculation_details']['kun']}\n\n"
        
        result += f"🎁 *Ваш дар: {gift_code}*\n\n"
        
        # Пытаемся найти дар в базе знаний
        gift_info = get_gift_info(gift_code)
        
        if gift_info:
            # Если дар найден - показываем полную информацию (с Telegram форматированием)
            result += self._format_gift_for_telegram(gift_info, gift_code)
        else:
            # Если точного дара нет - показываем дары с таким же кун
            result += f"⚠️ _Точного дара с кодом {gift_code} нет в базе._\n\n"
            kun_gifts = get_gifts_by_kun(kun)
            
            if kun_gifts:
                result += self._format_multiple_gifts_for_telegram(kun_gifts, kun)
            else:
                result += f"❌ Даров с Кун = {kun} не найдено в базе знаний.\n\n"
        
        result += "\n💡 _Для получения полной персональной трактовки с анализом ИИ, настройте API ключ DeepSeek._"
        
        return result
    
    def _format_gift_for_telegram(self, gift_info: dict, gift_code: str) -> str:
        """Форматирование дара для Telegram"""
        result = f"✨ *{gift_info.get('name', 'Без названия')}*\n\n"
        
        if gift_info.get('ma_ji_kun'):
            result += f"🔢 {gift_info['ma_ji_kun']}\n\n"
        
        if gift_info.get('description'):
            result += f"📖 {gift_info['description']}\n\n"
        
        if gift_info.get('image_url'):
            result += f"🖼 [Изображение дара]({gift_info['image_url']})\n\n"
        
        if gift_info.get('getgems_url'):
            result += f"💎 [NFT коллекция]({gift_info['getgems_url']})\n"
        
        return result
    
    def _format_multiple_gifts_for_telegram(self, kun_gifts: list, kun: int) -> str:
        """Форматирование нескольких даров для Telegram"""
        result = f"🔍 *Найдено {len(kun_gifts)} даров с Кун = {kun}:*\n\n"
        
        for i, gift in enumerate(kun_gifts[:3], 1):  # Показываем первые 3
            result += f"{i}. ✨ *{gift.get('name', 'Без названия')}*\n"
            result += f"   _Код: {gift.get('code', '')}_\n"
            
            desc = gift.get('description', '')
            if len(desc) > 120:
                desc = desc[:120] + "..."
            result += f"   {desc}\n\n"
        
        if len(kun_gifts) > 3:
            result += f"_И ещё {len(kun_gifts) - 3} даров..._\n\n"
        
        return result

