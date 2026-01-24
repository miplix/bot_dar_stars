"""
Скрипт для применения миграции через Supabase CLI
"""
import os
import sys
import subprocess
from urllib.parse import quote_plus, urlparse, urlunparse
from dotenv import load_dotenv

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def encode_db_url(url: str) -> str:
    """Кодирует пароль в URL для безопасной передачи"""
    try:
        parsed = urlparse(url)
        if '@' in parsed.netloc and ':' in parsed.netloc.split('@')[0]:
            auth_part = parsed.netloc.split('@')[0]
            username, password = auth_part.split(':', 1)
            # Кодируем пароль
            encoded_password = quote_plus(password)
            # Пересобираем URL
            new_netloc = f"{username}:{encoded_password}@{parsed.netloc.split('@')[1]}"
            return urlunparse((
                parsed.scheme,
                new_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
    except Exception:
        pass
    return url

def apply_migration():
    """Применяет миграцию через Supabase CLI"""
    
    print("=" * 60)
    print("🚀 Применение миграции через Supabase CLI")
    print("=" * 60)
    print()
    
    # Проверяем Supabase CLI
    try:
        result = subprocess.run(
            ['supabase', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print("❌ Supabase CLI не найден")
            return False
        print(f"✅ Supabase CLI: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ Supabase CLI не установлен")
        print("💡 Установите: scoop install supabase")
        return False
    
    # Получаем URL базы данных
    db_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL', '')
    if not db_url:
        print("❌ SUPABASE_DB_URL не установлен в .env")
        return False
    
    # Кодируем URL для безопасной передачи
    encoded_url = encode_db_url(db_url)
    
    print(f"🔗 Подключение к базе данных...")
    print(f"   URL: {db_url.split('@')[0]}@...")  # Не показываем полный URL с паролем
    
    # Проверяем наличие папки supabase/migrations
    migration_file = 'supabase/migrations/20240101000000_create_tables.sql'
    if not os.path.exists(migration_file):
        # Создаем структуру, если её нет
        os.makedirs('supabase/migrations', exist_ok=True)
        # Копируем миграцию
        if os.path.exists('migrations/001_create_tables.sql'):
            with open('migrations/001_create_tables.sql', 'r', encoding='utf-8') as f:
                content = f.read()
            with open(migration_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Миграция скопирована в {migration_file}")
        else:
            print("❌ Файл migrations/001_create_tables.sql не найден")
            return False
    
    print(f"📝 Применение миграции: {migration_file}")
    print()
    
    # Применяем миграцию через Supabase CLI
    try:
        print("🔧 Выполнение: supabase db push --db-url ...")
        result = subprocess.run(
            ['supabase', 'db', 'push', '--db-url', encoded_url],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=os.getcwd()
        )
        
        if result.returncode == 0:
            print("✅ Миграция успешно применена через Supabase CLI!")
            if result.stdout:
                print("\nВывод:")
                print(result.stdout)
            return True
        else:
            print("❌ Ошибка при применении миграции:")
            if result.stderr:
                print(result.stderr)
            if result.stdout:
                print(result.stdout)
            
            # Если ошибка подключения, предлагаем альтернативы
            if 'failed to connect' in result.stderr.lower() or 'no such host' in result.stderr.lower():
                print("\n💡 Проблема с подключением к базе данных")
                print("   Попробуйте:")
                print("   1. Проверьте правильность SUPABASE_DB_URL")
                print("   2. Используйте прямой PostgreSQL подключение: python scripts/apply_migration.py")
                print("   3. Примените миграцию через Supabase Dashboard → SQL Editor")
            
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Таймаут при выполнении команды")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)
