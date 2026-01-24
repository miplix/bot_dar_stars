"""
Улучшенный скрипт для применения миграции к Supabase
Пробует разные варианты подключения и форматы URL
"""
import os
import sys
import asyncio
import asyncpg
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse, quote_plus

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

async def try_connect_with_url(conn_url, description):
    """Пробует подключиться с указанным URL"""
    try:
        print(f"\n🔗 Попытка подключения: {description}")
        print(f"   URL: {conn_url[:50]}...")
        
        conn = await asyncio.wait_for(
            asyncpg.connect(conn_url),
            timeout=10.0
        )
        print("✅ Подключение установлено!")
        return conn
    except asyncio.TimeoutError:
        print("❌ Таймаут подключения")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {str(e)[:100]}")
        return None

async def apply_migration():
    """Применяет миграцию к базе данных"""
    print("🚀 Применение миграции к Supabase/PostgreSQL")
    print("=" * 60)
    
    # Получаем настройки
    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    database_url = (
        os.getenv('SUPABASE_DB_URL') or
        os.getenv('POSTGRES_PRISMA_URL') or 
        os.getenv('POSTGRES_URL') or 
        os.getenv('DATABASE_URL')
    )
    
    if not database_url:
        print("❌ SUPABASE_DB_URL не установлен!")
        return
    
    # Читаем SQL миграцию
    migration_file = 'migrations/001_create_tables.sql'
    if not os.path.exists(migration_file):
        print(f"❌ Файл миграции {migration_file} не найден!")
        return
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Пробуем разные варианты URL
    urls_to_try = []
    
    # 1. Исходный URL
    urls_to_try.append((database_url, "Исходный URL"))
    
    # 2. URL с правильно закодированным паролем
    try:
        parsed = urlparse(database_url)
        if '@' in parsed.netloc and ':' in parsed.netloc.split('@')[0]:
            auth_part = parsed.netloc.split('@')[0]
            username, password = auth_part.split(':', 1)
            
            if '%' not in password:
                encoded_password = quote_plus(password, safe='')
                new_netloc = f"{username}:{encoded_password}@{parsed.netloc.split('@')[1]}"
                encoded_url = urlunparse((
                    parsed.scheme,
                    new_netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
                urls_to_try.append((encoded_url, "URL с закодированным паролем"))
    except Exception:
        pass
    
    # 3. Pooler URL (если используется direct connection)
    try:
        parsed = urlparse(database_url)
        if 'pooler.supabase.com' not in parsed.hostname and 'db.' in parsed.hostname:
            # Пробуем использовать pooler
            pooler_host = parsed.hostname.replace('db.', 'pooler.')
            pooler_netloc = f"{parsed.username}:{parsed.password}@{pooler_host}:{parsed.port or 6543}"
            pooler_url = urlunparse((
                parsed.scheme,
                pooler_netloc,
                parsed.path,
                parsed.params,
                '?pgbouncer=true',
                parsed.fragment
            ))
            urls_to_try.append((pooler_url, "Pooler URL"))
    except Exception:
        pass
    
    # Пробуем подключиться с разными URL
    conn = None
    for url, description in urls_to_try:
        conn = await try_connect_with_url(url, description)
        if conn:
            break
    
    if not conn:
        print("\n❌ Не удалось подключиться ни с одним из вариантов URL")
        print("\n💡 Рекомендации:")
        print("   1. Проверьте интернет-соединение")
        print("   2. Убедитесь, что SUPABASE_DB_URL правильный")
        print("   3. Попробуйте применить миграцию через Supabase Dashboard:")
        print("      - Откройте https://supabase.com/dashboard")
        print("      - Выберите проект → SQL Editor")
        print("      - Скопируйте SQL из migrations/001_create_tables.sql")
        print("      - Вставьте и выполните")
        return
    
    try:
        print(f"\n📝 Применение миграции из {migration_file}...")
        
        # Выполняем миграцию
        await conn.execute(sql)
        
        print("✅ Миграция успешно применена!")
        print("\n📊 Проверка созданных таблиц...")
        
        # Проверяем созданные таблицы
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'telegram_%'
            ORDER BY table_name
        """)
        
        if tables:
            print(f"\n✅ Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"   ✓ {table['table_name']}")
        else:
            print("⚠️ Таблицы не найдены")
        
        print("\n" + "=" * 60)
        print("✅ Миграция успешно применена! Готово!")
        
    except Exception as e:
        print(f"\n❌ Ошибка при применении миграции: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(apply_migration())
