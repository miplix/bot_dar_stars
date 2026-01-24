"""
Скрипт для просмотра всех таблиц базы данных и их содержимого
"""
import asyncio
import os
import sys
from dotenv import load_dotenv
import asyncpg
import aiosqlite

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Загружаем переменные из .env
load_dotenv()

# Определяем тип базы данных без импорта Config
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://ypxrrjyineyhdrhxdwrk.supabase.co')
SUPABASE_API_KEY = os.getenv('SUPABASE_API_KEY', '') or os.getenv('SUPABASE_ANON_KEY', '')
SUPABASE_DB_URL = os.getenv('SUPABASE_DB_URL', '') or os.getenv('DATABASE_URL', '')
USE_POSTGRESQL = bool(SUPABASE_DB_URL)
USE_SUPABASE_API = bool(SUPABASE_API_KEY and SUPABASE_URL)
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/bot_database.db')

async def show_tables_postgresql(database_url: str):
    """Показать таблицы для PostgreSQL/Supabase"""
    conn = None
    try:
        conn = await asyncpg.connect(database_url)
        try:
            # Получаем список всех таблиц с префиксом telegram_
            tables = await conn.fetch("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name LIKE 'telegram_%'
                ORDER BY table_name
            """)
            
            if not tables:
                print("⚠️  Таблицы с префиксом 'telegram_' не найдены")
                # Попробуем найти все таблицы
                all_tables = await conn.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    ORDER BY table_name
                """)
                if all_tables:
                    print(f"\n📋 Найдено таблиц в схеме 'public': {len(all_tables)}")
                    for table in all_tables:
                        print(f"   - {table['table_name']}")
                return
            
            print(f"\n📊 Найдено таблиц: {len(tables)}\n")
            print("=" * 80)
            
            for table_info in tables:
                table_name = table_info['table_name']
                print(f"\n📋 ТАБЛИЦА: {table_name}")
                print("-" * 80)
                
                # Получаем структуру таблицы
                columns = await conn.fetch("""
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_schema = 'public' 
                    AND table_name = $1
                    ORDER BY ordinal_position
                """, table_name)
                
                print("\n🔹 Структура:")
                for col in columns:
                    col_type = col['data_type']
                    if col['character_maximum_length']:
                        col_type += f"({col['character_maximum_length']})"
                    nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                    default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                    print(f"   • {col['column_name']}: {col_type} {nullable}{default}")
                
                # Получаем количество записей
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                print(f"\n🔹 Количество записей: {count}")
                
                # Показываем данные (первые 10 записей)
                if count > 0:
                    print(f"\n🔹 Содержимое (первые {min(10, count)} записей):")
                    rows = await conn.fetch(f"SELECT * FROM {table_name} LIMIT 10")
                    
                    if rows:
                        # Получаем названия колонок
                        column_names = list(rows[0].keys())
                        
                        # Выводим заголовки
                        header = " | ".join([f"{name[:15]:<15}" for name in column_names])
                        print(f"   {header}")
                        print("   " + "-" * len(header))
                        
                        # Выводим данные
                        for row in rows:
                            values = []
                            for col_name in column_names:
                                value = row[col_name]
                                if value is None:
                                    values.append("NULL")
                                elif isinstance(value, str) and len(value) > 15:
                                    values.append(value[:12] + "...")
                                else:
                                    values.append(str(value)[:15])
                            print(f"   {' | '.join([f'{v:<15}' for v in values])}")
                        
                        if count > 10:
                            print(f"\n   ... и еще {count - 10} записей")
                else:
                    print("\n🔹 Таблица пуста")
                
                print()
            
            print("=" * 80)
        finally:
            if conn:
                await conn.close()
            
    except Exception as e:
        print(f"❌ Ошибка при получении данных: {e}")
        raise  # Пробрасываем исключение, чтобы main мог обработать

