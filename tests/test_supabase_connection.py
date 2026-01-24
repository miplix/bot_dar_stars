"""
Тест подключения к Supabase через API ключ
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Загружаем переменные из .env
load_dotenv()

async def test_supabase_api():
    """Тест подключения через Supabase REST API"""
    from supabase import create_client, Client
    
    supabase_url = os.getenv('SUPABASE_URL', 'https://ouodquakgyyeiyihmoxg.supabase.co')
    supabase_key = os.getenv('SUPABASE_API_KEY', '') or os.getenv('SUPABASE_ANON_KEY', '')
    
    print("=" * 60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К SUPABASE")
    print("=" * 60)
    print()
    print(f"📡 URL: {supabase_url}")
    if supabase_key:
        # Определяем тип ключа по началу
        if supabase_key.startswith('eyJ'):
            try:
                import base64
                import json
                # Декодируем JWT токен
                parts = supabase_key.split('.')
                if len(parts) >= 2:
                    payload = json.loads(base64.urlsafe_b64decode(parts[1] + '=='))
                    role = payload.get('role', 'unknown')
                    print(f"🔑 API Key: {supabase_key[:20]}... (role: {role})")
                    if role == 'anon':
                        print("   ⚠️  Используется 'anon' ключ - может быть ограничен RLS политиками")
                        print("   💡 Рекомендуется использовать 'service_role' ключ для полного доступа")
                    elif role == 'service_role':
                        print("   ✅ Используется 'service_role' ключ - полный доступ")
                else:
                    print(f"🔑 API Key: {supabase_key[:20]}...")
            except:
                print(f"🔑 API Key: {supabase_key[:20]}...")
        else:
            print(f"🔑 API Key: {supabase_key[:20]}...")
    else:
        print("🔑 API Key: НЕ НАСТРОЕН")
    print()
    
    if not supabase_key:
        print("❌ SUPABASE_API_KEY не настроен в .env файле!")
        print("   Добавьте в .env:")
        print("   SUPABASE_API_KEY=ваш_ключ_здесь")
        return False
    
    if not supabase_url:
        print("❌ SUPABASE_URL не настроен!")
        return False
    
    try:
        print("🔄 Подключаюсь к Supabase...")
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Тест 1: Проверка существования таблицы telegram_users
        print("\n📊 Тест 1: Проверка таблицы telegram_users...")
        try:
            # Пробуем простой запрос без count
            response = supabase.table('telegram_users').select('user_id').limit(1).execute()
            print(f"✅ Таблица telegram_users найдена и доступна!")
            print(f"   Найдено записей: {len(response.data) if response.data else 0}")
        except Exception as e:
            error_msg = str(e)
            print(f"⚠️  Ошибка при проверке таблицы: {error_msg}")
            
            # Проверяем тип ошибки
            if 'PGRST205' in error_msg or 'schema cache' in error_msg.lower():
                print("\n💡 Возможные причины:")
                print("   1. PostgREST кэш схемы не обновился (подождите 1-2 минуты)")
                print("   2. Используется 'anon' ключ вместо 'service_role'")
                print("   3. RLS политики блокируют доступ")
                print("\n   Решение:")
                print("   - Используйте 'service_role' ключ для полного доступа")
                print("   - Или подождите несколько минут для обновления кэша")
            else:
                print("   Возможно, таблица не существует или нет доступа")
        
        # Тест 2: Попытка чтения данных
        print("\n📊 Тест 2: Чтение данных из telegram_users...")
        try:
            response = supabase.table('telegram_users').select('*').limit(5).execute()
            if response.data:
                print(f"✅ Данные успешно прочитаны!")
                print(f"   Найдено записей: {len(response.data)}")
                if len(response.data) > 0:
                    print(f"   Пример записи: user_id={response.data[0].get('user_id', 'N/A')}")
            else:
                print("✅ Таблица пуста (это нормально для нового проекта)")
        except Exception as e:
            print(f"❌ Ошибка при чтении данных: {e}")
            return False
        
        # Тест 3: Проверка других таблиц
        print("\n📊 Тест 3: Проверка других таблиц...")
        tables_to_check = [
            'telegram_calculations',
            'telegram_promocodes',
            'telegram_alphabet',
            'telegram_ma_zhi_kun_positions',
            'telegram_gift_fields'
        ]
        
        found_tables = []
        for table_name in tables_to_check:
            try:
                response = supabase.table(table_name).select('*').limit(1).execute()
                found_tables.append(table_name)
                print(f"   ✅ {table_name}")
            except Exception as e:
                print(f"   ⚠️  {table_name}: {e}")
        
        print(f"\n✅ Найдено таблиц: {len(found_tables)}/{len(tables_to_check)}")
        
        print("\n" + "=" * 60)
        print("✅ ПОДКЛЮЧЕНИЕ К SUPABASE РАБОТАЕТ!")
        print("=" * 60)
        print("\n💡 Теперь можно запускать бота - он будет использовать Supabase")
        return True
        
    except ImportError:
        print("❌ Библиотека supabase не установлена!")
        print("   Установите: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        print(f"   Тип ошибки: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

async def test_supabase_postgres():
    """Тест подключения через прямое подключение PostgreSQL"""
    import asyncpg
    from urllib.parse import quote_plus, urlparse, parse_qs, urlencode, urlunparse
    
    database_url = os.getenv('SUPABASE_DB_URL', '') or os.getenv('DATABASE_URL', '')
    
    print("\n" + "=" * 60)
    print("ТЕСТ ПОДКЛЮЧЕНИЯ К SUPABASE (PostgreSQL)")
    print("=" * 60)
    print()
    
    if not database_url:
        print("⚠️  SUPABASE_DB_URL не настроен")
        print("   Используется подключение через REST API")
        return False
    
    # Показываем URL с замаскированным паролем
    try:
        parsed = urlparse(database_url)
        if '@' in parsed.netloc:
            auth_part = parsed.netloc.split('@')[0]
            host_part = parsed.netloc.split('@')[1]
            if ':' in auth_part:
                username, password = auth_part.split(':', 1)
                masked_url = f"{parsed.scheme}://{username}:***@{host_part}{parsed.path}"
            else:
                masked_url = f"{parsed.scheme}://***@{host_part}{parsed.path}"
        else:
            masked_url = database_url[:80]
        print(f"📡 Database URL: {masked_url}")
        
        # Проверяем формат
        if 'db.' in database_url and '.supabase.co' in database_url:
            print("   ✅ Формат Direct connection обнаружен")
        elif 'pooler.supabase.com' in database_url:
            print("   ✅ Формат Connection pooling обнаружен")
        else:
            print("   ⚠️  Нестандартный формат URL")
    except:
        print(f"📡 Database URL: {database_url[:80]}...")
    print()
    
    try:
        # Парсим URL и правильно кодируем пароль
        parsed = urlparse(database_url)
        
        # Если пароль содержит специальные символы, кодируем их
        if '@' in parsed.netloc:
            auth_part = parsed.netloc.split('@')[0]
            if ':' in auth_part:
                username, password = auth_part.split(':', 1)
                # Кодируем пароль
                encoded_password = quote_plus(password)
                # Пересобираем URL
                new_netloc = f"{username}:{encoded_password}@{parsed.netloc.split('@')[1]}"
                database_url = urlunparse((
                    parsed.scheme,
                    new_netloc,
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment
                ))
                print(f"🔧 Исправлен URL (пароль закодирован)")
        
        print("🔄 Подключаюсь к PostgreSQL...")
        conn = await asyncpg.connect(database_url)
        
        # Проверка таблицы
        result = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'telegram_users'
            )
        """)
        
        if result:
            print("✅ Таблица telegram_users найдена!")
            
            # Подсчет записей
            count = await conn.fetchval("SELECT COUNT(*) FROM telegram_users")
            print(f"   Количество записей: {count}")
        else:
            print("⚠️  Таблица telegram_users не найдена")
        
        await conn.close()
        print("\n✅ ПОДКЛЮЧЕНИЕ К POSTGRESQL РАБОТАЕТ!")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Ошибка подключения: {error_msg}")
        
        # Проверяем тип ошибки
        if 'getaddrinfo failed' in error_msg or '11001' in error_msg:
            print("\n💡 Проблема с подключением к базе данных:")
            print("   1. Проверьте формат SUPABASE_DB_URL")
            print("   2. Для Direct connection используйте:")
            print("      postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres")
            print("   3. Для Connection pooling используйте:")
            print("      postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?pgbouncer=true")
            print("   4. Убедитесь, что пароль правильно экранирован в URL")
        elif 'password authentication failed' in error_msg.lower():
            print("\n💡 Неверный пароль базы данных")
            print("   Проверьте пароль в Supabase Dashboard → Settings → Database")
        elif 'timeout' in error_msg.lower():
            print("\n💡 Превышено время ожидания")
            print("   Проверьте интернет-соединение и доступность Supabase")
        
        return False

