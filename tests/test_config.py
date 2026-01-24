"""
Тестирование конфигурации бота
Запустите этот скрипт для проверки правильности настройки переменных окружения
"""
import os
from dotenv import load_dotenv

# Загружаем переменные из .env (если файл существует)
load_dotenv()

print("=" * 60)
print("ПРОВЕРКА КОНФИГУРАЦИИ БОТА")
print("=" * 60)
print()

# Проверка BOT_TOKEN
bot_token = os.getenv('BOT_TOKEN')
if bot_token:
    print(f"✅ BOT_TOKEN: Установлен (длина: {len(bot_token)} символов)")
    if len(bot_token) < 40:
        print("   ⚠️  ВНИМАНИЕ: Токен слишком короткий, возможно неправильный")
else:
    print("❌ BOT_TOKEN: НЕ УСТАНОВЛЕН!")
    print("   Получите токен у @BotFather в Telegram")

print()

# Проверка DEEPSEEK_API_KEY
deepseek_key = os.getenv('DEEPSEEK_API_KEY')
if deepseek_key:
    print(f"✅ DEEPSEEK_API_KEY: Установлен (длина: {len(deepseek_key)} символов)")
    if len(deepseek_key) < 20:
        print("   ⚠️  ВНИМАНИЕ: Ключ слишком короткий, возможно неправильный")
else:
    print("❌ DEEPSEEK_API_KEY: НЕ УСТАНОВЛЕН!")
    print("   Бот будет работать без ИИ (только базовые интерпретации)")
    print("   Получите ключ: https://platform.deepseek.com")

print()

# Проверка ADMIN_IDS
admin_ids_str = os.getenv('ADMIN_IDS', '')
if admin_ids_str:
    try:
        # Проверяем, есть ли пробелы (частая ошибка)
        if ' ' in admin_ids_str:
            print("⚠️  ADMIN_IDS: Установлен, но содержит ПРОБЕЛЫ!")
            print(f"   Текущее значение: '{admin_ids_str}'")
            print("   Удалите все пробелы: 123456789,987654321")
        
        # Пытаемся распарсить
        admin_ids = [int(x.strip()) for x in admin_ids_str.split(',') if x.strip()]
        if admin_ids:
            print(f"✅ ADMIN_IDS: Установлен ({len(admin_ids)} админов)")
            for admin_id in admin_ids:
                print(f"   - {admin_id}")
        else:
            print("⚠️  ADMIN_IDS: Установлен, но пустой")
    except ValueError as e:
        print(f"❌ ADMIN_IDS: Ошибка парсинга - {e}")
        print(f"   Текущее значение: '{admin_ids_str}'")
        print("   Формат: 123456789,987654321 (только цифры и запятые)")
else:
    print("⚠️  ADMIN_IDS: НЕ УСТАНОВЛЕН")
    print("   Узнайте свой ID: @userinfobot в Telegram")
    print("   Формат: 123456789,987654321")

print()

# Проверка DEEPSEEK_API_URL
api_url = os.getenv('DEEPSEEK_API_URL', 'https://api.deepseek.com/v1')
print(f"✅ DEEPSEEK_API_URL: {api_url}")

print()

# Проверка DATABASE_PATH
db_path = os.getenv('DATABASE_PATH', 'data/bot_database.db')
print(f"✅ DATABASE_PATH: {db_path}")

# Проверяем существование директории для базы данных
import pathlib
db_dir = pathlib.Path(db_path).parent
if db_dir.exists():
    print(f"   ✅ Директория существует: {db_dir}")
else:
    print(f"   ⚠️  Директория НЕ существует: {db_dir}")
    print(f"   Она будет создана автоматически при запуске бота")

print()
print("=" * 60)
print("ИТОГИ ПРОВЕРКИ")
print("=" * 60)

errors = []
warnings = []

if not bot_token:
    errors.append("BOT_TOKEN не установлен")
elif len(bot_token) < 40:
    warnings.append("BOT_TOKEN может быть неправильным (слишком короткий)")

if not deepseek_key:
    warnings.append("DEEPSEEK_API_KEY не установлен - ИИ функции недоступны")
elif len(deepseek_key) < 20:
    warnings.append("DEEPSEEK_API_KEY может быть неправильным (слишком короткий)")

if not admin_ids_str:
    warnings.append("ADMIN_IDS не установлен - некому управлять ботом")
elif ' ' in admin_ids_str:
    errors.append("ADMIN_IDS содержит пробелы")

if errors:
    print()
    print("❌ КРИТИЧЕСКИЕ ОШИБКИ:")
    for error in errors:
        print(f"   • {error}")
    print()
    print("Исправьте ошибки перед запуском бота!")

if warnings:
    print()
    print("⚠️  ПРЕДУПРЕЖДЕНИЯ:")
    for warning in warnings:
        print(f"   • {warning}")

if not errors and not warnings:
    print()
    print("✅ Все переменные настроены правильно!")
    print("Бот готов к запуску!")

print()
print("=" * 60)
print("Для запуска бота выполните: python -m src.bot")
print("=" * 60)