async def show_tables_supabase_api(supabase_url: str, supabase_key: str):
    """Показать таблицы через Supabase REST API"""
    try:
        from supabase import create_client
        
        print("🔄 Подключаюсь к Supabase через REST API...")
        supabase = create_client(supabase_url, supabase_key)
        
        # Список таблиц для проверки
        tables_to_check = [
            'telegram_users',
            'telegram_calculations',
            'telegram_gifts_knowledge',
            'telegram_ai_interactions',
            'telegram_payments',
            'telegram_alphabet',
            'telegram_promocodes',
            'telegram_promocode_usage',
            'telegram_ma_zhi_kun_positions',
            'telegram_gift_fields'
        ]
        
        found_tables = []
        for table_name in tables_to_check:
            try:
                # Пробуем получить одну запись для проверки существования таблицы
                response = supabase.table(table_name).select('*').limit(1).execute()
                found_tables.append((table_name, response))
            except Exception as e:
                # Таблица может не существовать или быть недоступной
                pass
        
        if not found_tables:
            print("⚠️  Не удалось найти доступные таблицы")
            print("💡 Возможные причины:")
            print("   - Таблицы еще не созданы (примените миграцию)")
            print("   - Используется 'anon' ключ с ограничениями RLS")
            print("   - Нет доступа к таблицам")
            return
        
        print(f"\n📊 Найдено таблиц: {len(found_tables)}\n")
        print("=" * 80)
        
        for table_name, response in found_tables:
            print(f"\n📋 ТАБЛИЦА: {table_name}")
            print("-" * 80)
            
            # Получаем все данные (с ограничением)
            try:
                all_data = supabase.table(table_name).select('*').limit(100).execute()
                count = len(all_data.data) if all_data.data else 0
                
                print(f"\n🔹 Количество записей (показано): {count}")
                
                if count > 0 and all_data.data:
                    # Получаем названия колонок из первой записи
                    column_names = list(all_data.data[0].keys())
                    
                    print(f"\n🔹 Структура (колонки):")
                    for col_name in column_names:
                        print(f"   • {col_name}")
                    
                    print(f"\n🔹 Содержимое (первые {min(10, count)} записей):")
                    # Выводим заголовки
                    header = " | ".join([f"{name[:15]:<15}" for name in column_names])
                    print(f"   {header}")
                    print("   " + "-" * len(header))
                    
                    # Выводим данные
                    for row in all_data.data[:10]:
                        values = []
                        for col_name in column_names:
                            value = row.get(col_name)
                            if value is None:
                                values.append("NULL")
                            elif isinstance(value, str) and len(value) > 15:
                                values.append(value[:12] + "...")
                            else:
                                values.append(str(value)[:15])
                        print(f"   {' | '.join([f'{v:<15}' for v in values])}")
                    
                    if count > 10:
                        print(f"\n   ... и еще {count - 10} записей (показано максимум 100)")
                else:
                    print("\n🔹 Таблица пуста")
            except Exception as e:
                print(f"\n⚠️  Ошибка при чтении данных: {e}")
            
            print()
        
        print("=" * 80)
        
    except ImportError:
        print("❌ Библиотека supabase не установлена!")
        print("   Установите: pip install supabase")
        raise
    except Exception as e:
        print(f"❌ Ошибка при работе с Supabase API: {e}")
        raise

