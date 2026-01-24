"""
Тестовый скрипт для проверки подключения к Supabase PostgreSQL
"""
import asyncio
import asyncpg
import os
import sys
from dotenv import load_dotenv
from urllib.parse import quote_plus, urlparse, urlunparse

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

async def test_connection():
    """Тестирует подключение к Supabase"""
    print("=" * 60)
    print("🔍 ТЕСТ ПОДКЛЮЧЕНИЯ К SUPABASE")
    print("=" * 60)
    print()
    
    database_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL', '')
    
    if not database_url:
        print("❌ SUPABASE_DB_URL не установлен!")
        return
    
    # Маскируем пароль для вывода
    if '@' in database_url:
        parts = database_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            if len(user_pass) == 2:
                masked_url = f"{user_pass[0]}:***@{parts[1]}"
            else:
                masked_url = database_url
        else:
            masked_url = database_url
    else:
        masked_url = database_url
    
    print(f"📋 URL (пароль скрыт): {masked_url}")
    print()
    
    # Парсим URL
    try:
        parsed = urlparse(database_url)
        print(f"🔍 Анализ URL:")
        print(f"   Схема: {parsed.scheme}")
        print(f"   Хост: {parsed.hostname}")
        print(f"   Порт: {parsed.port}")
        print(f"   База данных: {parsed.path.lstrip('/')}")
        print()
        
        # Проверяем хост
        if parsed.hostname:
            print(f"🌐 Проверка хоста: {parsed.hostname}")
            import socket
            try:
                ip = socket.gethostbyname(parsed.hostname)
                print(f"   ✅ Хост разрешен: {ip}")
            except socket.gaierror as e:
                print(f"   ❌ Ошибка DNS: {e}")
                print("   💡 Проверьте интернет-соединение и правильность хоста")
                return
        else:
            print("❌ Хост не найден в URL")
            return
        
    except Exception as e:
        print(f"❌ Ошибка при парсинге URL: {e}")
        return
    
    # Обрабатываем URL для подключения
    conn_url = database_url.replace('?pgbouncer=true', '').split('?')[0]
    
    # Кодируем пароль
    try:
        parsed = urlparse(conn_url)
        if '@' in parsed.netloc and ':' in parsed.netloc.split('@')[0]:
            auth_part = parsed.netloc.split('@')[0]
            username, password = auth_part.split(':', 1)
            
            # Кодируем пароль
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
        print(f"⚠️ Предупреждение при обработке URL: {e}")
    
    # Пробуем подключиться
    print()
    print("🔗 Попытка подключения...")
    try:
        conn = await asyncpg.connect(conn_url, timeout=10)
        print("✅ Подключение успешно!")
        
        # Проверяем версию PostgreSQL
        version = await conn.fetchval("SELECT version()")
        print(f"📊 Версия PostgreSQL: {version.split(',')[0]}")
        
        # Проверяем существующие таблицы
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'telegram_%'
            ORDER BY table_name
        """)
        
        if tables:
            print(f"\n📋 Найдено таблиц: {len(tables)}")
            for table in tables:
                print(f"   - {table['table_name']}")
        else:
            print("\n📋 Таблицы не найдены (миграция еще не применена)")
        
        await conn.close()
        print("\n✅ Тест завершен успешно!")
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n❌ Ошибка подключения: {error_msg}")
        
        if 'getaddrinfo failed' in error_msg or '11001' in error_msg:
            print("\n💡 Проблема с DNS:")
            print("   1. Проверьте интернет-соединение")
            print("   2. Проверьте правильность хоста в SUPABASE_DB_URL")
            print("   3. Попробуйте ping к хосту: ping db.sukhbbohmkbvbivthovp.supabase.co")
        elif 'password authentication failed' in error_msg.lower():
            print("\n💡 Неверный пароль:")
            print("   1. Проверьте пароль в Supabase Dashboard")
            print("   2. Убедитесь, что пароль правильно закодирован в URL")
        elif 'timeout' in error_msg.lower():
            print("\n💡 Таймаут подключения:")
            print("   1. Проверьте интернет-соединение")
            print("   2. Проверьте, не блокирует ли файрвол подключение")
        else:
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_connection())
