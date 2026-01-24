"""
Интерактивный скрипт для настройки подключения к Supabase
"""
import os
import sys
from dotenv import load_dotenv

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def print_step(step_num, title):
    """Выводит заголовок шага"""
    print(f"\n{'='*60}")
    print(f"ШАГ {step_num}: {title}")
    print('='*60)

def check_existing_config():
    """Проверяет текущую конфигурацию"""
    print("\n📋 ПРОВЕРКА ТЕКУЩЕЙ КОНФИГУРАЦИИ")
    print("-" * 60)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_api_key = os.getenv('SUPABASE_API_KEY') or os.getenv('SUPABASE_ANON_KEY')
    supabase_db_url = os.getenv('SUPABASE_DB_URL')
    database_url = os.getenv('DATABASE_URL')
    
    print(f"SUPABASE_URL: {'✅ Установлен' if supabase_url else '❌ Не установлен'}")
    if supabase_url:
        print(f"   Значение: {supabase_url}")
    
    print(f"SUPABASE_API_KEY: {'✅ Установлен' if supabase_api_key else '❌ Не установлен'}")
    if supabase_api_key:
        print(f"   Тип: {'service_role' if 'service_role' in str(supabase_api_key) else 'anon'} (первые 20 символов)")
    
    print(f"SUPABASE_DB_URL: {'✅ Установлен' if supabase_db_url else '❌ Не установлен'}")
    if supabase_db_url:
        # Маскируем пароль в URL
        masked = supabase_db_url.split('@')[0].split(':')
        if len(masked) >= 2:
            masked_url = f"{masked[0]}:***@{supabase_db_url.split('@')[1] if '@' in supabase_db_url else ''}"
            print(f"   Значение: {masked_url}")
    
    print(f"DATABASE_URL: {'✅ Установлен' if database_url else '❌ Не установлен'}")
    if database_url:
        masked = database_url.split('@')[0].split(':')
        if len(masked) >= 2:
            masked_url = f"{masked[0]}:***@{database_url.split('@')[1] if '@' in database_url else ''}"
            print(f"   Значение: {masked_url}")
    
    return {
        'supabase_url': supabase_url,
        'supabase_api_key': supabase_api_key,
        'supabase_db_url': supabase_db_url,
        'database_url': database_url
    }

def print_instructions():
    """Выводит инструкции по настройке"""
    print_step(1, "Получение строки подключения PostgreSQL")
    
    print("""
Для применения миграции через скрипт нужно настроить SUPABASE_DB_URL.

1. Откройте Supabase Dashboard:
   https://app.supabase.com/

2. Выберите ваш проект

3. Перейдите в Settings → Database

4. Найдите раздел "Connection string"

5. Выберите один из вариантов:

   📌 Вариант A: Direct connection (для миграций)
      - Выберите "Direct connection"
      - Скопируйте "URI"
      - Формат: postgresql://postgres:[PASSWORD]@db.xxx.supabase.co:5432/postgres
   
   📌 Вариант B: Connection pooling (для продакшена)
      - Выберите "Connection pooling" → "Session mode"
      - Скопируйте "URI"
      - Формат: postgresql://postgres.xxx:[PASSWORD]@aws-0-xxx.pooler.supabase.com:6543/postgres?pgbouncer=true

6. Если пароль не указан:
   - Нажмите "Reset database password"
   - Скопируйте новый пароль
   - Вставьте его в строку подключения вместо [PASSWORD]

⚠️  ВАЖНО: Не забудьте заменить [PASSWORD] на реальный пароль!
    """)

def generate_env_example(config):
    """Генерирует пример .env файла"""
    print_step(2, "Пример содержимого .env файла")
    
    print("\n📝 Добавьте следующие строки в ваш .env файл:\n")
    print("# Supabase настройки")
    
    if config['supabase_url']:
        print(f"SUPABASE_URL={config['supabase_url']}")
    else:
        print("SUPABASE_URL=https://ouodquakgyyeiyihmoxg.supabase.co")
    
    if config['supabase_api_key']:
        print(f"SUPABASE_API_KEY={config['supabase_api_key'][:20]}...")
    else:
        print("# SUPABASE_API_KEY=ваш_service_role_ключ_здесь")
    
    print("\n# Для применения миграций через скрипт:")
    print("# SUPABASE_DB_URL=postgresql://postgres:ВАШ_ПАРОЛЬ@db.xxx.supabase.co:5432/postgres")
    print("\n# Или можно использовать общую переменную:")
    print("# DATABASE_URL=postgresql://postgres:ВАШ_ПАРОЛЬ@db.xxx.supabase.co:5432/postgres")
    
    print("\n💡 Примечания:")
    print("   - Замените ВАШ_ПАРОЛЬ на реальный пароль из Supabase Dashboard")
    print("   - Замените xxx на ID вашего проекта")
    print("   - .env файл не должен коммититься в git!")

def check_migration_readiness():
    """Проверяет готовность к применению миграции"""
    print_step(3, "Проверка готовности к миграции")
    
    supabase_db_url = os.getenv('SUPABASE_DB_URL')
    database_url = os.getenv('DATABASE_URL')
    
    if supabase_db_url or database_url:
        print("\n✅ SUPABASE_DB_URL или DATABASE_URL установлен!")
        print("   Можно применить миграцию через: python scripts/apply_migration.py")
        return True
    else:
        print("\n❌ SUPABASE_DB_URL не установлен")
        print("\n💡 Два способа применения миграции:")
        print("\n   1️⃣  Через Supabase Dashboard (рекомендуется, если нет SUPABASE_DB_URL):")
        print("       • Откройте Supabase Dashboard → SQL Editor")
        print("       • Скопируйте SQL из migrations/001_create_tables.sql")
        print("       • Вставьте и выполните")
        print("\n   2️⃣  Через скрипт (требует SUPABASE_DB_URL):")
        print("       • Настройте SUPABASE_DB_URL в .env")
        print("       • Запустите: python scripts/apply_migration.py")
        return False

def main():
    """Главная функция"""
    print("="*60)
    print("НАСТРОЙКА ПОДКЛЮЧЕНИЯ К SUPABASE")
    print("="*60)
    
    # Проверяем текущую конфигурацию
    config = check_existing_config()
    
    # Выводим инструкции
    print_instructions()
    
    # Генерируем пример .env
    generate_env_example(config)
    
    # Проверяем готовность к миграции
    ready = check_migration_readiness()
    
    if not ready:
        print("\n" + "="*60)
        print("📌 СЛЕДУЮЩИЕ ШАГИ:")
        print("="*60)
        print("""
1. Откройте Supabase Dashboard → Settings → Database
2. Получите строку подключения (Connection string)
3. Добавьте SUPABASE_DB_URL в .env файл
4. Запустите: python scripts/apply_migration.py

ИЛИ

1. Откройте Supabase Dashboard → SQL Editor
2. Скопируйте SQL из migrations/001_create_tables.sql
3. Вставьте и выполните SQL
        """)
    else:
        print("\n" + "="*60)
        print("✅ ВСЁ ГОТОВО!")
        print("="*60)
        print("\nТеперь можно применить миграцию:")
        print("   python scripts/apply_migration.py")
    
    print("\n" + "="*60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