async def show_tables_sqlite(db_path: str):
    """Показать таблицы для SQLite"""
    try:
        async with aiosqlite.connect(db_path) as conn:
            # Получаем список всех таблиц
            cursor = await conn.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' 
                AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            tables = await cursor.fetchall()
            
            if not tables:
                print("⚠️  Таблицы не найдены")
                return
            
            print(f"\n📊 Найдено таблиц: {len(tables)}\n")
            print("=" * 80)
            
            for (table_name,) in tables:
                print(f"\n📋 ТАБЛИЦА: {table_name}")
                print("-" * 80)
                
                # Получаем структуру таблицы
                cursor = await conn.execute(f"PRAGMA table_info({table_name})")
                columns = await cursor.fetchall()
                
                print("\n🔹 Структура:")
                for col in columns:
                    col_id, col_name, col_type, not_null, default_val, pk = col
                    nullable = "NOT NULL" if not_null else "NULL"
                    default = f" DEFAULT {default_val}" if default_val else ""
                    pk_str = " PRIMARY KEY" if pk else ""
                    print(f"   • {col_name}: {col_type} {nullable}{default}{pk_str}")
                
                # Получаем количество записей
                cursor = await conn.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = (await cursor.fetchone())[0]
                print(f"\n🔹 Количество записей: {count}")
                
                # Показываем данные (первые 10 записей)
                if count > 0:
                    print(f"\n🔹 Содержимое (первые {min(10, count)} записей):")
                    conn.row_factory = aiosqlite.Row
                    cursor = await conn.execute(f"SELECT * FROM {table_name} LIMIT 10")
                    rows = await cursor.fetchall()
                    
                    if rows:
                        # Получаем названия колонок
                        column_names = list(rows[0].keys())
                        
                        # Выводим заголовки
                        header = " | ".join([f"{name[:15]:<15}" for name in column_names])
                        print(f"   {header}")
                        print("   " + "-" * len(header))
                        
                        # Выводим данные
                        for row in rows:
                            values = []
                            for col_name in column_names:
                                value = row[col_name]
                                if value is None:
                                    values.append("NULL")
                                elif isinstance(value, str) and len(value) > 15:
                                    values.append(value[:12] + "...")
                                else:
                                    values.append(str(value)[:15])
                            print(f"   {' | '.join([f'{v:<15}' for v in values])}")
                        
                        if count > 10:
                            print(f"\n   ... и еще {count - 10} записей")
                else:
                    print("\n🔹 Таблица пуста")
                
                print()
            
            print("=" * 80)
            
    except Exception as e:
        print(f"❌ Ошибка при получении данных: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Главная функция"""
    print("=" * 80)
    print("ПРОСМОТР ТАБЛИЦ БАЗЫ ДАННЫХ")
    print("=" * 80)
    print()
    
    # Пробуем подключиться к Supabase через PostgreSQL
    if USE_POSTGRESQL and SUPABASE_DB_URL:
        print("🔥 Пытаюсь подключиться к PostgreSQL/Supabase")
        print(f"   URL: {SUPABASE_URL or 'установлен через SUPABASE_DB_URL'}")
        print()
        try:
            await show_tables_postgresql(SUPABASE_DB_URL)
            return
        except Exception as e:
            error_msg = str(e)
            print(f"\n⚠️  Не удалось подключиться к PostgreSQL")
            if 'getaddrinfo failed' in error_msg or '11001' in error_msg:
                print("   Причина: проблема с подключением к серверу")
            elif 'password authentication failed' in error_msg.lower():
                print("   Причина: неверный пароль")
            else:
                print(f"   Ошибка: {error_msg}")
            
            # Пробуем через REST API, если доступен
            if USE_SUPABASE_API:
                print("\n💡 Пробую использовать Supabase REST API...")
                print()
                try:
                    await show_tables_supabase_api(SUPABASE_URL, SUPABASE_API_KEY)
                    return
                except Exception as api_e:
                    print(f"⚠️  Не удалось подключиться через REST API: {api_e}")
                    print("💡 Пробую использовать SQLite...")
                    print()
            else:
                print("💡 Пробую использовать SQLite...")
                print()
    
    # Используем SQLite
    print(f"💾 Используется SQLite")
    print(f"   Путь: {DATABASE_PATH}")
    print()
    # Создаем директорию, если её нет
    db_dir = os.path.dirname(DATABASE_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    
    # Проверяем, существует ли файл базы данных
    if not os.path.exists(DATABASE_PATH):
        print(f"⚠️  Файл базы данных не найден: {DATABASE_PATH}")
        print("💡 База данных будет создана при первом запуске бота")
        return
    
    await show_tables_sqlite(DATABASE_PATH)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