async def main():
    """Главная функция"""
    # Проверяем конфигурацию (без импорта Config, чтобы не требовать BOT_TOKEN)
    supabase_url = os.getenv('SUPABASE_URL', 'https://ouodquakgyyeiyihmoxg.supabase.co')
    supabase_key = os.getenv('SUPABASE_API_KEY', '') or os.getenv('SUPABASE_ANON_KEY', '')
    database_url = os.getenv('SUPABASE_DB_URL', '') or os.getenv('DATABASE_URL', '')
    
    use_supabase_api = bool(supabase_key and supabase_url)
    use_postgresql = bool(database_url)
    
    print("\n📋 ТЕКУЩАЯ КОНФИГУРАЦИЯ:")
    print(f"   USE_SUPABASE_API: {use_supabase_api}")
    print(f"   USE_POSTGRESQL: {use_postgresql}")
    print(f"   USE_SUPABASE: {use_supabase_api or use_postgresql}")
    print()
    
    # Тест через API ключ (если настроен)
    if use_supabase_api:
        success = await test_supabase_api()
        if success:
            return
    
    # Тест через PostgreSQL (если настроен)
    if use_postgresql:
        await test_supabase_postgres()
        return
    
    # Если ничего не настроено
    print("\n⚠️  Supabase не настроен!")
    print("   Добавьте в .env файл:")
    print("   SUPABASE_URL=https://ouodquakgyyeiyihmoxg.supabase.co")
    print("   SUPABASE_API_KEY=ваш_ключ_здесь")
    print()
    print("   Или:")
    print("   SUPABASE_DB_URL=postgresql://...")

if __name__ == '__main__':
    asyncio.run(main())
