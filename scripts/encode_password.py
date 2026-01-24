"""
Скрипт для правильного кодирования пароля и обновления SUPABASE_DB_URL
"""
import os
import sys
from dotenv import load_dotenv
from urllib.parse import quote_plus, urlparse, urlunparse

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

def encode_password_in_url(db_url):
    """Кодирует пароль в URL строке подключения"""
    try:
        parsed = urlparse(db_url)
        
        if '@' not in parsed.netloc:
            print("⚠️ URL не содержит учетные данные")
            return db_url
        
        # Разделяем на auth и host
        auth_part = parsed.netloc.split('@')[0]
        host_part = parsed.netloc.split('@')[1]
        
        if ':' not in auth_part:
            print("⚠️ URL не содержит пароль")
            return db_url
        
        # Разделяем username и password
        username, password = auth_part.split(':', 1)
        
        # Кодируем пароль
        encoded_password = quote_plus(password)
        
        # Собираем обратно
        new_netloc = f"{username}:{encoded_password}@{host_part}"
        
        # Создаем новый URL
        new_url = urlunparse((
            parsed.scheme,
            new_netloc,
            parsed.path,
            parsed.params,
            parsed.query,
            parsed.fragment
        ))
        
        return new_url
    except Exception as e:
        print(f"❌ Ошибка при обработке URL: {e}")
        return db_url

def main():
    """Главная функция"""
    print("="*60)
    print("КОДИРОВАНИЕ ПАРОЛЯ В SUPABASE_DB_URL")
    print("="*60)
    print()
    
    # Получаем текущий URL
    db_url = os.getenv('SUPABASE_DB_URL') or os.getenv('DATABASE_URL')
    
    if not db_url:
        print("❌ SUPABASE_DB_URL не установлен!")
        print("\n💡 Сначала добавьте SUPABASE_DB_URL в .env файл")
        return
    
    print("📋 Текущий SUPABASE_DB_URL (пароль замаскирован):")
    try:
        parsed = urlparse(db_url)
        if '@' in parsed.netloc:
            auth = parsed.netloc.split('@')[0]
            host = parsed.netloc.split('@')[1]
            if ':' in auth:
                username, password = auth.split(':', 1)
                masked = f"{parsed.scheme}://{username}:***@{host}{parsed.path}"
                print(f"   {masked}")
            else:
                print(f"   {db_url[:80]}...")
        else:
            print(f"   {db_url[:80]}...")
    except:
        print(f"   {db_url[:80]}...")
    
    print()
    print("🔄 Кодирую пароль...")
    
    # Кодируем пароль
    encoded_url = encode_password_in_url(db_url)
    
    if encoded_url == db_url:
        print("⚠️ URL не изменился (возможно, пароль уже закодирован или нет пароля)")
    else:
        print("✅ Пароль закодирован!")
        print()
        print("📋 Новый SUPABASE_DB_URL (пароль замаскирован):")
        try:
            parsed = urlparse(encoded_url)
            if '@' in parsed.netloc:
                auth = parsed.netloc.split('@')[0]
                host = parsed.netloc.split('@')[1]
                if ':' in auth:
                    username, password = auth.split(':', 1)
                    masked = f"{parsed.scheme}://{username}:***@{host}{parsed.path}"
                    print(f"   {masked}")
                else:
                    print(f"   {encoded_url[:80]}...")
            else:
                print(f"   {encoded_url[:80]}...")
        except:
            print(f"   {encoded_url[:80]}...")
        
        print()
        print("="*60)
        print("📝 ОБНОВИТЕ .env ФАЙЛ")
        print("="*60)
        print()
        print("Добавьте или обновите следующую строку в .env:")
        print()
        print(f"SUPABASE_DB_URL={encoded_url}")
        print()
        print("💡 После обновления .env файла:")
        print("   1. Сохраните файл")
        print("   2. Запустите: python scripts/apply_migration.py")
        print()
        
        # Показываем, какие символы были закодированы
        try:
            parsed_old = urlparse(db_url)
            parsed_new = urlparse(encoded_url)
            if '@' in parsed_old.netloc and '@' in parsed_new.netloc:
                old_auth = parsed_old.netloc.split('@')[0]
                new_auth = parsed_new.netloc.split('@')[0]
                if ':' in old_auth and ':' in new_auth:
                    old_pass = old_auth.split(':', 1)[1]
                    new_pass = new_auth.split(':', 1)[1]
                    if old_pass != new_pass:
                        print("📊 Информация о кодировании:")
                        print(f"   Исходный пароль: {old_pass[:20]}...")
                        print(f"   Закодированный: {new_pass[:30]}...")
                        print()
                        # Показываем, какие символы были закодированы
                        special_chars = []
                        for char in old_pass:
                            if char in ['@', '#', '%', '&', '+', '=', '?', '/', ':', ';', ' ']:
                                special_chars.append(char)
                        if special_chars:
                            print(f"   Закодированные символы: {', '.join(set(special_chars))}")
                        else:
                            print("   Символы '_' и '.' не требуют кодирования, но пароль закодирован для безопасности")
        except:
            pass
    
    print()
    print("="*60)
    print("💡 ПРИМЕЧАНИЕ")
    print("="*60)
    print()
    print("Символы '_' (подчеркивание) и '.' (точка) обычно НЕ требуют")
    print("кодирования в URL, но кодирование всего пароля - это хорошая")
    print("практика для безопасности и избежания проблем с парсингом.")
    print()
    print("Если после кодирования подключение все еще не работает:")
    print("1. Проверьте, что пароль правильный в Supabase Dashboard")
    print("2. Попробуйте сбросить пароль: Settings → Database → Reset password")
    print("3. Или используйте способ через Supabase Dashboard SQL Editor")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
