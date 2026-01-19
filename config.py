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
    # Формат: 123456789,987654321 (БЕЗ пробелов, но парсер удалит их автоматически)
    admin_ids_str = os.getenv('ADMIN_IDS', '').strip()
    ADMIN_IDS = []
    
    if admin_ids_str:
        try:
            # Удаляем все пробелы и разбиваем по запятым
            parts = [x.strip() for x in admin_ids_str.replace(' ', '').split(',') if x.strip()]
            ADMIN_IDS = [int(x) for x in parts if x]
            print(f"✅ Загружены админы: {ADMIN_IDS}")
        except ValueError as e:
            print(f"⚠️ Ошибка при парсинге ADMIN_IDS: {e}")
            ADMIN_IDS = []
    else:
        print("⚠️ ADMIN_IDS не установлен в переменных окружения!")
    
    # DeepSeek AI API
    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    if not DEEPSEEK_API_KEY:
        print("⚠️ DEEPSEEK_API_KEY не установлен! ИИ функции будут недоступны.")
    else:
        print("✅ DEEPSEEK_API_KEY загружен")
    
    DEEPSEEK_API_URL = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
    
    # Database
    # Поддержка Vercel Postgres (Neon) для продакшена
    # и SQLite для локальной разработки
    DATABASE_URL = os.getenv('POSTGRES_PRISMA_URL') or os.getenv('POSTGRES_URL') or os.getenv('DATABASE_URL', '')
    
    # Если установлен DATABASE_URL, используем PostgreSQL (Vercel Postgres)
    # Иначе используем SQLite
    USE_POSTGRESQL = bool(DATABASE_URL)
    
    if USE_POSTGRESQL:
        print("🐘 Используется PostgreSQL (Vercel Postgres / Neon)")
    else:
        # SQLite для локальной разработки
        default_db_path = 'data/bot_database.db'
        if os.getenv('VERCEL') or os.getenv('VERCEL_ENV'):
            # На Vercel без PostgreSQL БД не будет работать!
            print("⚠️ ВНИМАНИЕ: На Vercel SQLite не работает! Установите Vercel Postgres и настройте DATABASE_URL")
            default_db_path = '/tmp/bot_database.db'
        DATABASE_PATH = os.getenv('DATABASE_PATH', default_db_path)
        print(f"💾 Используется SQLite: {DATABASE_PATH}")
    
    # Подписки (цены в Telegram Stars)
    TRIAL_DURATION_DAYS = 7
    TRIAL_AI_LIMIT = 5  # Лимит запросов к ИИ для trial периода
    
    # Цены подписок в звездах
    PREMIUM_TEST_PRICE = 15      # Тестовая подписка на 1 день (для тестирования)
    
    # PRO подписка (базовый уровень)
    PRO_MONTH_PRICE = 249   # PRO подписка на месяц
    PRO_YEAR_PRICE = 2499   # PRO подписка на год
    
    # ORDEN подписка (полный доступ)
    ORDEN_MONTH_PRICE = 499   # ORDEN подписка на месяц
    ORDEN_YEAR_PRICE = 4999   # ORDEN подписка на год
    
    # Длительность подписок в днях
    PREMIUM_TEST_DAYS = 1       # Тестовая подписка
    PRO_MONTH_DAYS = 30
    PRO_YEAR_DAYS = 365
    ORDEN_MONTH_DAYS = 30
    ORDEN_YEAR_DAYS = 365
    
    # Уровни доступа подписок
    SUBSCRIPTION_LEVELS = {
        'trial': 'trial',           # Trial - базовый доступ
        'premium_test': 'trial',     # Тестовая - базовый доступ
        'pro_month': 'pro',          # PRO месяц - без алхимии, сантр, анализа слов
        'pro_year': 'pro',           # PRO год - без алхимии, сантр, анализа слов
        'orden_month': 'orden',      # ORDEN месяц - полный доступ
        'orden_year': 'orden'        # ORDEN год - полный доступ
    }
    
    @classmethod
    def validate(cls):
        """Проверка наличия всех необходимых настроек"""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN обязателен для запуска бота!")
        return True

# Валидация конфигурации при импорте
Config.validate()

