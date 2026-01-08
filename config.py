"""
Конфигурация бота - безопасная загрузка настроек из переменных окружения
"""
import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла (только для локальной разработки)
# На Railway переменные уже будут в окружении
load_dotenv()

class Config:
    """Класс для хранения конфигурации приложения"""
    
    # Telegram Bot
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN не найден в переменных окружения!")
    
    # Админы (ID пользователей через запятую)
    # ВАЖНО: На Railway нужно установить эту переменную в настройках проекта
    # Формат: 123456789,987654321 (БЕЗ пробелов!)
    admin_ids_str = os.getenv('ADMIN_IDS', '').strip()
    ADMIN_IDS = []
    
    print(f"🔍 DEBUG: ADMIN_IDS raw value: '{admin_ids_str}'")
    print(f"🔍 DEBUG: ADMIN_IDS length: {len(admin_ids_str)}")
    
    if admin_ids_str:
        try:
            # Удаляем все пробелы и разбиваем по запятым
            parts = [x.strip() for x in admin_ids_str.replace(' ', '').split(',') if x.strip()]
            print(f"🔍 DEBUG: После разбиения: {parts}")
            
            ADMIN_IDS = [int(x) for x in parts if x]
            print(f"✅ Загружены админы: {ADMIN_IDS}")
            
            if not ADMIN_IDS:
                print("⚠️ ADMIN_IDS задан, но пустой после парсинга!")
        except ValueError as e:
            print(f"❌ Ошибка при парсинге ADMIN_IDS: {e}")
            print(f"❌ Проблемное значение: '{admin_ids_str}'")
            ADMIN_IDS = []
    else:
        print("⚠️ ADMIN_IDS не установлен в переменных окружения!")
        print("ℹ️  Установите ADMIN_IDS в формате: 123456789,987654321")
    
    # DeepSeek AI API
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    if not DEEPSEEK_API_KEY:
        print("⚠️ DEEPSEEK_API_KEY не установлен! ИИ функции будут недоступны.")
    else:
        print("✅ DEEPSEEK_API_KEY загружен")
    
    DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
    
    # Database
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/bot_database.db')
    
    # Подписки (цены в Telegram Stars)
    TRIAL_DURATION_DAYS = 7
    TRIAL_AI_LIMIT = 5  # Лимит запросов к ИИ для trial периода
    
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

