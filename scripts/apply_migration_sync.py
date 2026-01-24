"""
Синхронный скрипт для применения миграции к Supabase/PostgreSQL
Использует psycopg2 вместо asyncpg для лучшей совместимости с Windows
"""
import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from urllib.parse import urlparse, urlunparse, quote_plus

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def apply_migration():
    """Применяет миграцию к базе данных"""
    print("Применение миграции к Supabase/PostgreSQL (синхронная версия)")
    print("=" * 60)
    
    # Получаем DATABASE_URL из переменных окружения
    database_url = (
        os.getenv('SUPABASE_DB_URL') or
        os.getenv('POSTGRES_PRISMA_URL') or 
        os.getenv('POSTGRES_URL') or 
        os.getenv('DATABASE_URL')
    )
    
    if not database_url:
        print("ОШИБКА: DATABASE_URL не установлен!")
        print("\nУбедитесь, что установлена переменная:")
        print("  - SUPABASE_DB_URL (для Supabase) - РЕКОМЕНДУЕТСЯ")
        print("  - POSTGRES_URL или POSTGRES_PRISMA_URL (для Vercel Postgres)")
        print("  - DATABASE_URL (общий вариант)")
        return False
    
    # Обрабатываем URL
    conn_url = database_url.replace('?pgbouncer=true', '').split('?')[0]
    
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
        print(f"Предупреждение при обработке URL: {e}")
    
    print(f"\nПодключение к базе данных...")
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(conn_url, connect_timeout=10)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        print("Подключение установлено")
        
        # Читаем SQL миграцию
        migration_file = 'migrations/001_create_tables.sql'
        if not os.path.exists(migration_file):
            print(f"ОШИБКА: Файл миграции {migration_file} не найден!")
            conn.close()
            return False
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"\nПрименение миграции из {migration_file}...")
        
        # Выполняем миграцию
        cursor = conn.cursor()
        cursor.execute(sql)
        cursor.close()
        
        print("Миграция успешно применена!")
        print("\nПроверка созданных таблиц...")
        
        # Проверяем созданные таблицы
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'telegram_%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        if tables:
            print(f"\nНайдено таблиц: {len(tables)}")
            for table in tables:
                print(f"   ✓ {table[0]}")
        else:
            print("Таблицы не найдены. Возможно, они уже существуют или произошла ошибка.")
        
        cursor.close()
        conn.close()
        print("\n" + "=" * 60)
        print("Миграция успешно применена! Готово!")
        return True
        
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        print(f"\nОШИБКА при применении миграции: {error_msg}")
        print("=" * 60)
        
        if 'could not translate host name' in error_msg.lower() or 'getaddrinfo' in error_msg.lower():
            print("\nПроблема с подключением к серверу базы данных")
            print("Возможные причины:")
            print("  - Неверный SUPABASE_DB_URL или DATABASE_URL")
            print("  - Проблемы с сетью или DNS")
            print("\nРешение:")
            print("  1. Проверьте SUPABASE_DB_URL в .env файле")
            print("  2. Получите правильный Connection String из Supabase Dashboard:")
            print("     Settings → Database → Connection String (URI)")
            print("  3. Или примените миграцию через Supabase Dashboard → SQL Editor")
            print("     (используйте скрипт: python apply_migration_manual.py)")
        elif 'password authentication failed' in error_msg.lower():
            print("\nНеверный пароль базы данных")
            print("Решение:")
            print("  1. Откройте Supabase Dashboard → Settings → Database")
            print("  2. Проверьте или сбросьте пароль базы данных")
            print("  3. Обновите SUPABASE_DB_URL в .env с новым паролем")
        else:
            print("\nОбщие рекомендации:")
            print("  1. Проверьте правильность SUPABASE_DB_URL в .env")
            print("  2. Убедитесь, что пароль правильно закодирован в URL")
            print("  3. Попробуйте применить миграцию через Supabase Dashboard:")
            print("     (используйте скрипт: python apply_migration_manual.py)")
        return False
    except Exception as e:
        print(f"\nОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
