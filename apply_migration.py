"""
Скрипт для применения миграции к Neon Postgres
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def apply_migration():
    """Применяет миграцию к базе данных"""
    # Получаем DATABASE_URL из переменных окружения
    database_url = (
        os.getenv('POSTGRES_PRISMA_URL') or 
        os.getenv('POSTGRES_URL') or 
        os.getenv('DATABASE_URL')
    )
    
    if not database_url:
        print("❌ DATABASE_URL не установлен!")
        print("Убедитесь, что установлена переменная POSTGRES_URL или POSTGRES_PRISMA_URL")
        return
    
    # Удаляем параметры pgbouncer из URL если есть (для миграций нужен прямой доступ)
    # Используем POSTGRES_URL_NON_POOLING если доступен
    conn_url = os.getenv('POSTGRES_URL_NON_POOLING') or database_url.replace('?pgbouncer=true', '').split('?')[0]
    
    print(f"🔗 Подключение к базе данных...")
    
    try:
        conn = await asyncpg.connect(conn_url)
        print("✅ Подключение установлено")
        
        # Читаем SQL миграцию
        migration_file = 'migrations/001_create_tables.sql'
        if not os.path.exists(migration_file):
            print(f"❌ Файл миграции {migration_file} не найден!")
            await conn.close()
            return
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        print(f"📝 Применение миграции из {migration_file}...")
        
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
            print(f"\n✅ Создано таблиц: {len(tables)}")
            for table in tables:
                print(f"   - {table['table_name']}")
        else:
            print("⚠️ Таблицы не найдены. Возможно, они уже существуют или произошла ошибка.")
        
        await conn.close()
        print("\n✅ Готово!")
        
    except Exception as e:
        print(f"❌ Ошибка при применении миграции: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(apply_migration())

