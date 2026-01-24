"""
Скрипт для применения миграции к Supabase/PostgreSQL
Поддерживает подключение через SUPABASE_DB_URL или SUPABASE_API_KEY
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

# Пробуем импортировать Supabase клиент
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("⚠️ Supabase Python клиент не установлен. Установите: pip install supabase")

async def apply_migration_via_supabase_api():
    """Применение миграции через Supabase Python SDK используя RPC функцию exec_sql"""
    if not SUPABASE_AVAILABLE:
        print("   ⚠️ Supabase Python клиент не установлен!")
        print("   💡 Установите: pip install supabase")
        return False
    
    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    # Используем Service Role Key для выполнения SQL (обязательно!)
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_API_KEY')
    
    # Для выполнения SQL нужен Service Role Key (не Anon Key!)
    if not supabase_service_key:
        print("   ⚠️ SUPABASE_SERVICE_ROLE_KEY не найден!")
        print("   💡 Для выполнения SQL через API нужен Service Role Key")
        print("   💡 Получите его из Supabase Dashboard → Settings → API → service_role key")
        return False
    
    if not supabase_url:
        return False
    
    try:
        print("🔧 Применение миграции через Supabase Python SDK (Service Role Key)...")
        
        # Создаем клиент Supabase с Service Role Key
        supabase: Client = create_client(supabase_url, supabase_service_key)
        
        # Читаем SQL миграцию
        migration_file = 'migrations/001_create_tables.sql'
        if not os.path.exists(migration_file):
            print(f"❌ Файл миграции {migration_file} не найден!")
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        # Очищаем SQL от комментариев
        sql_clean = []
        for line in sql.split('\n'):
            line = line.strip()
            if line and not line.startswith('--'):
                sql_clean.append(line)
        
        full_sql = ' '.join(sql_clean)
        
        print("   📝 Попытка выполнения SQL через RPC функцию exec_sql...")
        
        # Пробуем вызвать RPC функцию exec_sql через Supabase Python SDK
        try:
            response = supabase.rpc('exec_sql', {'sql_text': full_sql}).execute()
            
            # Проверяем результат
            if hasattr(response, 'data') and response.data:
                result = response.data
                if isinstance(result, dict):
                    if result.get('status') == 'success':
                        print("   ✅ SQL успешно выполнен через RPC функцию!")
                        print(f"   Сообщение: {result.get('message', '')}")
                        return True
                    elif result.get('status') == 'error':
                        print(f"   ❌ Ошибка при выполнении SQL: {result.get('message', '')}")
                        return False
                else:
                    print("   ✅ SQL успешно выполнен через RPC функцию!")
                    print(f"   Результат: {result}")
                    return True
            else:
                # Если ответ пустой, но нет ошибки - считаем успешным
                print("   ✅ SQL успешно выполнен через RPC функцию!")
                return True
                
        except Exception as rpc_error:
            error_msg = str(rpc_error)
            
            # Проверяем, не найдена ли функция
            if '404' in error_msg or 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower() or 'PGRST202' in error_msg or 'Could not find the function' in error_msg:
                print("   ⚠️ RPC функция exec_sql не найдена в базе данных")
                print("   💡 Нужно создать функцию exec_sql в Supabase")
                print("   💡 Выполните следующий SQL в Supabase Dashboard → SQL Editor:")
                print("\n" + "="*60)
                print("""
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

