"""
Скрипт для применения миграции к Supabase через Management API (HTTP)
Использует прямой HTTP запрос к Supabase для выполнения SQL
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

def apply_migration_via_http():
    """Применяет миграцию через Supabase Management API (HTTP)"""
    print("🚀 Применение миграции к Supabase через Management API")
    print("=" * 60)
    
    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_API_KEY')
    
    if not supabase_service_key:
        print("❌ SUPABASE_SERVICE_ROLE_KEY не найден!")
        print("\n💡 Для выполнения SQL через API нужен Service Role Key")
        print("   Получите его из Supabase Dashboard → Settings → API → service_role key")
        return False
    
    if not supabase_url:
        print("❌ SUPABASE_URL не найден!")
        return False
    
    # Читаем SQL миграцию
    migration_file = 'migrations/001_create_tables.sql'
    if not os.path.exists(migration_file):
        print(f"❌ Файл миграции {migration_file} не найден!")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    print(f"📝 Чтение миграции из {migration_file}...")
    print(f"   Размер SQL: {len(sql)} символов")
    
    # Очищаем SQL от комментариев
    sql_clean = []
    for line in sql.split('\n'):
        line = line.strip()
        if line and not line.startswith('--'):
            sql_clean.append(line)
    
    full_sql = ' '.join(sql_clean)
    
    print("\n🔧 Попытка выполнения SQL через Supabase Management API...")
    print(f"   URL: {supabase_url}")
    
    # Пробуем использовать Supabase Management API
    # Для выполнения SQL через API нужно использовать RPC функцию или прямой запрос
    
    # Вариант 1: Пробуем через RPC функцию exec_sql (если она существует)
    try:
        print("\n📡 Попытка 1: Вызов RPC функции exec_sql...")
        
        rpc_url = f"{supabase_url}/rest/v1/rpc/exec_sql"
        headers = {
            'apikey': supabase_service_key,
            'Authorization': f'Bearer {supabase_service_key}',
            'Content-Type': 'application/json',
            'Prefer': 'return=representation'
        }
        
        payload = {
            'sql_text': full_sql
        }
        
        response = requests.post(rpc_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200 or response.status_code == 201:
            result = response.json()
            if isinstance(result, dict):
                if result.get('status') == 'success':
                    print("   ✅ SQL успешно выполнен через RPC функцию!")
                    print(f"   Сообщение: {result.get('message', '')}")
                    return True
                elif result.get('status') == 'error':
                    print(f"   ❌ Ошибка: {result.get('message', '')}")
                    return False
            print("   ✅ SQL успешно выполнен!")
            return True
        elif response.status_code == 404:
            print("   ⚠️ RPC функция exec_sql не найдена")
            print("   💡 Нужно создать функцию exec_sql в Supabase")
        else:
            print(f"   ⚠️ Ошибка HTTP {response.status_code}: {response.text[:200]}")
    except Exception as e:
        print(f"   ⚠️ Ошибка при вызове RPC: {e}")
    
    # Вариант 2: Пробуем через Supabase SQL Editor API (если доступен)
    # Это требует специальных прав и может не работать для всех проектов
    print("\n📡 Попытка 2: Прямое выполнение SQL через Management API...")
    print("   ⚠️ Этот метод может не работать для всех проектов")
    print("   💡 Рекомендуется создать функцию exec_sql в Supabase Dashboard")
    
    print("\n" + "=" * 60)
    print("❌ Не удалось применить миграцию через HTTP API")
    print("\n💡 Решение:")
    print("   1. Создайте функцию exec_sql в Supabase Dashboard:")
    print("      - Откройте Supabase Dashboard → SQL Editor")
    print("      - Выполните следующий SQL:")
    print("\n" + "-" * 60)
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
    print("-" * 60)
    print("\n   2. После создания функции запустите скрипт снова")
    print("\n   ИЛИ примените миграцию вручную:")
    print("   - Откройте Supabase Dashboard → SQL Editor")
    print(f"   - Скопируйте содержимое файла: {migration_file}")
    print("   - Вставьте и выполните SQL в редакторе")
    
    return False

if __name__ == '__main__':
    success = apply_migration_via_http()
    sys.exit(0 if success else 1)
