"""
Показывает информацию о таблицах базы данных на основе миграции
"""
import sys

# Исправляем кодировку для Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 80)
print("СТРУКТУРА ТАБЛИЦ БАЗЫ ДАННЫХ")
print("=" * 80)
print()

tables_info = [
    {
        "name": "telegram_users",
        "description": "Пользователи Telegram бота",
        "columns": [
            ("user_id", "BIGINT", "PRIMARY KEY", "ID пользователя Telegram"),
            ("username", "TEXT", "", "Имя пользователя"),
            ("first_name", "TEXT", "", "Имя"),
            ("birth_date", "TEXT", "", "Дата рождения"),
            ("registration_date", "TIMESTAMPTZ", "DEFAULT NOW()", "Дата регистрации"),
            ("subscription_type", "TEXT", "DEFAULT 'trial'", "Тип подписки"),
            ("subscription_end_date", "TIMESTAMPTZ", "", "Дата окончания подписки"),
            ("is_active", "BOOLEAN", "DEFAULT TRUE", "Активен ли пользователь"),
            ("is_admin", "BOOLEAN", "DEFAULT FALSE", "Является ли администратором"),
            ("created_at", "TIMESTAMPTZ", "DEFAULT NOW()", "Дата создания"),
            ("updated_at", "TIMESTAMPTZ", "DEFAULT NOW()", "Дата обновления")
        ]
    },
    {
        "name": "telegram_calculations",
        "description": "Расчеты даров",
        "columns": [
            ("id", "SERIAL", "PRIMARY KEY", "ID записи"),
            ("user_id", "BIGINT", "REFERENCES telegram_users", "ID пользователя"),
            ("calculation_type", "TEXT", "NOT NULL", "Тип расчета"),
            ("birth_date", "TEXT", "", "Дата рождения для расчета"),
            ("result_data", "TEXT", "", "Результат расчета"),
            ("calculation_date", "TIMESTAMPTZ", "DEFAULT NOW()", "Дата расчета")
        ]
    },
    {
        "name": "telegram_gifts_knowledge",
        "description": "База знаний о дарах",
        "columns": [
            ("id", "SERIAL", "PRIMARY KEY", "ID записи"),
            ("gift_number", "INTEGER", "", "Номер дара"),
            ("gift_name", "TEXT", "", "Название дара"),
            ("description", "TEXT", "", "Описание"),
            ("characteristics", "TEXT", "", "Характеристики"),
            ("category", "TEXT", "", "Категория")
        ]
    },
    {
        "name": "telegram_ai_interactions",
        "description": "История взаимодействий с ИИ",
        "columns": [
            ("id", "SERIAL", "PRIMARY KEY", "ID записи"),
            ("user_id", "BIGINT", "REFERENCES telegram_users", "ID пользователя"),
            ("query", "TEXT", "", "Запрос пользователя"),
            ("response", "TEXT", "", "Ответ ИИ"),
            ("interaction_date", "TIMESTAMPTZ", "DEFAULT NOW()", "Дата взаимодействия")
        ]
    },
    {
        "name": "telegram_payments",
        "description": "Платежи",
        "columns": [
            ("id", "SERIAL", "PRIMARY KEY", "ID записи"),
            ("user_id", "BIGINT", "REFERENCES telegram_users", "ID пользователя"),
            ("amount", "INTEGER", "", "Сумма платежа"),
            ("currency", "TEXT", "", "Валюта"),
            ("payment_date", "TIMESTAMPTZ", "DEFAULT NOW()", "Дата платежа"),
            ("subscription_type", "TEXT", "", "Тип подписки"),
            ("status", "TEXT", "", "Статус платежа")
        ]
    },
    {
        "name": "telegram_alphabet",
        "description": "Алфавит для анализа слов",
        "columns": [
            ("id", "SERIAL", "PRIMARY KEY", "ID записи"),
            ("letter", "TEXT", "UNIQUE NOT NULL", "Буква"),
            ("name", "TEXT", "", "Название буквы"),
            ("description", "TEXT", "", "Описание значения буквы")
        ]
    },
    {
        "name": "telegram_promocodes",
        "description": "Промокоды",
        "columns": [
            ("id", "SERIAL", "PRIMARY KEY", "ID записи"),
            ("code", "TEXT", "UNIQUE NOT NULL", "Код промокода"),
            ("type", "TEXT", "NOT NULL", "Тип промокода (discount/subscription)"),
            ("discount_percent", "INTEGER", "", "Процент скидки"),
            ("subscription_days", "INTEGER", "", "Дни подписки"),
            ("subscription_type", "TEXT", "", "Тип подписки"),
            ("max_uses", "INTEGER", "", "Максимальное количество использований"),
            ("current_uses", "INTEGER", "DEFAULT 0", "Текущее количество использований"),
            ("created_date", "TIMESTAMPTZ", "DEFAULT NOW()", "Дата создания"),
            ("created_by", "BIGINT", "REFERENCES telegram_users", "ID создателя"),
            ("is_active", "BOOLEAN", "DEFAULT TRUE", "Активен ли промокод")
        ]
    },
    {
        "name": "telegram_promocode_usage",
        "description": "Использования промокодов",
        "columns": [
            ("id", "SERIAL", "PRIMARY KEY", "ID записи"),
            ("promocode_id", "INTEGER", "REFERENCES telegram_promocodes", "ID промокода"),
            ("user_id", "BIGINT", "REFERENCES telegram_users", "ID пользователя"),
            ("usage_date", "TIMESTAMPTZ", "DEFAULT NOW()", "Дата использования")
        ]
    },
    {
        "name": "telegram_ma_zhi_kun_positions",
        "description": "Позиции Ма-Жи-Кун",
        "columns": [
            ("id", "SERIAL", "PRIMARY KEY", "ID записи"),
            ("name", "TEXT", "UNIQUE NOT NULL", "Название позиции (МА/ЖИ/КУН)"),
            ("description", "TEXT", "NOT NULL", "Описание позиции")
        ]
    },
    {
        "name": "telegram_gift_fields",
        "description": "Поля даров (1-9)",
        "columns": [
            ("id", "INTEGER", "PRIMARY KEY", "ID поля (1-9)"),
            ("name", "TEXT", "NOT NULL", "Название поля"),
            ("description", "TEXT", "NOT NULL", "Описание поля")
        ]
    }
]

for i, table in enumerate(tables_info, 1):
    print(f"\n{i}. 📋 ТАБЛИЦА: {table['name']}")
    print(f"   Описание: {table['description']}")
    print(f"\n   Структура (колонки):")
    for col_name, col_type, constraints, description in table['columns']:
        constraints_str = f" {constraints}" if constraints else ""
        print(f"      • {col_name:<25} {col_type:<15}{constraints_str:<25} - {description}")
    print()

print("=" * 80)
print(f"\nВсего таблиц: {len(tables_info)}")
print("\n💡 Для просмотра данных в таблицах используйте: python scripts/show_tables.py")
print("💡 Для применения миграции используйте: python scripts/apply_migration.py")