GRANT EXECUTE ON FUNCTION exec_sql(text) TO service_role;
                """.strip())
                print("="*60)
                print("\n   📌 После создания функции:")
                print("      1. Подождите несколько секунд (для обновления schema cache)")
                print("      2. Запустите скрипт снова: python scripts/apply_migration.py")
                return False
            else:
                print(f"   ❌ Ошибка при вызове RPC функции: {error_msg}")
                import traceback
                traceback.print_exc()
                return False
        
    except Exception as e:
        print(f"❌ Ошибка при использовании Supabase API: {e}")
        import traceback
        traceback.print_exc()
        return False

async def apply_migration():
    """Применяет миграцию к базе данных"""
    print("🚀 Применение миграции к Supabase/PostgreSQL")
    print("=" * 60)
    
    # Получаем настройки Supabase
    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_API_KEY')
    supabase_api_key = os.getenv('SUPABASE_API_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
    
    # Получаем DATABASE_URL из переменных окружения (поддержка Supabase)
    database_url = (
        os.getenv('SUPABASE_DB_URL') or
        os.getenv('POSTGRES_PRISMA_URL') or 
        os.getenv('POSTGRES_URL') or 
        os.getenv('DATABASE_URL')
    )
    
    # СНАЧАЛА пробуем через API, если есть Service Role Key
    if supabase_service_key and supabase_url:
        print("🔑 Найден SUPABASE_SERVICE_ROLE_KEY, пробуем применить миграцию через API...")
        success = await apply_migration_via_supabase_api()
        if success:
            print("\n✅ Миграция успешно применена через Supabase API!")
            return
        else:
            print("\n⚠️ Не удалось применить миграцию через API, пробуем прямое подключение...")
    
    # Если есть только API ключ, но нет DB URL и Service Role Key
    if not database_url and supabase_api_key and supabase_url and not supabase_service_key:
        print("⚠️ SUPABASE_DB_URL не установлен, и нет SUPABASE_SERVICE_ROLE_KEY")
        print("\n💡 Для применения миграций нужен один из вариантов:")
        print("   1. SUPABASE_SERVICE_ROLE_KEY (для применения через API)")
        print("   2. SUPABASE_DB_URL (для прямого подключения)")
        print("\n📌 Получите SUPABASE_SERVICE_ROLE_KEY из Supabase Dashboard:")
        print("   Settings → API → service_role key")
        print("\n📌 Или получите SUPABASE_DB_URL:")
        print("   Settings → Database → Connection String (URI)")
        print("\n💡 Альтернативный способ применения миграции:")
        print("   1. Откройте Supabase Dashboard → SQL Editor")
        print("   2. Скопируйте содержимое файла: migrations/001_create_tables.sql")
        print("   3. Вставьте и выполните SQL в редакторе")
        return
    
    if not database_url:
        print("❌ DATABASE_URL не установлен!")
        print("\nУбедитесь, что установлена переменная:")
        print("  - SUPABASE_DB_URL (для Supabase) - РЕКОМЕНДУЕТСЯ")
        print("  - POSTGRES_URL или POSTGRES_PRISMA_URL (для Vercel Postgres)")
        print("  - DATABASE_URL (общий вариант)")
        print("\n💡 Альтернативный способ применения миграции:")
        print("   1. Откройте Supabase Dashboard → SQL Editor")
        print("   2. Скопируйте содержимое файла: migrations/001_create_tables.sql")
        print("   3. Вставьте и выполните SQL в редакторе")
        return
    
    # Удаляем параметры pgbouncer из URL если есть (для миграций нужен прямой доступ)
    # Используем POSTGRES_URL_NON_POOLING если доступен
    from urllib.parse import quote_plus, urlparse, urlunparse
    
    conn_url = os.getenv('POSTGRES_URL_NON_POOLING') or database_url.replace('?pgbouncer=true', '').split('?')[0]
    
    # Правильно кодируем пароль в URL (если содержит специальные символы)
    try:
        parsed = urlparse(conn_url)
        if '@' in parsed.netloc and ':' in parsed.netloc.split('@')[0]:
            auth_part = parsed.netloc.split('@')[0]
            username, password = auth_part.split(':', 1)
            
            # Проверяем, не закодирован ли пароль уже
            # Если пароль содержит % - возможно уже закодирован
            if '%' not in password:
                # Кодируем пароль (особенно важно для специальных символов)
                encoded_password = quote_plus(password, safe='')
            else:
                # Пароль уже закодирован, используем как есть
                encoded_password = password
            
            # Пересобираем URL
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
        print(f"⚠️ Предупреждение при обработке URL: {e}")
        print(f"   Используем исходный URL")
    
    print(f"\n🔗 Подключение к базе данных...")
    if supabase_url:
        print(f"   Supabase URL: {supabase_url}")
    
    # Отладочная информация (скрываем пароль)
    try:
        parsed_debug = urlparse(conn_url)
        if parsed_debug.password:
            debug_url = conn_url.replace(parsed_debug.password, '***')
        else:
            debug_url = conn_url
        print(f"   Connection URL: {debug_url[:80]}...")
    except:
        pass
    
    try:
        # Для Supabase pooler нужно использовать прямой connection string
        # Если URL содержит pooler, попробуем заменить на прямой
        if 'pooler.supabase.com' in conn_url:
            print("   Обнаружен pooler URL, пытаемся использовать прямой connection...")
            # Заменяем pooler на прямой хост
            conn_url_direct = conn_url.replace('pooler.supabase.com', 'db.supabase.co')
            # Убираем параметры pgbouncer
            if '?' in conn_url_direct:
                conn_url_direct = conn_url_direct.split('?')[0]
            print(f"   Пробуем прямой connection...")
            try:
                conn = await asyncpg.connect(conn_url_direct, timeout=10)
            except Exception as e1:
                print(f"   Прямой connection не удался: {e1}")
                print(f"   Пробуем через pooler...")
                conn = await asyncpg.connect(conn_url, timeout=10)
        elif 'db.supabase.co' in conn_url:
            # Если используется прямой URL, но он не работает, пробуем pooler
            print("   Пробуем прямое подключение...")
            try:
                conn = await asyncpg.connect(conn_url, timeout=10)
            except Exception as e1:
                print(f"   Прямое подключение не удалось: {e1}")
                # Пробуем использовать pooler URL
                print("   Пробуем через pooler URL...")
                # Извлекаем проект ID из URL
                try:
                    parsed = urlparse(conn_url)
                    host_parts = parsed.hostname.split('.')
                    if len(host_parts) >= 1:
                        project_id = host_parts[0]
                        # Создаем pooler URL
                        pooler_url = conn_url.replace(f'db.{project_id}.supabase.co', f'{project_id}.pooler.supabase.com')
                        # Добавляем параметры для транзакционного режима
                        if '?' not in pooler_url:
                            pooler_url += '?pgbouncer=true'
                        print(f"   Пробуем pooler URL...")
                        conn = await asyncpg.connect(pooler_url, timeout=10)
                    else:
                        raise e1
                except Exception as e2:
                    print(f"   Pooler подключение также не удалось: {e2}")
                    raise e1
        else:
            conn = await asyncpg.connect(conn_url, timeout=10)
        print("✅ Подключение установлено")
        
        # Читаем SQL миграцию
        migration_file = 'migrations/001_create_tables.sql'
        if not os.path.exists(migration_file):
            print(f"❌ Файл миграции {migration_file} не найден!")
            await conn.close()
            return
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
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
            print("⚠️ Таблицы не найдены. Возможно, они уже существуют или произошла ошибка.")
        
        await conn.close()
        print("\n" + "=" * 60)
        print("✅ Миграция успешно применена! Готово!")
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Ошибка при применении миграции: {error_msg}")
        print("=" * 60)
        
        if 'getaddrinfo failed' in error_msg or '11001' in error_msg:
            print("\n💡 Проблема с подключением к серверу базы данных")
            print("   Возможные причины:")
            print("   - Неверный SUPABASE_DB_URL или DATABASE_URL")
            print("   - Проблемы с сетью")
            print("\n💡 Решение:")
            print("   1. Проверьте SUPABASE_DB_URL в .env файле")
            print("   2. Получите правильный Connection String из Supabase Dashboard:")
            print("      Settings → Database → Connection String (URI)")
            print("   3. Или примените миграцию через Supabase Dashboard → SQL Editor")
        elif 'password authentication failed' in error_msg.lower():
            print("\n💡 Неверный пароль базы данных")
            print("   Решение:")
            print("   1. Откройте Supabase Dashboard → Settings → Database")
            print("   2. Проверьте или сбросьте пароль базы данных")
            print("   3. Обновите SUPABASE_DB_URL в .env с новым паролем")
            print("   4. Убедитесь, что пароль правильно закодирован в URL")
        elif 'connection' in error_msg.lower() or 'timeout' in error_msg.lower():
            print("\n💡 Проблема с подключением")
            print("   Решение:")
            print("   1. Проверьте интернет-соединение")
            print("   2. Убедитесь, что SUPABASE_DB_URL правильный")
            print("   3. Попробуйте применить миграцию через Supabase Dashboard → SQL Editor")
        else:
            print("\n💡 Общие рекомендации:")
            print("   1. Проверьте правильность SUPABASE_DB_URL в .env")
            print("   2. Убедитесь, что пароль правильно закодирован в URL")
            print("   3. Попробуйте применить миграцию через Supabase Dashboard:")
            print("      - Откройте SQL Editor")
            print("      - Скопируйте содержимое: migrations/001_create_tables.sql")
            print("      - Вставьте и выполните SQL")
            import traceback
            print("\n📋 Детали ошибки:")
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(apply_migration())

