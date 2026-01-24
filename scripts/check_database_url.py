"""
Проверка и помощь в исправлении SUPABASE_DB_URL
"""
import os
import sys
from dotenv import load_dotenv
from urllib.parse import urlparse, quote_plus

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def check_db_url():
    """Проверяет и анализирует SUPABASE_DB_URL"""
    print("="*60)
    print("ПРОВЕРКА SUPABASE_DB_URL")
    print("="*60)
    print()
    
    db_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL не установлен!")
        return False
    
    print(f"📋 Текущий SUPABASE_DB_URL:")
    # Маскируем пароль для безопасности
    try:
        parsed = urlparse(db_url)
        if '@' in parsed.netloc:
            auth_part = parsed.netloc.split('@')[0]
            host_part = parsed.netloc.split('@')[1]
            if ':' in auth_part:
                username, password = auth_part.split(':', 1)
                masked_url = f"{parsed.scheme}://{username}:***@{host_part}{parsed.path}"
                print(f"   {masked_url}")
            else:
                print(f"   {db_url[:80]}...")
        else:
            print(f"   {db_url[:80]}...")
    except:
        print(f"   {db_url[:80]}...")
    
    print()
    
    # Анализируем URL
    try:
        parsed = urlparse(db_url)
        
        print("🔍 Анализ URL:")
        print(f"   Схема: {parsed.scheme}")
        print(f"   Хост: {parsed.netloc.split('@')[-1] if '@' in parsed.netloc else parsed.netloc}")
        
        # Проверяем формат
        issues = []
        
        if parsed.scheme != 'postgresql' and parsed.scheme != 'postgres':
            issues.append(f"⚠️ Неправильная схема: {parsed.scheme} (должно быть postgresql или postgres)")
        
        if '@' not in parsed.netloc:
            issues.append("⚠️ URL не содержит учетные данные (user:password@host)")
        
        if '@' in parsed.netloc:
            auth = parsed.netloc.split('@')[0]
            if ':' not in auth:
                issues.append("⚠️ URL не содержит пароль (формат: user:password@host)")
            else:
                username, password = auth.split(':', 1)
                if not password or password == '':
                    issues.append("⚠️ Пароль пустой!")
                if '[' in password or ']' in password:
                    issues.append("⚠️ Пароль содержит незамененные плейсхолдеры [PASSWORD]")
        
        # Проверяем формат Supabase
        host = parsed.netloc.split('@')[-1] if '@' in parsed.netloc else parsed.netloc
        if 'supabase.co' not in host and 'pooler.supabase.com' not in host:
            issues.append("⚠️ Хост не похож на Supabase")
        
        if issues:
            print("\n❌ Обнаружены проблемы:")
            for issue in issues:
                print(f"   {issue}")
        else:
            print("\n✅ Формат URL выглядит корректно")
        
        # Проверяем, что это Supabase проект
        supabase_url = os.getenv('SUPABASE_URL', '')
        if supabase_url:
            project_id = supabase_url.split('//')[1].split('.')[0] if '//' in supabase_url else ''
            if project_id and project_id in db_url:
                print(f"✅ URL содержит ID проекта: {project_id}")
            else:
                print(f"⚠️ URL может не соответствовать проекту: {project_id}")
        
    except Exception as e:
        print(f"\n❌ Ошибка при анализе URL: {e}")
        return False
    
    print()
    print("="*60)
    print("💡 РЕКОМЕНДАЦИИ")
    print("="*60)
    print()
    print("Если подключение не работает, проверьте:")
    print()
    print("1. Пароль базы данных:")
    print("   • Откройте Supabase Dashboard → Settings → Database")
    print("   • Проверьте 'Database password'")
    print("   • Если пароль забыт, нажмите 'Reset database password'")
    print()
    print("2. Формат строки подключения:")
    print("   Direct connection:")
    print("   postgresql://postgres:ВАШ_ПАРОЛЬ@db.xxx.supabase.co:5432/postgres")
    print()
    print("   Connection pooling:")
    print("   postgresql://postgres.xxx:ВАШ_ПАРОЛЬ@aws-0-xxx.pooler.supabase.com:6543/postgres?pgbouncer=true")
    print()
    print("3. Специальные символы в пароле:")
    print("   • Если пароль содержит @, #, % и т.д., они должны быть URL-encoded")
    print("   • Используйте функцию quote_plus() для кодирования")
    print()
    print("4. Альтернативный способ:")
    print("   • Примените миграцию через Supabase Dashboard → SQL Editor")
    print("   • Скопируйте SQL из migrations/001_create_tables.sql")
    print("   • Вставьте и выполните")
    print()
    
    return len(issues) == 0

if __name__ == '__main__':
    check_db_url()
