"""
Модуль для работы с алфавитом и анализа слов
"""
from database import Database
from ai_handler import AIHandler
from gifts_knowledge import get_gift_info
import json

class AlphabetAnalyzer:
    """Класс для анализа слов через значения букв алфавита"""
    
    def __init__(self, db: Database, ai_handler: AIHandler):
        self.db = db
        self.ai = ai_handler
    
    async def analyze_word(self, word: str, user_id: int = None) -> dict:
        """
        Анализирует слово по буквам и возвращает его значение
        
        Args:
            word: Слово для анализа
            user_id: ID пользователя для истории
            
        Returns:
            dict с результатами анализа
        """
        word = word.strip().upper()
        
        # Проверяем, не является ли это даром
        gift_info = None
        if word.isdigit():
            gift_num = int(word)
            if 1 <= gift_num <= 144:
                gift_info = get_gift_info(gift_num)
        
        # Получаем значения букв
        letter_meanings = []
        for letter in word:
            if letter.isalpha():
                meaning = await self.db.get_letter_meaning(letter)
                if meaning:
                    letter_meanings.append({
                        "letter": letter,
                        "name": meaning['name'] or "",
                        "description": meaning['description'] or ""
                    })
        
        # Формируем текст для анализа ИИ
        analysis_text = self._format_analysis_text(word, letter_meanings, gift_info)
        
        # Получаем анализ от ИИ
        prompt = f"""Проанализируй предоставленное слово, используя интерпретации его букв из базы данных алфавита.

{analysis_text}

Сформируй ответ строго по структуре:

*НАЗВАНИЕ СЛОВА:* [1-3 слова, передающие его суть]

*КРАТКОЕ ЗНАЧЕНИЕ:* [ключевая характеристика или действие]

*ГЛУБИННЫЙ СМЫСЛ:*
[Связное описание целостного образа, процесса или состояния, рождаемого сочетанием букв]

*РАЗБОР ПО БУКВАМ:*

Для каждой буквы приведи:

*[Буква]:*
• Интерпретация: [интерпретация базового значения из БД]
• Роль в слове: [как она конкретно влияет на общий смысл и настроение слова]

*ПРАКТИКА ОСМЫСЛЕНИЯ:*
[Простое действие или вопрос для внутреннего прожития смысла этого слова - не медитация, а акт осознания или наблюдения]

Будь лаконичным. Интерпретация должна вытекать из сочетания значений букв, а не быть общей."""

        ai_response = await self.ai.get_response(prompt, user_id)
        
        return {
            "word": word,
            "letter_meanings": letter_meanings,
            "gift_info": gift_info,
            "ai_analysis": ai_response,
            "raw_text": analysis_text
        }
    
    def _format_analysis_text(self, word: str, letter_meanings: list, gift_info: dict = None) -> str:
        """Форматирует текст для анализа"""
        text = f"СЛОВО/ФРАЗА: {word}\n\n"
        
        if gift_info:
            text += f"🎁 ЭТО ДАР #{gift_info['number']}: {gift_info['name']}\n"
            text += f"Описание дара: {gift_info['description']}\n\n"
        
        text += "РАЗБОР ПО БУКВАМ:\n"
        for lm in letter_meanings:
            text += f"\n{lm['letter']}"
            if lm['name']:
                text += f" - {lm['name']}"
            if lm['description']:
                text += f"\n  Значение: {lm['description']}"
        
        return text
    
    async def format_result_for_user(self, analysis: dict) -> str:
        """Форматирует результат анализа для отправки пользователю"""
        result = f"🔮 <b>АНАЛИЗ СЛОВА: {analysis['word']}</b>\n\n"
        
        # Анализ от ИИ (без разбора по буквам - он уже в промпте для ИИ)
        result += analysis['ai_analysis']
        
        return result
    
    async def analyze_phrase(self, phrase: str, user_id: int = None) -> dict:
        """
        Анализирует фразу из нескольких слов
        """
        words = phrase.strip().split()
        
        if len(words) == 1:
            return await self.analyze_word(words[0], user_id)
        
        # Анализируем каждое слово
        word_analyses = []
        for word in words:
            if word.strip():
                analysis = await self.analyze_word(word, user_id)
                word_analyses.append(analysis)
        
        # Собираем общий текст для финального анализа
        combined_text = f"ФРАЗА: {phrase}\n\n"
        combined_text += "ЗНАЧЕНИЯ ОТДЕЛЬНЫХ СЛОВ:\n\n"
        
        for wa in word_analyses:
            combined_text += f"Слово: {wa['word']}\n"
            combined_text += wa['raw_text'] + "\n"
            combined_text += f"Анализ: {wa['ai_analysis']}\n\n"
        
        # Получаем общий анализ фразы
        prompt = f"""Проанализируй фразу как единое целое на основе значений отдельных слов:

{combined_text}

Предоставь:
1. КРАТКОЕ ЗНАЧЕНИЕ ФРАЗЫ (1-3 слова)
2. ОБЩЕЕ ОПИСАНИЕ: что несет в себе вся фраза как единое целое, её энергия и смысл
3. КАК СЛОВА ВЗАИМОДЕЙСТВУЮТ: как значения слов дополняют друг друга"""

        final_analysis = await self.ai.get_response(prompt, user_id)
        
        return {
            "phrase": phrase,
            "words": word_analyses,
            "final_analysis": final_analysis
        }
    
    async def format_phrase_result(self, analysis: dict) -> str:
        """Форматирует результат анализа фразы"""
        result = f"🔮 <b>АНАЛИЗ ФРАЗЫ: {analysis['phrase']}</b>\n\n"
        
        result += "📖 <b>Анализ отдельных слов:</b>\n\n"
        
        for wa in analysis['words']:
            result += f"<b>{wa['word']}</b>\n"
            # Краткая выдержка из анализа каждого слова
            ai_text = wa['ai_analysis']
            if len(ai_text) > 200:
                ai_text = ai_text[:200] + "..."
            result += f"<i>{ai_text}</i>\n\n"
        
        result += "✨ <b>ОБЩЕЕ ЗНАЧЕНИЕ ФРАЗЫ:</b>\n\n"
        result += analysis['final_analysis']
        
        return result


def check_if_gift_or_command(text: str) -> dict:
    """
    Проверяет, является ли текст даром или командой
    
    Returns:
        dict: {"type": "gift/command/word", "value": ...}
    """
    text = text.strip()
    
    # Проверка на число (дар)
    if text.isdigit():
        num = int(text)
        if 1 <= num <= 144:
            gift_info = get_gift_info(num)
            if gift_info:
                return {"type": "gift", "value": num, "info": gift_info}
    
    # Проверка на команды сантр (список основных команд)
    mantra_commands = ["ши", "ду", "си", "ци", "чи", "ра", "та", "то", "ма", "на"]
    text_lower = text.lower()
    for cmd in mantra_commands:
        if text_lower.startswith(cmd):
            return {"type": "command", "value": cmd}
    
    return {"type": "word", "value": text}

