"""
Скрипт для применения миграции через Supabase CLI
"""
import os
import sys
import subprocess
from dotenv import load_dotenv

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def apply_migration_via_cli():
    """Применяет миграцию через Supabase CLI"""
    
    print("=" * 60)
    print("🚀 Применение миграции через Supabase CLI")
    print("=" * 60)
    print()
    
    # Проверяем, установлен ли Supabase CLI
    try:
        result = subprocess.run(
            ['supabase', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("❌ Supabase CLI не найден или не работает")
            print("\n💡 Установите Supabase CLI:")
            print("   scoop install supabase")
            return False
        
        print(f"✅ Supabase CLI найден: {result.stdout.strip()}")
        print()
        
    except FileNotFoundError:
        print("❌ Supabase CLI не установлен")
        print("\n💡 Установите Supabase CLI:")
        print("   scoop install supabase")
        return False
    except Exception as e:
        print(f"❌ Ошибка при проверке Supabase CLI: {e}")
        return False
    
    # Получаем настройки
    supabase_url = os.getenv('SUPABASE_URL', '').rstrip('/')
    supabase_db_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL', '')
    
    if not supabase_url:
        print("❌ SUPABASE_URL не установлен в .env")
        return False
    
    print(f"🔗 Supabase URL: {supabase_url}")
    
    # Проверяем наличие файла миграции
    migration_file = 'migrations/001_create_tables.sql'
    if not os.path.exists(migration_file):
        print(f"❌ Файл миграции {migration_file} не найден!")
        return False
    
    print(f"📝 Файл миграции: {migration_file}")
    print()
    
    # Вариант 1: Использовать supabase db push (если проект связан)
    print("📌 Вариант 1: Применение через supabase db push")
    print("   (требует предварительной настройки: supabase login и supabase link)")
    print()
    
    # Вариант 2: Использовать psql напрямую (если установлен)
    if supabase_db_url:
        print("📌 Вариант 2: Применение через psql (прямое подключение)")
        print(f"   Используется: SUPABASE_DB_URL")
        print()
        
        try:
            # Проверяем, установлен ли psql
            psql_check = subprocess.run(
                ['psql', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if psql_check.returncode == 0:
                print(f"✅ psql найден: {psql_check.stdout.strip()}")
                print()
                print("🔧 Применение миграции через psql...")
                
                # Читаем SQL
                with open(migration_file, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # Выполняем через psql
                result = subprocess.run(
                    ['psql', supabase_db_url, '-f', migration_file],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    print("✅ Миграция успешно применена через psql!")
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
                    return False
            else:
                print("⚠️ psql не найден")
                print("💡 Установите PostgreSQL client для использования этого варианта")
                print()
        except FileNotFoundError:
            print("⚠️ psql не установлен")
            print("💡 Установите PostgreSQL client:")
            print("   - Windows: choco install postgresql")
            print("   - Или скачайте с https://www.postgresql.org/download/windows/")
            print()
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            print()
    
    # Вариант 3: Инструкции для ручного применения
    print("📌 Вариант 3: Ручное применение через Supabase CLI")
    print()
    print("Выполните следующие команды:")
    print()
    print("1. Войдите в Supabase:")
    print("   supabase login")
    print()
    print("2. Свяжите проект (получите project-ref из URL вашего проекта):")
    print(f"   supabase link --project-ref <project-ref>")
    print("   (project-ref - это часть URL после /project/)")
    print()
    print("3. Примените миграцию:")
    print("   supabase db push")
    print()
    print("Или используйте прямое подключение к БД:")
    if supabase_db_url:
        print(f"   supabase db push --db-url \"{supabase_db_url}\"")
    else:
        print("   supabase db push --db-url \"YOUR_DATABASE_URL\"")
    print()
    
    return False


if __name__ == '__main__':
    success = apply_migration_via_cli()
    sys.exit(0 if success else 1)
