"""
Конфигурация бота - безопасная загрузка настроек из переменных окружения
"""
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

class Config:
    """Класс для хранения конфигурации приложения"""
    
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в .env файле!")
    
    # DeepSeek AI API
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/bot_database.db')
    
    # Подписки (цены в Telegram Stars)
    TRIAL_DURATION_DAYS = 7
    
    # Цены подписок в звездах
    PREMIUM_TEST_PRICE = 15      # Тестовая подписка на 1 день (для тестирования)
    PREMIUM_MONTH_PRICE = 249   # Подписка на месяц
    PREMIUM_YEAR_PRICE = 2499   # Подписка на год
    
    # Длительность подписок в днях
    PREMIUM_TEST_DAYS = 1       # Тестовая подписка
    PREMIUM_MONTH_DAYS = 30
    PREMIUM_YEAR_DAYS = 365
    
    @classmethod
    def validate(cls):
        """Проверка наличия всех необходимых настроек"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN обязателен для запуска бота!")
        return True

# Валидация конфигурации при импорте
Config.validate()

