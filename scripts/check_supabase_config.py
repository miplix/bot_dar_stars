"""
Скрипт для проверки настроек Supabase и получения инструкций
"""
import os
import sys
from dotenv import load_dotenv

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def check_supabase_config():
    """Проверяет настройки Supabase и выдает инструкции"""
    print("=" * 60)
    print("🔍 ПРОВЕРКА НАСТРОЕК SUPABASE")
    print("=" * 60)
    print()
    
    # Проверяем SUPABASE_URL
    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    if supabase_url:
        print(f"✅ SUPABASE_URL: {supabase_url}")
    else:
        print("❌ SUPABASE_URL: не установлен")
        print("   Добавьте в .env: SUPABASE_URL=https://xxx.supabase.co")
        return
    
    # Проверяем SUPABASE_API_KEY
    supabase_api_key = os.getenv('SUPABASE_API_KEY') or os.getenv('SUPABASE_ANON_KEY', '')
    if supabase_api_key:
        masked_key = supabase_api_key[:20] + "..." if len(supabase_api_key) > 20 else "***"
        print(f"✅ SUPABASE_API_KEY: {masked_key}")
    else:
        print("❌ SUPABASE_API_KEY: не установлен")
        print("   Добавьте в .env: SUPABASE_API_KEY=<your-api-key>")
    
    # Проверяем SUPABASE_DB_URL
    supabase_db_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL', '')
    if supabase_db_url:
        # Маскируем пароль в URL
        if '@' in supabase_db_url:
            parts = supabase_db_url.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                if len(user_pass) == 2:
                    masked_url = f"{user_pass[0]}:***@{parts[1]}"
                else:
                    masked_url = supabase_db_url
            else:
                masked_url = supabase_db_url
        else:
            masked_url = supabase_db_url
        print(f"✅ SUPABASE_DB_URL: {masked_url}")
        print()
        print("🎉 Все настройки Supabase установлены!")
        print("   Теперь можно применить миграцию: python scripts/apply_migration.py")
    else:
        print("❌ SUPABASE_DB_URL: не установлен")
        print()
        print("=" * 60)
        print("📋 ИНСТРУКЦИЯ: Как получить SUPABASE_DB_URL")
        print("=" * 60)
        print()
        print("Для применения миграций нужен прямой доступ к PostgreSQL.")
        print("Получите Connection String из Supabase Dashboard:")
        print()
        print("1️⃣  Откройте Supabase Dashboard:")
        print(f"   https://supabase.com/dashboard/project/{supabase_url.split('//')[1].split('.')[0] if '//' in supabase_url else ''}")
        print()
        print("2️⃣  Перейдите в Settings → Database")
        print()
        print("3️⃣  Найдите раздел 'Connection string' или 'Connection pooling'")
        print()
        print("4️⃣  Скопируйте Connection String (URI) - формат:")
        print("    postgresql://postgres:[YOUR-PASSWORD]@db.xxx.supabase.co:5432/postgres")
        print()
        print("5️⃣  Добавьте в .env файл:")
        print("    SUPABASE_DB_URL=postgresql://postgres:ВАШ_ПАРОЛЬ@db.xxx.supabase.co:5432/postgres")
        print()
        print("⚠️  ВАЖНО:")
        print("   - Если пароль содержит специальные символы, они должны быть закодированы")
        print("   - Используйте URI формат (не Connection Pooling для миграций)")
        print()
        print("💡 Альтернативный способ применения миграции:")
        print("   1. Откройте Supabase Dashboard → SQL Editor")
        print("   2. Скопируйте содержимое файла: migrations/001_create_tables.sql")
        print("   3. Вставьте и выполните SQL в редакторе")
        print()
    
    print("=" * 60)

if __name__ == '__main__':
    check_supabase_config()
