-- Миграция для создания таблиц Telegram бота в Vercel Postgres

-- Таблица пользователей Telegram бота
CREATE TABLE IF NOT EXISTS telegram_users (
    user_id BIGINT PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    birth_date TEXT,
    registration_date TIMESTAMPTZ DEFAULT NOW(),
    subscription_type TEXT DEFAULT 'trial',
    subscription_end_date TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица расчетов даров
CREATE TABLE IF NOT EXISTS telegram_calculations (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES telegram_users(user_id) ON DELETE CASCADE,
    calculation_type TEXT NOT NULL,
    birth_date TEXT,
    result_data TEXT,
    calculation_date TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица для базы знаний о дарах
CREATE TABLE IF NOT EXISTS telegram_gifts_knowledge (
    id SERIAL PRIMARY KEY,
    gift_number INTEGER,
    gift_name TEXT,
    description TEXT,
    characteristics TEXT,
    category TEXT
);

-- Таблица истории взаимодействий с ИИ
CREATE TABLE IF NOT EXISTS telegram_ai_interactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES telegram_users(user_id) ON DELETE CASCADE,
    query TEXT,
    response TEXT,
    interaction_date TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица платежей
CREATE TABLE IF NOT EXISTS telegram_payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES telegram_users(user_id) ON DELETE CASCADE,
    amount INTEGER,
    currency TEXT,
    payment_date TIMESTAMPTZ DEFAULT NOW(),
    subscription_type TEXT,
    status TEXT
);

-- Таблица алфавита для анализа слов
CREATE TABLE IF NOT EXISTS telegram_alphabet (
    id SERIAL PRIMARY KEY,
    letter TEXT UNIQUE NOT NULL,
    name TEXT,
    description TEXT
);

-- Таблица промокодов
CREATE TABLE IF NOT EXISTS telegram_promocodes (
    id SERIAL PRIMARY KEY,
    code TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    discount_percent INTEGER,
    subscription_days INTEGER,
    subscription_type TEXT,
    max_uses INTEGER,
    current_uses INTEGER DEFAULT 0,
    created_date TIMESTAMPTZ DEFAULT NOW(),
    created_by BIGINT REFERENCES telegram_users(user_id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- Таблица использований промокодов
CREATE TABLE IF NOT EXISTS telegram_promocode_usage (
    id SERIAL PRIMARY KEY,
    promocode_id INTEGER REFERENCES telegram_promocodes(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES telegram_users(user_id) ON DELETE CASCADE,
    usage_date TIMESTAMPTZ DEFAULT NOW()
);

-- Таблица позиций Ма-Жи-Кун
CREATE TABLE IF NOT EXISTS telegram_ma_zhi_kun_positions (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL
);

-- Таблица полей (1-9)
CREATE TABLE IF NOT EXISTS telegram_gift_fields (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL
);

-- Индексы для улучшения производительности
CREATE INDEX IF NOT EXISTS idx_telegram_users_user_id ON telegram_users(user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_calculations_user_id ON telegram_calculations(user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_promocodes_code ON telegram_promocodes(code);
CREATE INDEX IF NOT EXISTS idx_telegram_promocodes_active ON telegram_promocodes(is_active);
CREATE INDEX IF NOT EXISTS idx_telegram_promocode_usage_promocode_id ON telegram_promocode_usage(promocode_id);
CREATE INDEX IF NOT EXISTS idx_telegram_promocode_usage_user_id ON telegram_promocode_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_telegram_alphabet_letter ON telegram_alphabet(letter);

