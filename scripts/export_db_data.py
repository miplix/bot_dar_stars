"""
Скрипт для экспорта данных из базы данных:
- Пользователи и сроки подписки
- Промокоды
"""
import sqlite3
import os
import sys
from datetime import datetime

# Устанавливаем UTF-8 кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Определяем путь к базе данных
def get_db_path():
    """Определяет путь к базе данных"""
    # Проверяем переменные окружения
    if os.getenv('DATABASE_PATH'):
        return os.getenv('DATABASE_PATH')
    
    # Проверяем Vercel окружение
    if os.getenv('VERCEL') or os.getenv('VERCEL_ENV'):
        return '/tmp/bot_database.db'
    
    # Локальная разработка
    return 'data/bot_database.db'

def export_users_and_subscriptions(db_path: str):
    """Экспорт пользователей и их подписок"""
    print("=" * 80)
    print("ПОЛЬЗОВАТЕЛИ И ПОДПИСКИ")
    print("=" * 80)
    print()
    
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        cursor = db.execute("""
            SELECT 
                user_id,
                username,
                first_name,
                registration_date,
                subscription_type,
                subscription_end_date,
                is_admin,
                is_active
            FROM users
            ORDER BY registration_date DESC
        """)
        
        users = cursor.fetchall()
        
        if not users:
            print("❌ Пользователи не найдены")
            return
        
        print(f"Всего пользователей: {len(users)}\n")
        
        # Подсчет статистики
        active_subscriptions = 0
        expired_subscriptions = 0
        trial_users = 0
        premium_users = 0
        admins = 0
        
        for user in users:
            if user['is_admin'] == 1:
                admins += 1
            if user['subscription_type'] == 'trial':
                trial_users += 1
            elif user['subscription_type'] and user['subscription_type'].startswith('premium'):
                premium_users += 1
            
            if user['subscription_end_date']:
                end_date = datetime.fromisoformat(user['subscription_end_date'])
                if end_date > datetime.now():
                    active_subscriptions += 1
                else:
                    expired_subscriptions += 1
        
        print(f"📊 Статистика:")
        print(f"   • Администраторов: {admins}")
        print(f"   • Trial пользователей: {trial_users}")
        print(f"   • Premium пользователей: {premium_users}")
        print(f"   • Активных подписок: {active_subscriptions}")
        print(f"   • Истекших подписок: {expired_subscriptions}")
        print()
        print("-" * 80)
        print()
        
        # Детальная информация о пользователях
        for user in users:
            user_id = user['user_id']
            username = user['username'] or "—"
            first_name = user['first_name'] or "—"
            reg_date = user['registration_date'] or "—"
            sub_type = user['subscription_type'] or "—"
            sub_end = user['subscription_end_date'] or "—"
            is_admin = "👑 АДМИН" if user['is_admin'] == 1 else ""
            is_active = "✅" if user['is_active'] == 1 else "❌"
            
            # Проверка статуса подписки
            status = ""
            if sub_end and sub_end != "—":
                try:
                    end_date = datetime.fromisoformat(sub_end)
                    now = datetime.now()
                    if end_date > now:
                        days_left = (end_date - now).days
                        status = f"🟢 Активна (осталось {days_left} дн.)"
                    else:
                        days_expired = (now - end_date).days
                        status = f"🔴 Истекла ({days_expired} дн. назад)"
                except:
                    status = "⚠️ Ошибка даты"
            elif sub_type == "trial":
                status = "🟡 Trial период"
            else:
                status = "⚪ Нет подписки"
            
            print(f"ID: {user_id} | {is_active} {is_admin}")
            print(f"   Имя: {first_name}")
            print(f"   Username: @{username}")
            print(f"   Регистрация: {reg_date}")
            print(f"   Тип подписки: {sub_type}")
            print(f"   Дата окончания: {sub_end}")
            print(f"   Статус: {status}")
            print()

