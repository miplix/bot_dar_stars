"""
Скрипт для применения миграции через Supabase Dashboard
Выводит SQL для копирования в SQL Editor
"""
import os
from pathlib import Path

def main():
    print("=" * 60)
    print("Применение миграции через Supabase Dashboard")
    print("=" * 60)
    print("\nИнструкция:")
    print("1. Откройте https://supabase.com/dashboard")
    print("2. Выберите ваш проект")
    print("3. Перейдите в SQL Editor (левое меню)")
    print("4. Скопируйте SQL ниже и вставьте в редактор")
    print("5. Нажмите Run для выполнения")
    print("\n" + "=" * 60)
    print("SQL для выполнения:")
    print("=" * 60)
    print()
    
    # Читаем файл миграции
    migration_file = Path('migrations/001_create_tables.sql')
    if migration_file.exists():
        sql = migration_file.read_text(encoding='utf-8')
        print(sql)
        print()
        print("=" * 60)
        print("Скопируйте SQL выше и выполните в Supabase Dashboard")
        print("=" * 60)
    else:
        print(f"❌ Файл миграции {migration_file} не найден!")

if __name__ == '__main__':
    main()
