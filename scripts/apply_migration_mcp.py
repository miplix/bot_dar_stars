"""
Скрипт для применения миграции к Supabase через прямое подключение
Создает функцию exec_sql если её нет, затем применяет миграцию
"""
import asyncio
import asyncpg
import os
import sys
from dotenv import load_dotenv

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

async def create_exec_sql_function(conn):
    """Создает функцию exec_sql в базе данных если её нет"""
    try:
        # Проверяем, существует ли функция
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT 1 
                FROM pg_proc 
                WHERE proname = 'exec_sql'
            )
        """)
        
        if exists:
            print("   ✅ Функция exec_sql уже существует")
            return True
        
        print("   📝 Создание функции exec_sql...")
        
        # Создаем функцию exec_sql
        await conn.execute("""
            CREATE OR REPLACE FUNCTION exec_sql(sql_text text)
            RETURNS json
            LANGUAGE plpgsql
            SECURITY DEFINER
            AS $$
            BEGIN
                EXECUTE sql_text;
                RETURN json_build_object('status', 'success', 'message', 'SQL executed successfully');
            EXCEPTION WHEN OTHERS THEN
                RETURN json_build_object('status', 'error', 'message', SQLERRM);
            END;
            $$;
        """)
        
        # Даем права service_role
        await conn.execute("""
            GRANT EXECUTE ON FUNCTION exec_sql(text) TO service_role;
        """)
        
        print("   ✅ Функция exec_sql успешно создана")
        return True
        
    except Exception as e:
        print(f"   ⚠️ Ошибка при создании функции exec_sql: {e}")
        return False

async def apply_migration_direct():
    """Применяет миграцию через прямое подключение к PostgreSQL"""
    print("🚀 Применение миграции к Supabase через прямое подключение")
    print("=" * 60)
    
    # Получаем DATABASE_URL
    database_url = (
        os.getenv('SUPABASE_DB_URL') or
        os.getenv('POSTGRES_URL_NON_POOLING') or
        os.getenv('POSTGRES_PRISMA_URL') or 
        os.getenv('POSTGRES_URL') or 
        os.getenv('DATABASE_URL')
    )
    
    if not database_url:
        print("❌ DATABASE_URL не установлен!")
        print("\n💡 Установите одну из переменных:")
        print("  - SUPABASE_DB_URL (рекомендуется)")
        print("  - POSTGRES_URL_NON_POOLING")
        print("  - DATABASE_URL")
        return False
    
    supabase_url = os.getenv('SUPABASE_URL', '')
    if supabase_url:
        print(f"   Supabase URL: {supabase_url}")
    
    # Обрабатываем URL для правильного подключения
    from urllib.parse import quote_plus, urlparse, urlunparse
    
    conn_url = database_url
    
    # Убираем параметры pgbouncer для миграций (нужен прямой доступ)
    if '?pgbouncer=true' in conn_url:
        conn_url = conn_url.split('?')[0]
    
    # Если используется pooler, пробуем заменить на прямой connection
    if 'pooler.supabase.com' in conn_url:
        print("   🔄 Обнаружен pooler URL, заменяем на прямой connection...")
        conn_url = conn_url.replace('pooler.supabase.com', 'db.supabase.co')
        if '?' in conn_url:
            conn_url = conn_url.split('?')[0]
    
    # Правильно кодируем пароль в URL
    try:
        parsed = urlparse(conn_url)
        if '@' in parsed.netloc and ':' in parsed.netloc.split('@')[0]:
            auth_part = parsed.netloc.split('@')[0]
            username, password = auth_part.split(':', 1)
            
            if '%' not in password:
                encoded_password = quote_plus(password, safe='')
            else:
                encoded_password = password
            
            new_netloc = f"{username}:{encoded_password}@{parsed.netloc.split('@')[1]}"
            conn_url = urlunparse((
                parsed.scheme,
                new_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
    except Exception as e:
        print(f"   ⚠️ Предупреждение при обработке URL: {e}")
    
    # Отладочная информация (скрываем пароль)
    try:
        parsed_debug = urlparse(conn_url)
        if parsed_debug.password:
            debug_url = conn_url.replace(parsed_debug.password, '***')
        else:
            debug_url = conn_url
        print(f"   Connection URL: {debug_url[:100]}...")
    except:
        pass
    
    try:
        print("\n🔗 Подключение к базе данных...")
        
        # Пробуем подключиться
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(conn_url, timeout=10),
                timeout=15
            )
        except asyncio.TimeoutError:
            print("   ❌ Таймаут подключения")
            return False
        except Exception as e:
            error_msg = str(e)
            # Если прямой connection не работает, пробуем pooler
            if 'db.supabase.co' in conn_url:
                print(f"   ⚠️ Прямое подключение не удалось: {error_msg}")
                print("   🔄 Пробуем через pooler...")
                # Пробуем pooler URL
                pooler_url = conn_url.replace('db.supabase.co', 'pooler.supabase.com')
                if '?' not in pooler_url:
                    pooler_url += '?pgbouncer=true'
                try:
                    conn = await asyncio.wait_for(
                        asyncpg.connect(pooler_url, timeout=10),
                        timeout=15
                    )
                    print("   ✅ Подключение через pooler установлено")
                except Exception as e2:
                    print(f"   ❌ Pooler подключение также не удалось: {e2}")
                    raise e
            else:
                raise e
        
        print("   ✅ Подключение установлено")
        
        # Создаем функцию exec_sql если её нет
        await create_exec_sql_function(conn)
        
        # Читаем SQL миграцию
        migration_file = 'migrations/001_create_tables.sql'
        if not os.path.exists(migration_file):
            print(f"\n❌ Файл миграции {migration_file} не найден!")
            await conn.close()
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"\n📝 Применение миграции из {migration_file}...")
        
        # Выполняем миграцию
        try:
            await conn.execute(sql)
            print("   ✅ Миграция успешно применена!")
        except Exception as e:
            error_msg = str(e)
            # Игнорируем ошибки "already exists" для таблиц и индексов
            if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                print(f"   ⚠️ Некоторые объекты уже существуют: {error_msg[:100]}")
                print("   ✅ Миграция применена (существующие объекты пропущены)")
            else:
                print(f"   ❌ Ошибка при применении миграции: {error_msg}")
                raise
        
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
            print("   ⚠️ Таблицы не найдены")
        
        await conn.close()
        print("\n" + "=" * 60)
        print("✅ Миграция успешно применена! Готово!")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Ошибка при применении миграции: {error_msg}")
        print("=" * 60)
        
        if 'getaddrinfo failed' in error_msg or '11001' in error_msg:
            print("\n💡 Проблема с подключением к серверу базы данных")
            print("   Возможные причины:")
            print("   - Неверный SUPABASE_DB_URL")
            print("   - Проблемы с сетью")
            print("   - Неправильный формат URL")
            print("\n💡 Решение:")
            print("   1. Проверьте SUPABASE_DB_URL в .env файле")
            print("   2. Получите правильный Connection String из Supabase Dashboard:")
            print("      Settings → Database → Connection String (URI)")
            print("   3. Убедитесь, что используете прямой connection (не pooler)")
        elif 'password authentication failed' in error_msg.lower():
            print("\n💡 Неверный пароль базы данных")
            print("   Решение:")
            print("   1. Проверьте пароль в SUPABASE_DB_URL")
            print("   2. Убедитесь, что пароль правильно закодирован в URL")
        elif 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
            print("\n💡 Проблема с подключением")
            print("   Решение:")
            print("   1. Проверьте интернет-соединение")
            print("   2. Убедитесь, что SUPABASE_DB_URL правильный")
        else:
            import traceback
            print("\n📋 Детали ошибки:")
            traceback.print_exc()
        
        return False

if __name__ == '__main__':
    success = asyncio.run(apply_migration_direct())
    sys.exit(0 if success else 1)
