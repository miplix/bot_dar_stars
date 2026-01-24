"""
Скрипт для применения миграции к Supabase через Management API
Использует HTTP запросы для выполнения SQL через Supabase API
"""
import os
import sys
import requests
from dotenv import load_dotenv

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def apply_migration_via_api():
    """Применяет миграцию через Supabase Management API"""
    print("🚀 Применение миграции к Supabase через API")
    print("=" * 60)
    
    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    supabase_api_key = os.getenv('SUPABASE_API_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
    
    if not supabase_url or not supabase_api_key:
        print("❌ SUPABASE_URL или SUPABASE_API_KEY не установлены!")
        print("\nУбедитесь, что установлены переменные в .env:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_API_KEY")
        return
    
    print(f"\n🔗 Подключение к Supabase...")
    print(f"   URL: {supabase_url}")
    
    # Читаем SQL миграцию
    migration_file = 'migrations/001_create_tables.sql'
    if not os.path.exists(migration_file):
        print(f"❌ Файл миграции {migration_file} не найден!")
        return
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"\n📝 Применение миграции из {migration_file}...")
    
    # Supabase Management API endpoint для выполнения SQL
    # Используем PostgREST для выполнения SQL через RPC
    # Но для произвольного SQL нужен service_role ключ и специальная настройка
    
    # Альтернативный способ: используем Supabase Dashboard API
    # Но это требует специальных прав
    
    # Самый простой способ: используем Supabase Python клиент для создания RPC функции
    # Или выполняем SQL через Supabase Dashboard API
    
    try:
        # Пробуем использовать Supabase Python клиент
        from supabase import create_client, Client
        
        print("🔧 Попытка применения через Supabase Python клиент...")
        supabase: Client = create_client(supabase_url, supabase_api_key)
        
        # Supabase Python клиент не поддерживает произвольный SQL напрямую
        # Но можно попробовать через RPC функцию
        
        # Разбиваем SQL на отдельные команды
        sql_commands = [cmd.strip() for cmd in sql.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
        
        print("⚠️ Supabase Python клиент не поддерживает выполнение произвольного SQL")
        print("💡 Для применения миграций через API нужен service_role ключ и настройка RPC функции")
        print("\n📌 Рекомендуемый способ:")
        print("   1. Откройте Supabase Dashboard: https://supabase.com/dashboard")
        print("   2. Выберите ваш проект")
        print("   3. Перейдите в SQL Editor")
        print("   4. Скопируйте содержимое файла: migrations/001_create_tables.sql")
        print("   5. Вставьте SQL в редактор и нажмите Run")
        
        # Показываем SQL для копирования
        print("\n" + "=" * 60)
        print("📋 SQL для копирования в Supabase Dashboard:")
        print("=" * 60)
        print(sql)
        print("=" * 60)
        
        return False
        
    except ImportError:
        print("❌ Supabase Python клиент не установлен!")
        print("\n💡 Установите: pip install supabase")
        print("\n📌 Альтернативный способ:")
        print("   1. Откройте Supabase Dashboard → SQL Editor")
        print("   2. Скопируйте содержимое: migrations/001_create_tables.sql")
        print("   3. Вставьте и выполните SQL")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        print("\n📌 Альтернативный способ:")
        print("   1. Откройте Supabase Dashboard → SQL Editor")
        print("   2. Скопируйте содержимое: migrations/001_create_tables.sql")
        print("   3. Вставьте и выполните SQL")
        return False

def apply_migration_via_http():
    """Попытка применения миграции через HTTP запросы к Supabase Management API"""
    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    supabase_api_key = os.getenv('SUPABASE_API_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
    
    if not supabase_url or not supabase_api_key:
        return False
    
    # Читаем SQL миграцию
    migration_file = 'migrations/001_create_tables.sql'
    if not os.path.exists(migration_file):
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    # Supabase Management API для выполнения SQL
    # Это требует service_role ключ и специальных настроек
    # Обычный anon ключ не имеет прав на выполнение произвольного SQL
    
    # Проверяем, является ли ключ service_role
    # service_role ключ обычно длиннее и имеет другую структуру
    
    headers = {
        'apikey': supabase_api_key,
        'Authorization': f'Bearer {supabase_api_key}',
        'Content-Type': 'application/json'
    }
    
    # Пробуем использовать PostgREST для выполнения SQL
    # Но это не работает напрямую для произвольного SQL
    
    print("⚠️ Выполнение SQL через HTTP API требует service_role ключ")
    print("   и специальной настройки Supabase")
    
    return False

if __name__ == '__main__':
    apply_migration_via_api()