def export_promocodes(db_path: str):
    """Экспорт промокодов"""
    print("=" * 80)
    print("ПРОМОКОДЫ")
    print("=" * 80)
    print()
    
    with sqlite3.connect(db_path) as db:
        db.row_factory = sqlite3.Row
        
        # Получаем все промокоды
        cursor = db.execute("""
            SELECT 
                p.id,
                p.code,
                p.type,
                p.discount_percent,
                p.subscription_days,
                p.max_uses,
                p.current_uses,
                p.created_date,
                p.created_by,
                p.is_active,
                u.username as creator_username
            FROM promocodes p
            LEFT JOIN users u ON p.created_by = u.user_id
            ORDER BY p.created_date DESC
        """)
        
        promocodes = cursor.fetchall()
        
        if not promocodes:
            print("❌ Промокоды не найдены")
            return
        
        print(f"Всего промокодов: {len(promocodes)}\n")
        
        # Подсчет статистики
        active_promos = 0
        expired_promos = 0
        discount_promos = 0
        subscription_promos = 0
        
        for promo in promocodes:
            if promo['is_active'] == 1:
                active_promos += 1
            else:
                expired_promos += 1
            
            if promo['type'] == 'discount':
                discount_promos += 1
            elif promo['type'] == 'subscription':
                subscription_promos += 1
        
        print(f"📊 Статистика:")
        print(f"   • Активных: {active_promos}")
        print(f"   • Неактивных: {expired_promos}")
        print(f"   • Со скидкой: {discount_promos}")
        print(f"   • С подпиской: {subscription_promos}")
        print()
        print("-" * 80)
        print()
        
        # Детальная информация о промокодах
        for promo in promocodes:
            promo_id = promo['id']
            code = promo['code']
            promo_type = promo['type']
            is_active = "✅ Активен" if promo['is_active'] == 1 else "❌ Неактивен"
            max_uses = promo['max_uses'] or "∞"
            current_uses = promo['current_uses'] or 0
            created_date = promo['created_date'] or "—"
            creator = promo['creator_username'] or f"ID: {promo['created_by']}" if promo['created_by'] else "—"
            
            # Информация в зависимости от типа
            details = ""
            if promo_type == 'discount':
                discount = promo['discount_percent'] or 0
                details = f"Скидка: {discount}%"
            elif promo_type == 'subscription':
                days = promo['subscription_days'] or 0
                details = f"Подписка: {days} дней"
            
            # Статус использования
            usage_status = ""
            if max_uses != "∞":
                remaining = max_uses - current_uses
                if remaining > 0:
                    usage_status = f"Осталось использований: {remaining}/{max_uses}"
                else:
                    usage_status = f"🔴 Исчерпан ({current_uses}/{max_uses})"
            else:
                usage_status = f"Использовано: {current_uses} раз"
            
            print(f"ID: {promo_id} | {is_active}")
            print(f"   Код: {code}")
            print(f"   Тип: {promo_type} ({details})")
            print(f"   {usage_status}")
            print(f"   Создан: {created_date}")
            print(f"   Создатель: {creator}")
            print()
        
        # Дополнительная информация об использовании промокодов
        print("-" * 80)
        print("ИСПОЛЬЗОВАНИЕ ПРОМОКОДОВ")
        print("-" * 80)
        print()
        
        for promo in promocodes:
            if promo['current_uses'] and promo['current_uses'] > 0:
                cursor = db.execute("""
                    SELECT 
                        pu.usage_date,
                        u.user_id,
                        u.username,
                        u.first_name
                    FROM promocode_usage pu
                    JOIN users u ON pu.user_id = u.user_id
                    WHERE pu.promocode_id = ?
                    ORDER BY pu.usage_date DESC
                """, (promo['id'],))
                
                usages = cursor.fetchall()
                
                if usages:
                    print(f"Промокод '{promo['code']}' использован {len(usages)} раз(а):")
                    for usage in usages:
                        user_info = f"@{usage['username']}" if usage['username'] else f"ID: {usage['user_id']}"
                        name = usage['first_name'] or "—"
                        print(f"   • {user_info} ({name}) - {usage['usage_date']}")
                    print()

def main():
    """Главная функция"""
    # Проверяем аргументы командной строки
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = get_db_path()
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        print("Убедитесь, что бот был запущен хотя бы один раз.")
        print(f"\nИспользование: python scripts/export_db_data.py [путь_к_базе_данных]")
        return
    
    print(f"📁 База данных: {db_path}")
    print()
    
    try:
        export_users_and_subscriptions(db_path)
        print()
        export_promocodes(db_path)
        
        print("=" * 80)
        print("✅ Экспорт завершен")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Ошибка при экспорте: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

