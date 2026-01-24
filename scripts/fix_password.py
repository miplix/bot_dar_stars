"""
Скрипт для проверки и исправления пароля в SUPABASE_DB_URL
"""
import os
import sys
from dotenv import load_dotenv
from urllib.parse import urlparse, quote_plus, urlunparse

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def analyze_password():
    """Анализирует пароль в URL"""
    print("="*60)
    print("АНАЛИЗ ПАРОЛЯ В SUPABASE_DB_URL")
    print("="*60)
    print()
    
    db_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL не установлен!")
        return
    
    try:
        parsed = urlparse(db_url)
        
        if '@' not in parsed.netloc:
            print("❌ URL не содержит учетные данные (user:password@host)")
            print("\n💡 Формат должен быть:")
            print("   postgresql://postgres:ПАРОЛЬ@db.xxx.supabase.co:5432/postgres")
            return
        
        auth_part = parsed.netloc.split('@')[0]
        host_part = parsed.netloc.split('@')[1]
        
        if ':' not in auth_part:
            print("❌ URL не содержит пароль")
            print("\n💡 Формат должен быть:")
            print("   postgresql://postgres:ПАРОЛЬ@db.xxx.supabase.co:5432/postgres")
            return
        
        username, password = auth_part.split(':', 1)
        
        print(f"✅ Username: {username}")
        print(f"📋 Пароль: {'***' if password else '❌ ОТСУТСТВУЕТ'}")
        
        if not password:
            print("\n❌ ПАРОЛЬ ОТСУТСТВУЕТ В URL!")
            print("\n💡 Решение:")
            print("   1. Откройте Supabase Dashboard → Settings → Database")
            print("   2. Найдите 'Database password' или нажмите 'Reset database password'")
            print("   3. Обновите SUPABASE_DB_URL в .env:")
            print("      SUPABASE_DB_URL=postgresql://postgres:ВАШ_ПАРОЛЬ@db.xxx.supabase.co:5432/postgres")
            return
        
        # Проверяем длину пароля
        if len(password) < 8:
            print(f"⚠️ Пароль очень короткий ({len(password)} символов)")
        
        # Проверяем специальные символы
        special_chars = []
        for char in password:
            if char in ['@', '#', '%', '&', '+', '=', '?', '/', ':', ';', ' ']:
                special_chars.append(char)
        
        if special_chars:
            print(f"⚠️ Пароль содержит специальные символы: {', '.join(set(special_chars))}")
            print("   Эти символы могут требовать URL-кодирования")
        else:
            print("✅ Пароль содержит только безопасные символы (_, ., буквы, цифры)")
        
        # Проверяем, закодирован ли пароль
        decoded = password
        try:
            # Пробуем декодировать
            from urllib.parse import unquote_plus
            decoded = unquote_plus(password)
            if decoded != password:
                print(f"✅ Пароль закодирован (длина: {len(password)} символов)")
                print(f"   Декодированный: {decoded[:20]}...")
            else:
                print("ℹ️ Пароль не закодирован (это нормально для _, ., букв, цифр)")
        except:
            pass
        
        print()
        print("="*60)
        print("💡 РЕКОМЕНДАЦИИ")
        print("="*60)
        print()
        
        # Если пароль не закодирован и содержит только безопасные символы
        if not special_chars:
            print("Символы '_' и '.' НЕ требуют кодирования.")
            print("Проблема скорее всего в другом:")
            print()
            print("1. ❓ Пароль неправильный?")
            print("   • Проверьте пароль в Supabase Dashboard")
            print("   • Settings → Database → Database password")
            print("   • Или сбросьте: Reset database password")
            print()
            print("2. ❓ Проблемы с сетью?")
            print("   • Проверьте интернет-соединение")
            print("   • Попробуйте подключиться через Supabase Dashboard")
            print()
            print("3. ❓ Неправильный формат URL?")
            print("   • Убедитесь, что используется Direct connection")
            print("   • Формат: postgresql://postgres:ПАРОЛЬ@db.xxx.supabase.co:5432/postgres")
            print()
            print("4. ✅ Лучшее решение:")
            print("   • Примените миграцию через Supabase Dashboard → SQL Editor")
            print("   • Это работает всегда, независимо от пароля!")
        else:
            print("Пароль содержит специальные символы, которые могут требовать кодирования.")
            print("Попробуйте закодировать пароль:")
            print()
            encoded_password = quote_plus(password)
            new_netloc = f"{username}:{encoded_password}@{host_part}"
            new_url = urlunparse((
                parsed.scheme,
                new_netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                parsed.fragment
            ))
            print("Обновите .env:")
            print(f"SUPABASE_DB_URL={new_url}")
        
    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    try:
        analyze_password()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
