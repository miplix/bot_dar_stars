"""
Диагностика подключения к Supabase
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

def diagnose_connection():
    """Диагностика подключения к Supabase"""
    print("=" * 60)
    print("ДИАГНОСТИКА ПОДКЛЮЧЕНИЯ К SUPABASE")
    print("=" * 60)
    print()
    
    # Проверяем переменные окружения
    supabase_url = os.getenv('SUPABASE_URL', '')
    supabase_key = os.getenv('SUPABASE_API_KEY', '') or os.getenv('SUPABASE_ANON_KEY', '')
    database_url = os.getenv('SUPABASE_DB_URL', '') or os.getenv('DATABASE_URL', '')
    
    print("📋 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    print(f"   SUPABASE_URL: {'✅ Установлен' if supabase_url else '❌ Не установлен'}")
    if supabase_url:
        print(f"      Значение: {supabase_url}")
    
    print(f"   SUPABASE_API_KEY: {'✅ Установлен' if supabase_key else '❌ Не установлен'}")
    if supabase_key:
        key_type = "service_role" if "service_role" in supabase_key or len(supabase_key) > 100 else "anon"
        print(f"      Тип: {key_type}")
        print(f"      Длина: {len(supabase_key)} символов")
    
    print(f"   SUPABASE_DB_URL: {'✅ Установлен' if database_url else '❌ Не установлен'}")
    if database_url:
        # Парсим URL и показываем информацию
        try:
            parsed = urlparse(database_url)
            
            # Маскируем пароль
            if '@' in parsed.netloc:
                auth_part = parsed.netloc.split('@')[0]
                host_part = parsed.netloc.split('@')[1]
                if ':' in auth_part:
                    username, password = auth_part.split(':', 1)
                    masked_url = f"{parsed.scheme}://{username}:***@{host_part}{parsed.path}"
                else:
                    masked_url = f"{parsed.scheme}://***@{host_part}{parsed.path}"
            else:
                masked_url = database_url[:80] + "..." if len(database_url) > 80 else database_url
            
            print(f"      URL (замаскирован): {masked_url}")
            print(f"      Схема: {parsed.scheme}")
            
            if '@' in parsed.netloc:
                host = parsed.netloc.split('@')[1].split(':')[0]
                print(f"      Хост: {host}")
                
                # Проверяем формат хоста
                if 'db.' in host and '.supabase.co' in host:
                    print(f"      ✅ Формат Direct connection обнаружен")
                elif 'pooler.supabase.com' in host:
                    print(f"      ✅ Формат Connection pooling обнаружен")
                else:
                    print(f"      ⚠️ Нестандартный формат хоста")
                
                # Проверяем порт
                if ':' in parsed.netloc.split('@')[1]:
                    port = parsed.netloc.split('@')[1].split(':')[1].split('/')[0]
                    print(f"      Порт: {port}")
                else:
                    print(f"      Порт: не указан (по умолчанию)")
            
            print(f"      Путь: {parsed.path}")
            
            # Проверяем параметры
            if parsed.query:
                print(f"      Параметры: {parsed.query}")
                if 'pgbouncer=true' in parsed.query:
                    print(f"      ⚠️ Используется pgbouncer - для миграций нужен прямой доступ")
            
        except Exception as e:
            print(f"      ⚠️ Ошибка при парсинге URL: {e}")
    
    print()
    print("=" * 60)
    print("РЕКОМЕНДАЦИИ:")
    print("=" * 60)
    print()
    
    if not supabase_url:
        print("❌ SUPABASE_URL не установлен")
        print("   Добавьте в .env: SUPABASE_URL=https://ваш-проект.supabase.co")
        print()
    
    if not supabase_key:
        print("❌ SUPABASE_API_KEY не установлен")
        print("   Добавьте в .env: SUPABASE_API_KEY=ваш_ключ")
        print("   Получите ключ в Supabase Dashboard → Settings → API")
        print()
    
    if not database_url:
        print("⚠️ SUPABASE_DB_URL не установлен")
        print("   REST API подключение будет работать, но прямое PostgreSQL подключение недоступно")
        print("   Для прямого подключения добавьте в .env:")
        print("   SUPABASE_DB_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres")
        print()
    else:
        # Проверяем формат URL
        try:
            parsed = urlparse(database_url)
            if '@' in parsed.netloc:
                host = parsed.netloc.split('@')[1].split(':')[0]
                
                # Проверяем DNS
                print("🔍 Проверка DNS...")
                try:
                    import socket
                    if ':' in parsed.netloc.split('@')[1]:
                        port = int(parsed.netloc.split('@')[1].split(':')[1].split('/')[0])
                    else:
                        port = 5432 if parsed.scheme == 'postgresql' else 6543
                    
                    socket.gethostbyname(host)
                    print(f"   ✅ DNS резолвинг работает для {host}")
                except socket.gaierror as e:
                    print(f"   ❌ Ошибка DNS для {host}: {e}")
                    print("   💡 Возможные причины:")
                    print("      - Неправильный формат URL")
                    print("      - Проблемы с интернет-соединением")
                    print("      - Хост недоступен")
                    print()
                    print("   💡 Решение:")
                    print("      - Проверьте формат SUPABASE_DB_URL")
                    print("      - Убедитесь, что используете правильный project reference")
                    print("      - Для Direct connection: db.[PROJECT_REF].supabase.co")
                    print("      - Для Connection pooling: aws-0-[REGION].pooler.supabase.com")
        except Exception as e:
            print(f"   ⚠️ Не удалось проверить DNS: {e}")
    
    print()
    print("=" * 60)
    print("СТАТУС ПОДКЛЮЧЕНИЯ:")
    print("=" * 60)
    print()
    
    use_supabase_api = bool(supabase_key and supabase_url)
    use_postgresql = bool(database_url)
    
    print(f"   REST API подключение: {'✅ Доступно' if use_supabase_api else '❌ Недоступно'}")
    print(f"   PostgreSQL подключение: {'✅ Доступно' if use_postgresql else '❌ Недоступно'}")
    print()
    
    if use_supabase_api:
        print("   ✅ REST API подключение работает!")
        print("   💡 Можно использовать Supabase через REST API")
        print("   ⚠️ Для применения миграций нужен прямой доступ к PostgreSQL")
    else:
        print("   ❌ REST API подключение не настроено")
    
    if use_postgresql:
        print("   ⚠️ PostgreSQL подключение настроено, но может не работать из-за DNS")
        print("   💡 Проверьте формат SUPABASE_DB_URL")
    else:
        print("   ⚠️ PostgreSQL подключение не настроено")
        print("   💡 Добавьте SUPABASE_DB_URL для прямого доступа к базе данных")

if __name__ == '__main__':
    diagnose_connection()
