"""
Скрипт для проверки всех таблиц в Supabase
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

async def check_all_tables():
    """Проверка всех таблиц в базе данных"""
    import asyncpg
    from urllib.parse import quote_plus, urlparse, urlunparse
    
    database_url = os.getenv('SUPABASE_DB_URL', '') or os.getenv('DATABASE_URL', '')
    
    if not database_url:
        print("❌ SUPABASE_DB_URL не настроен!")
        print("   Проверка через PostgreSQL невозможна")
        return
    
    try:
        # Кодируем пароль в URL
        parsed = urlparse(database_url)
        if '@' in parsed.netloc and ':' in parsed.netloc.split('@')[0]:
            auth_part = parsed.netloc.split('@')[0]
            username, password = auth_part.split(':', 1)
            encoded_password = quote_plus(password)
            new_netloc = f"{username}:{encoded_password}@{parsed.netloc.split('@')[1]}"
            database_url = urlunparse((
                parsed.scheme, new_netloc, parsed.path,
                parsed.params, parsed.query, parsed.fragment
            ))
        
        print("🔄 Подключение к базе данных...")
        conn = await asyncpg.connect(database_url)
        
        # Получаем список всех таблиц
        print("\n📊 ПОЛУЧЕНИЕ СПИСКА ВСЕХ ТАБЛИЦ...\n")
        tables = await conn.fetch("""
            SELECT 
                table_name,
                (SELECT COUNT(*) FROM information_schema.columns 
                 WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        print(f"✅ Найдено таблиц: {len(tables)}\n")
        print("=" * 80)
        
        # Проверяем каждую таблицу
        for table in tables:
            table_name = table['table_name']
            column_count = table['column_count']
            
            # Получаем количество строк
            try:
                row_count = await conn.fetchval(f'SELECT COUNT(*) FROM "{table_name}"')
            except Exception as e:
                row_count = f"Ошибка: {str(e)[:50]}"
            
            # Получаем колонки
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            """, table_name)
            
            print(f"\n📋 Таблица: {table_name}")
            print(f"   Колонок: {column_count}")
            print(f"   Строк: {row_count}")
            
            if isinstance(row_count, int) and row_count > 0 and row_count <= 5:
                # Показываем примеры данных для небольших таблиц
                try:
                    sample = await conn.fetch(f'SELECT * FROM "{table_name}" LIMIT 3')
                    if sample:
                        print(f"\n   Примеры данных (первые {len(sample)} строки):")
                        for i, row in enumerate(sample, 1):
                            print(f"   [{i}] {dict(row)}")
                except Exception as e:
                    print(f"   ⚠️ Не удалось получить примеры: {str(e)[:50]}")
            
            print(f"\n   Структура ({len(columns)} колонок):")
            for col in columns[:10]:  # Показываем первые 10 колонок
                nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"      - {col['column_name']}: {col['data_type']} ({nullable})")
            if len(columns) > 10:
                print(f"      ... и еще {len(columns) - 10} колонок")
            
            print("-" * 80)
        
        await conn.close()
        print("\n✅ Проверка завершена!")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(check_all_tables())
