# 🏗️ Архитектура проекта

## 📐 Общая схема

```
┌─────────────────────────────────────────────────────────────┐
│                      TELEGRAM USER                           │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT API                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                      bot.py (aiogram)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  • Обработка команд (/start, /calculate, etc)       │   │
│  │  • FSM (машина состояний)                           │   │
│  │  • Клавиатуры и интерфейс                          │   │
│  └──────────────────────────────────────────────────────┘   │
└────┬──────────────┬──────────────┬──────────────┬──────────┘
     │              │              │              │
     ▼              ▼              ▼              ▼
┌─────────┐  ┌─────────────┐  ┌──────────┐  ┌──────────────┐
│config.py│  │database.py  │  │calcula   │  │ai_handler.py │
│         │  │             │  │tions.py  │  │              │
│• Токены │  │• SQLite     │  │          │  │• DeepSeek    │
│• Настр. │  │• Юзеры      │  │• Ода     │  │  API         │
│• .env   │  │• Расчеты    │  │• Туна    │  │• Промпты     │
│         │  │• Подписки   │  │• Триа    │  │• Анализ      │
│         │  │• База знаний│  │• Чиа     │  │              │
└─────────┘  └──────┬──────┘  └──────────┘  └──────────────┘
                    │
                    ▼
            ┌───────────────┐
            │  SQLite DB    │
            │               │
            │• users        │
            │• calculations │
            │• gifts_know.  │
            │• ai_interact. │
            │• payments     │
            └───────────────┘
```

---

## 🔄 Поток данных

### 1️⃣ Регистрация пользователя

```
Пользователь → /start
    ↓
bot.py: cmd_start()
    ↓
database.py: add_user()
    ↓
SQLite: INSERT INTO users
    ↓
Ответ: Приветствие + меню
```

### 2️⃣ Расчет даров

```
Пользователь → "🎁 Рассчитать дары"
    ↓
bot.py: cmd_calculate()
    ↓
FSM: waiting_for_birth_date
    ↓
Пользователь вводит дату → "15.05.1990"
    ↓
bot.py: process_birth_date()
    ↓
database.py: check_subscription() ← Проверка подписки
    ↓
calculations.py: calculate_all_gifts()
    │
    ├─→ calculate_oda()
    ├─→ calculate_tuna()
    ├─→ calculate_tria()
    └─→ calculate_chia()
    ↓
database.py: save_calculation() ← Сохранение результата
    ↓
ai_handler.py: get_gift_interpretation()
    ↓
DeepSeek API: Анализ даров
    ↓
Ответ: Полная трактовка с ИИ
```

### 3️⃣ Работа с подписками

```
Пользователь → "💎 Подписка"
    ↓
bot.py: cmd_subscription()
    ↓
database.py: check_subscription()
    ↓
SQLite: SELECT FROM users
    ↓
Проверка subscription_end_date
    ↓
Ответ: Статус подписки + меню оплаты
```

---

## 📦 Модули и их функции

### bot.py
**Роль:** Главный контроллер бота

**Функции:**
- `cmd_start()` - Приветствие и регистрация
- `cmd_calculate()` - Начало расчета
- `process_birth_date()` - Обработка даты
- `cmd_subscription()` - Управление подпиской
- `cmd_help()` - Справка

**Зависимости:**
- aiogram (Telegram Bot API)
- config.py (настройки)
- database.py (БД)
- calculations.py (расчеты)
- ai_handler.py (ИИ)
- keyboards.py (интерфейс)

---

### config.py
**Роль:** Управление конфигурацией

**Функции:**
- Загрузка `.env` файла
- Валидация токенов
- Хранение констант

**Данные:**
- `BOT_TOKEN` - токен Telegram бота
- `DEEPSEEK_API_KEY` - ключ DeepSeek
- `DATABASE_PATH` - путь к БД
- `TRIAL_DURATION_DAYS` - длительность триала
- `PREMIUM_PRICE_STARS` - цена премиума

---

### database.py
**Роль:** Работа с базой данных

**Функции:**
- `init_db()` - Создание таблиц
- `add_user()` - Добавление пользователя
- `get_user()` - Получение данных юзера
- `update_user_birth_date()` - Обновление даты
- `save_calculation()` - Сохранение расчета
- `check_subscription()` - Проверка подписки
- `add_gift_knowledge()` - Добавление знаний
- `get_gift_knowledge()` - Получение знаний

**Таблицы:**
- `users` - пользователи
- `calculations` - расчеты
- `gifts_knowledge` - база знаний
- `ai_interactions` - история с ИИ
- `payments` - платежи

---

### calculations.py
**Роль:** Расчет даров по формулам

**Класс:** `GiftsCalculator`

**Методы:**
- `parse_date()` - Парсинг даты
- `reduce_to_22()` - Приведение к 1-22
- `calculate_oda()` - Расчет Оды
- `calculate_tuna()` - Расчет Туны
- `calculate_tria()` - Расчет Триа
- `calculate_chia()` - Расчет Чиа
- `calculate_all_gifts()` - Все дары

**Формулы:**
- **Ода:** день + месяц + год → 1-22
- **Туна:** день + месяц → 1-22
- **Триа:** месяц + год → 1-22
- **Чиа:** день + год → 1-22

---

### ai_handler.py
**Роль:** Интеграция с ИИ

**Класс:** `AIHandler`

**Методы:**
- `get_gift_interpretation()` - Получение трактовки
- `_build_prompt()` - Построение промпта
- `_get_basic_interpretation()` - Базовая трактовка

**API:**
- DeepSeek Chat API
- Model: `deepseek-chat`
- Temperature: 0.7
- Max tokens: 1000

**Промпт включает:**
- Системное сообщение (роль эксперта)
- Данные о дарах
- Контекст пользователя
- Запрос на анализ

---

### keyboards.py
**Роль:** Интерфейс бота

**Функции:**
- `get_main_menu()` - Главное меню
- `get_subscription_menu()` - Меню подписок
- `get_calculation_type_menu()` - Выбор типа расчета

**Клавиатуры:**
- Reply Keyboard - основное меню
- Inline Keyboard - подписки и выбор

---

### gifts_knowledge.py
**Роль:** База знаний о дарах

**Структура:**
```python
GIFTS_DATABASE = {
    1: {
        "name": "Название",
        "description": "Описание",
        "characteristics": [...],
        "strengths": [...],
        "challenges": [...],
        "recommendations": [...],
        "element": "Стихия",
        "planet": "Планета",
        "archetype": "Архетип"
    }
}
```

**Функции:**
- `get_gift_info()` - Получение инфо
- `add_gift_info()` - Добавление инфо
- `format_gift_description()` - Форматирование

---

## 🗄️ Структура базы данных

### Таблица: users
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    birth_date TEXT,
    registration_date TEXT,
    subscription_type TEXT DEFAULT 'trial',
    subscription_end_date TEXT,
    is_active INTEGER DEFAULT 1
)
```

### Таблица: calculations
```sql
CREATE TABLE calculations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    calculation_type TEXT,
    birth_date TEXT,
    result_data TEXT,
    calculation_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
```

### Таблица: gifts_knowledge
```sql
CREATE TABLE gifts_knowledge (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    gift_number INTEGER,
    gift_name TEXT,
    description TEXT,
    characteristics TEXT,
    category TEXT
)
```

### Таблица: ai_interactions
```sql
CREATE TABLE ai_interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    query TEXT,
    response TEXT,
    interaction_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
```

### Таблица: payments
```sql
CREATE TABLE payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    currency TEXT,
    payment_date TEXT,
    subscription_type TEXT,
    status TEXT,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
```

---

## 🔐 Безопасность

### Уровни защиты

1. **Конфигурация**
   - `.env` файл (не в git)
   - Валидация при запуске
   - Безопасное хранение токенов

2. **База данных**
   - Параметризованные запросы
   - Защита от SQL-инъекций
   - Ограничение прав доступа

3. **API**
   - HTTPS для всех запросов
   - Авторизация через токены
   - Обработка ошибок

---

## ⚡ Производительность

### Асинхронность
- Все операции асинхронные (async/await)
- Параллельная обработка запросов
- Неблокирующие операции БД

### Оптимизация
- SQLite для быстрого доступа
- Кэширование результатов
- Минимальные запросы к API

### Масштабируемость
- Легко переход на PostgreSQL
- Горизонтальное масштабирование
- Балансировка нагрузки

---

## 🧪 Тестирование

### Модульные тесты
- `test_calculations.py` - тесты расчетов
- Проверка формул
- Граничные случаи
- Валидация данных

### Интеграционные тесты
- Работа с БД
- API запросы
- Полный цикл расчета

---

## 📈 Мониторинг

### Логирование
- Уровень: INFO
- Вывод: консоль
- Формат: timestamp + message

### Метрики
- Количество пользователей
- Количество расчетов
- Время обработки
- Ошибки API

---

## 🚀 Развертывание

### Локальное
```bash
python bot.py
```

### Production
- Systemd service
- Docker container
- Supervisor
- PM2

### Требования
- Python 3.8+
- SQLite 3
- Интернет (для API)
- Telegram Bot Token

---

**Архитектура готова к расширению и масштабированию! 🎯**

