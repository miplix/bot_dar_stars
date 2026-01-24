"""
Управление базой данных для бота
Поддерживает:
- Supabase (PostgreSQL) - для продакшена, без лимитов
- SQLite - для локальной разработки
"""
import aiosqlite
import os
import asyncio
import contextlib
from datetime import datetime, timedelta
from src.config import Config
from urllib.parse import urlparse
from supabase import create_client
from dateutil.parser import isoparse

try:
    import asyncpg
except Exception:
    asyncpg = None

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = None, database_url: str = None):
        self.use_postgresql = Config.USE_POSTGRESQL
        self.use_supabase = Config.USE_SUPABASE
        self.use_supabase_api = Config.USE_SUPABASE_API and not self.use_postgresql
        # Используем SUPABASE_DB_URL или DATABASE_URL для подключения к Supabase
        self.database_url = database_url or Config.SUPABASE_DB_URL
        
        # db_path нужен только для SQLite
        if self.use_postgresql:
            self.db_path = db_path  # Может быть None для PostgreSQL/Supabase
        else:
            self.db_path = db_path or getattr(Config, 'DATABASE_PATH', 'data/bot_database.db')
            # Создаем директорию для базы данных, если её нет (только для SQLite)
            db_dir = os.path.dirname(self.db_path)
            if db_dir:  # Если путь содержит директорию (не корневой файл)
                os.makedirs(db_dir, exist_ok=True)
        
        self.pool = None  # Connection pool для PostgreSQL/Supabase
        self._pool_loop = None  # Event loop, к которому привязан pool
        self._supabase = None
        if self.use_supabase_api:
            self._supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_API_KEY)
        elif self.use_postgresql and asyncpg is None:
            raise RuntimeError(
                "asyncpg не установлен, но требуется PostgreSQL. "
                "Установите asyncpg или используйте SUPABASE_API_KEY без SUPABASE_DB_URL."
            )

    async def _sb(self, fn):
        """Запускает синхронный вызов Supabase в отдельном потоке."""
        return await asyncio.to_thread(fn)

    @staticmethod
    def _parse_dt(value):
        if value is None or isinstance(value, datetime):
            return value
        try:
            return isoparse(value)
        except Exception:
            try:
                return datetime.fromisoformat(value)
            except Exception:
                return None
        
    async def _ensure_pool(self):
        """Обеспечивает наличие connection pool для текущего event loop"""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = asyncio.get_event_loop()
        
        # Проверяем, нужно ли пересоздать pool
        if self.pool is None or (self._pool_loop is not None and self._pool_loop is not current_loop):
            # Закрываем старый pool, если он существует и привязан к другому loop
            if self.pool is not None:
                try:
                    await self.pool.close()
                except Exception:
                    pass  # Игнорируем ошибки при закрытии старого pool
            
            # Создаем новый connection pool для текущего event loop
            # Для Supabase: asyncpg лучше работает с direct connection, а не через pgbouncer
            # Но если используется connection pooling URL, оставляем как есть
            conn_url = self.database_url
            
            # Если URL содержит pgbouncer и используется Supabase, лучше использовать direct connection
            # Но можно оставить pgbouncer, если нужна лучшая производительность при большом количестве соединений
            # Для asyncpg обычно direct connection работает лучше
            if 'pooler.supabase.com' in conn_url or 'pgbouncer=true' in conn_url:
                # Используем как есть - asyncpg может работать с pgbouncer
                pass
            
            self.pool = await asyncpg.create_pool(
                conn_url, 
                min_size=1, 
                max_size=10,
                command_timeout=30  # Таймаут для команд
            )
            self._pool_loop = current_loop
        
        return self.pool
    
    @contextlib.asynccontextmanager
    async def _pg_connection_ctx(self):
        """Context manager для получения соединения с PostgreSQL"""
        pool = await self._ensure_pool()
        conn = await pool.acquire()
        try:
            yield conn
        finally:
            try:
                await pool.release(conn)
            except Exception:
                # Игнорируем ошибки при освобождении соединения
                pass
    
    async def _get_pg_connection(self):
        """Получает соединение с PostgreSQL (для обратной совместимости)"""
        # ВАЖНО: Этот метод должен использоваться с try/finally и _release_pg_connection
        # Лучше использовать _pg_connection_ctx() как context manager
        pool = await self._ensure_pool()
        return await pool.acquire()
    
    async def _release_pg_connection(self, conn):
        """Освобождает соединение с PostgreSQL"""
        if self.pool and conn:
            try:
                await self.pool.release(conn)
            except Exception:
                # Игнорируем ошибки при освобождении соединения
                pass
        
    async def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        if self.use_supabase_api:
            try:
                await self._sb(lambda: self._supabase.table("telegram_users").select("user_id").limit(1).execute())
                print("✅ Таблицы Supabase доступны (REST API)")
            except Exception as e:
                print(f"⚠️ Ошибка при проверке Supabase REST API: {e}")
                print("Проверьте SUPABASE_URL и SUPABASE_API_KEY")
            return
        if self.use_postgresql:
            # PostgreSQL - таблицы должны быть созданы через миграцию
            # Проверяем, что таблицы существуют
            try:
                async with self._pg_connection_ctx() as conn:
                    # Проверяем наличие таблицы users
                    result = await conn.fetchval("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_schema = 'public' 
                            AND table_name = 'telegram_users'
                        )
                    """)
                    if not result:
                        if self.use_supabase:
                            print("⚠️ Таблицы не найдены в Supabase. Примените миграцию:")
                            print("   1. Через Supabase Dashboard → SQL Editor")
                            print("   2. Или используйте MCP Supabase для применения миграции")
                        else:
                            print("⚠️ Таблицы не найдены. Примените миграцию: python scripts/apply_migration.py")
                    else:
                        db_type = "Supabase" if self.use_supabase else "PostgreSQL"
                        print(f"✅ Таблицы {db_type} найдены")
            except Exception as e:
                print(f"⚠️ Ошибка при проверке базы данных: {e}")
                if self.use_supabase:
                    print("Проверьте SUPABASE_DB_URL в переменных окружения")
                else:
                    print("Примените миграцию вручную через SQL Editor")
            return
        
        # SQLite - создаем таблицы
        # Убеждаемся, что db_path установлен
        if not self.db_path:
            self.db_path = getattr(Config, 'DATABASE_PATH', 'data/bot_database.db')
        # Создаем директорию для базы данных, если её нет
        db_dir = os.path.dirname(self.db_path)
        if db_dir:  # Если путь содержит директорию (не корневой файл)
            os.makedirs(db_dir, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    birth_date TEXT,
                    registration_date TEXT,
                    subscription_type TEXT DEFAULT 'trial',
                    subscription_end_date TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_admin INTEGER DEFAULT 0
                )
            """)
            
            # Таблица расчетов даров
            await db.execute("""
                CREATE TABLE IF NOT EXISTS calculations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    calculation_type TEXT,
                    birth_date TEXT,
                    result_data TEXT,
                    calculation_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица для базы знаний о дарах
            await db.execute("""
                CREATE TABLE IF NOT EXISTS gifts_knowledge (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gift_number INTEGER,
                    gift_name TEXT,
                    description TEXT,
                    characteristics TEXT,
                    category TEXT
                )
            """)
            
            # Таблица истории взаимодействий с ИИ
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ai_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    query TEXT,
                    response TEXT,
                    interaction_date TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица платежей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    amount INTEGER,
                    currency TEXT,
                    payment_date TEXT,
                    subscription_type TEXT,
                    status TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица алфавита для анализа слов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS alphabet (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    letter TEXT UNIQUE,
                    name TEXT,
                    description TEXT
                )
            """)
            
            # Таблица промокодов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS promocodes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    type TEXT NOT NULL,
                    discount_percent INTEGER,
                    subscription_days INTEGER,
                    subscription_type TEXT,
                    max_uses INTEGER,
                    current_uses INTEGER DEFAULT 0,
                    created_date TEXT,
                    created_by INTEGER,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (created_by) REFERENCES users (user_id)
                )
            """)
            
            # Миграция: добавление колонки subscription_type, если её нет
            cursor = await db.execute("PRAGMA table_info(promocodes)")
            columns = [row[1] for row in await cursor.fetchall()]
            if 'subscription_type' not in columns:
                await db.execute("ALTER TABLE promocodes ADD COLUMN subscription_type TEXT")
            
            # Таблица использований промокодов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS promocode_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    promocode_id INTEGER,
                    user_id INTEGER,
                    usage_date TEXT,
                    FOREIGN KEY (promocode_id) REFERENCES promocodes (id),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # Таблица позиций Ма-Жи-Кун
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ma_zhi_kun_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL
                )
            """)
            
            # Таблица полей (1-9)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS gift_fields (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL
                )
            """)
            
            # Миграция: добавление колонки is_admin, если её нет
            cursor = await db.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in await cursor.fetchall()]
            if 'is_admin' not in columns:
                await db.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")
            
            await db.commit()
    
    async def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Добавление нового пользователя (только если его еще нет)"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if self.use_supabase_api:
                existing = await self._sb(
                    lambda: self._supabase.table("telegram_users")
                    .select("user_id")
                    .eq("user_id", user_id)
                    .limit(1)
                    .execute()
                )
                if existing.data:
                    logger.debug(f"Пользователь {user_id} уже существует в Supabase")
                    return

                registration_date = datetime.now().isoformat()
                trial_end = (datetime.now() + timedelta(days=Config.TRIAL_DURATION_DAYS)).isoformat()

                await self._sb(
                    lambda: self._supabase.table("telegram_users")
                    .insert(
                        {
                            "user_id": user_id,
                            "username": username,
                            "first_name": first_name,
                            "registration_date": registration_date,
                            "subscription_type": "trial",
                            "subscription_end_date": trial_end,
                        }
                    )
                    .execute()
                )
                logger.info(f"Пользователь {user_id} успешно сохранен в Supabase")
            elif self.use_postgresql:
                # PostgreSQL
                conn = await self._get_pg_connection()
                try:
                    # Проверяем, есть ли уже пользователь
                    existing_user = await conn.fetchval(
                        "SELECT user_id FROM telegram_users WHERE user_id = $1", user_id
                    )
                    
                    if existing_user:
                        logger.debug(f"Пользователь {user_id} уже существует в БД")
                        return
                    
                    # Новый пользователь - создаем с триал периодом
                    registration_date = datetime.now()
                    trial_end = datetime.now() + timedelta(days=Config.TRIAL_DURATION_DAYS)
                    
                    logger.info(f"Создание нового пользователя {user_id} (username={username}, first_name={first_name})")
                    async with conn.transaction():
                        await conn.execute("""
                            INSERT INTO telegram_users 
                            (user_id, username, first_name, registration_date, subscription_type, subscription_end_date)
                            VALUES ($1, $2, $3, $4, 'trial', $5)
                        """, user_id, username, first_name, registration_date, trial_end)
                    
                    # Проверяем, что данные сохранились
                    saved_user = await conn.fetchval(
                        "SELECT user_id FROM telegram_users WHERE user_id = $1", user_id
                    )
                    if not saved_user:
                        error_msg = f"Пользователь {user_id} не был сохранен в базу данных"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    logger.info(f"Пользователь {user_id} успешно сохранен в БД")
                finally:
                    await self._release_pg_connection(conn)
            else:
                # SQLite
                async with aiosqlite.connect(self.db_path) as db:
                    # Устанавливаем настройки для надежной записи
                    await db.execute("PRAGMA synchronous = NORMAL")
                    
                    # Проверяем, есть ли уже пользователь
                    cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                    existing_user = await cursor.fetchone()
                    
                    if existing_user:
                        logger.debug(f"Пользователь {user_id} уже существует в БД")
                        return
                    
                    # Новый пользователь - создаем с триал периодом
                    registration_date = datetime.now().isoformat()
                    trial_end = (datetime.now() + timedelta(days=Config.TRIAL_DURATION_DAYS)).isoformat()
                    
                    logger.info(f"Создание нового пользователя {user_id} (username={username}, first_name={first_name})")
                    await db.execute("""
                        INSERT INTO users 
                        (user_id, username, first_name, registration_date, subscription_type, subscription_end_date)
                        VALUES (?, ?, ?, ?, 'trial', ?)
                    """, (user_id, username, first_name, registration_date, trial_end))
                    await db.commit()
                    
                    # Проверяем, что данные сохранились
                    cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                    saved_user = await cursor.fetchone()
                    if not saved_user:
                        error_msg = f"Пользователь {user_id} не был сохранен в базу данных"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    logger.info(f"Пользователь {user_id} успешно сохранен в БД")
        except Exception as e:
            logger.error(f"Ошибка при сохранении пользователя {user_id}: {e}", exc_info=True)
            raise
    
    async def get_user(self, user_id: int):
        """Получение данных пользователя"""
        if self.use_supabase_api:
            result = await self._sb(
                lambda: self._supabase.table("telegram_users")
                .select("*")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        if self.use_postgresql:
            async with self._pg_connection_ctx() as conn:
                row = await conn.fetchrow(
                    "SELECT * FROM telegram_users WHERE user_id = $1", user_id
                )
                return row
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM users WHERE user_id = ?", (user_id,)
                )
                return await cursor.fetchone()
    
    async def update_user_birth_date(self, user_id: int, birth_date: str):
        """Обновление даты рождения пользователя"""
        if self.use_supabase_api:
            await self._sb(
                lambda: self._supabase.table("telegram_users")
                .update({"birth_date": birth_date})
                .eq("user_id", user_id)
                .execute()
            )
        elif self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                async with conn.transaction():
                    await conn.execute(
                        "UPDATE telegram_users SET birth_date = $1 WHERE user_id = $2",
                        birth_date, user_id
                    )
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE users SET birth_date = ? WHERE user_id = ?",
                    (birth_date, user_id)
                )
                await db.commit()
    
    async def save_calculation(self, user_id: int, calc_type: str, birth_date: str, result_data: str):
        """Сохранение результата расчета"""
        if self.use_supabase_api:
            calculation_date = datetime.now().isoformat()
            await self._sb(
                lambda: self._supabase.table("telegram_calculations")
                .insert(
                    {
                        "user_id": user_id,
                        "calculation_type": calc_type,
                        "birth_date": birth_date,
                        "result_data": result_data,
                        "calculation_date": calculation_date,
                    }
                )
                .execute()
            )
        elif self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                calculation_date = datetime.now()
                async with conn.transaction():
                    await conn.execute("""
                        INSERT INTO telegram_calculations 
                        (user_id, calculation_type, birth_date, result_data, calculation_date)
                        VALUES ($1, $2, $3, $4, $5)
                    """, user_id, calc_type, birth_date, result_data, calculation_date)
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                calculation_date = datetime.now().isoformat()
                await db.execute("""
                    INSERT INTO calculations 
                    (user_id, calculation_type, birth_date, result_data, calculation_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (user_id, calc_type, birth_date, result_data, calculation_date))
                await db.commit()
    
    async def check_subscription(self, user_id: int) -> dict:
        """Проверка подписки пользователя"""
        user = await self.get_user(user_id)
        if not user:
            return {"active": False, "type": None}
        
        if user['subscription_end_date']:
            # PostgreSQL/Supabase возвращает datetime объект, SQLite - строку
            end_date = self._parse_dt(user['subscription_end_date'])
            
            if datetime.now() < end_date:
                return {
                    "active": True,
                    "type": user['subscription_type'],
                    "end_date": end_date
                }
        
        return {"active": False, "type": user['subscription_type']}
    
    async def add_gift_knowledge(self, gift_number: int, gift_name: str, 
                                 description: str, characteristics: str, category: str):
        """Добавление информации о даре в базу знаний"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO gifts_knowledge 
                (gift_number, gift_name, description, characteristics, category)
                VALUES (?, ?, ?, ?, ?)
            """, (gift_number, gift_name, description, characteristics, category))
            await db.commit()
    
    async def get_gift_knowledge(self, gift_number: int):
        """Получение информации о даре из базы знаний"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM gifts_knowledge WHERE gift_number = ?", (gift_number,)
            )
            return await cursor.fetchone()
    
    async def update_subscription(self, user_id: int, subscription_type: str, days: int):
        """Обновление подписки пользователя"""
        # Получаем текущую подписку
        user = await self.get_user(user_id)
        
        # Если есть активная подписка, продлеваем от её окончания
        # Иначе начинаем с текущего момента
        if user and user.get('subscription_end_date'):
            # PostgreSQL/Supabase возвращает datetime, SQLite - строку
            current_end = self._parse_dt(user['subscription_end_date'])
            if current_end > datetime.now():
                new_end = current_end + timedelta(days=days)
            else:
                new_end = datetime.now() + timedelta(days=days)
        else:
            new_end = datetime.now() + timedelta(days=days)
        
        if self.use_supabase_api:
            await self._sb(
                lambda: self._supabase.table("telegram_users")
                .update(
                    {
                        "subscription_type": subscription_type,
                        "subscription_end_date": new_end.isoformat(),
                    }
                )
                .eq("user_id", user_id)
                .execute()
            )
        elif self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                async with conn.transaction():
                    await conn.execute("""
                        UPDATE telegram_users 
                        SET subscription_type = $1, subscription_end_date = $2
                        WHERE user_id = $3
                    """, subscription_type, new_end, user_id)
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    UPDATE users 
                    SET subscription_type = ?, subscription_end_date = ?
                    WHERE user_id = ?
                """, (subscription_type, new_end.isoformat(), user_id))
                await db.commit()
        
        return new_end
    
    async def add_payment(self, user_id: int, amount: int, currency: str, 
                         subscription_type: str, status: str = 'completed'):
        """Добавление записи о платеже"""
        payment_date = datetime.now()
        
        if self.use_supabase_api:
            await self._sb(
                lambda: self._supabase.table("telegram_payments")
                .insert(
                    {
                        "user_id": user_id,
                        "amount": amount,
                        "currency": currency,
                        "payment_date": payment_date.isoformat(),
                        "subscription_type": subscription_type,
                        "status": status,
                    }
                )
                .execute()
            )
        elif self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                async with conn.transaction():
                    await conn.execute("""
                        INSERT INTO telegram_payments 
                        (user_id, amount, currency, payment_date, subscription_type, status)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, user_id, amount, currency, payment_date, subscription_type, status)
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO payments 
                    (user_id, amount, currency, payment_date, subscription_type, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (user_id, amount, currency, payment_date.isoformat(), subscription_type, status))
                await db.commit()
    
    async def get_user_payments(self, user_id: int):
        """Получение истории платежей пользователя"""
        if self.use_postgresql:
            async with self._pg_connection_ctx() as conn:
                rows = await conn.fetch("""
                    SELECT * FROM telegram_payments 
                    WHERE user_id = $1 
                    ORDER BY payment_date DESC
                """, user_id)
                return rows
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM payments 
                    WHERE user_id = ? 
                    ORDER BY payment_date DESC
                """, (user_id,))
                return await cursor.fetchall()
    
    async def get_subscription_stats(self):
        """Получение статистики по подпискам"""
        if self.use_supabase_api:
            result = await self._sb(
                lambda: self._supabase.table("telegram_users")
                .select("subscription_type, subscription_end_date")
                .execute()
            )
            stats = {}
            now = datetime.now()
            for row in result.data or []:
                sub_type = row.get("subscription_type") or "unknown"
                stats.setdefault(sub_type, {"count": 0, "active": 0})
                stats[sub_type]["count"] += 1
                end_date = self._parse_dt(row.get("subscription_end_date"))
                if end_date and now < end_date:
                    stats[sub_type]["active"] += 1
            return [(k, v["count"], v["active"]) for k, v in stats.items()]
        if self.use_postgresql:
            async with self._pg_connection_ctx() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        subscription_type,
                        COUNT(*) as count,
                        COUNT(CASE WHEN subscription_end_date > NOW() THEN 1 END) as active_count
                    FROM telegram_users
                    GROUP BY subscription_type
                """)
                return rows
        else:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT 
                        subscription_type,
                        COUNT(*) as count,
                        COUNT(CASE WHEN datetime(subscription_end_date) > datetime('now') THEN 1 END) as active_count
                    FROM users
                    GROUP BY subscription_type
                """)
                return await cursor.fetchall()
    
    async def get_all_users_with_subscriptions(self, limit: int = 50):
        """Получение списка пользователей с подписками"""
        if self.use_supabase_api:
            result = await self._sb(
                lambda: self._supabase.table("telegram_users")
                .select(
                    "user_id, username, first_name, registration_date, "
                    "subscription_type, subscription_end_date, is_admin"
                )
                .order("registration_date", desc=True)
                .limit(limit)
                .execute()
            )
            return result.data
        if self.use_postgresql:
            async with self._pg_connection_ctx() as conn:
                rows = await conn.fetch("""
                    SELECT 
                        user_id,
                        username,
                        first_name,
                        registration_date,
                        subscription_type,
                        subscription_end_date,
                        is_admin
                    FROM telegram_users
                    ORDER BY registration_date DESC
                    LIMIT $1
                """, limit)
                return rows
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT 
                        user_id,
                        username,
                        first_name,
                        registration_date,
                        subscription_type,
                        subscription_end_date,
                        is_admin
                    FROM users
                    ORDER BY registration_date DESC
                    LIMIT ?
                """, (limit,))
                return await cursor.fetchall()
    
    async def init_alphabet_data(self):
        """Инициализация данных алфавита"""
        alphabet_data = [
            ("А", "Оду", "выбор обусловленный вас в точке внешне. Точка судьбы, точка отправления. Если А оформить в Оду - это О."),
            ("Б", "Братья", "соединяющая, объединяющий."),
            ("В", "Воздух", "трансляция, вышка. Как завывает ветер."),
            ("Г", "Грани", "огранка, ограничивающая. Граница которая двигается. Тут много алхимических процессов."),
            ("Д", "Дума", "обладает внешними границами. Потенциальная точка входа, которая обладает внешними границами. Есть нахальность и потенциальность. Развилка."),
            ("Е", "", ""),
            ("Ж", "Жизнь", "сила, рождающая жизнь"),
            ("З", "Зета", "разрез, зеркало. Зевать. Процесс разделения. Как секира. Активно действует. Отрывающая. Я тебя срезал."),
            ("И", "", "связь, вспомогательная, более подвижная связь. Если И возвести в Оду - получается Н."),
            ("Й", "", "если И оплодотворить райдой. Более активное движение"),
            ("К", "Кама", "кодировка. Кодировка в поле МА. Работаем где-то с потенциалом. С тем, чего еще не существует в принципе."),
            ("Л", "Лота", "лезвие, разделяющий, линия. С твердыми, проявленными объектами. Отделить одно тело от другого. Работает еще и с Духом. Имеет выбор с чем работать. Вычерчивает границу от тебя. Отстаивания подвижных границ. Я устанавливаю правило границ"),
            ("М", "Мана", "то что рождает выбор, создающий связи выбора. Мама рождает ребенка, который может родить еще одного ребенка. Одно рождает другое."),
            ("Н", "Нита", "натянутая нить. Связи."),
            ("О", "Ома", "если она присутствует - значит есть душа"),
            ("П", "Приа", "портал, проникновение, пушка, поход, путешествие, поддержка. Портал, который С чем-то связывает. Связь с внешним объектом. П часто зависима. Она пропускает. Место куда мы идем зависит от места, где мы находимся. Выбор объекта, куда мы придем."),
            ("Р", "Райда", "движение выбора связующее с внешним действием. Путь, стрела, толкающий. АКТИВНОСТЬ"),
            ("С", "Сутра", "связующая. Что-то связующее с точкой, обладающее двигающим выбором. Одно синхронизировано с другим. Та что готова синхронизироваться. Провод от розетки"),
            ("Т", "ТаАта", "тело. Сосуд, который имеет автоматический объект. Предмет. Не наделенное Духом. Наделить - Таата бра Ома."),
            ("У", "", "точка входа"),
            ("Ф", "Фата, фита", "КЛЮЧ. То, что открывает, вскрывает поле Ома, как ключом. Фа - подсознание, Фи - осознание. Фа - мы проникаем, фи - связываемся. Вверх активно, вниз нас ведут. Фата ты имеешь право выбора, а фита - выбора нет, за тебя выбирают."),
            ("Х", "Храм", "то место, где начинается действие."),
            ("Ц", "Циа", "возвышение. Энергия Ци. Подцепить, цеплять, цепь. Подхватывает из-под низа и поднимает наверх."),
            ("Ч", "Чиа", "экосистемы, энергоцентр. Черта связующая с выбором. Кто-то провел черту от высших вниз. Кто-то сверху спустился вниз. Можно спускаться вниз. Как заземлитесь. Или провести черту. Черчение. Буква Л только с Божественной волей."),
            ("Ш", "Ши", "внимание, внимание куда-либо стремится, связаться с чем-либо. Ши - это как руки к небу - энергия опускается через руки и попадает в ШишкУ."),
            ("Щ", "", ""),
            ("Ы", "", ""),
            ("Э", "", ""),
            ("Ю", "Юдл", "состоит из Й + У. Если И оплодотворить райдой + точка входа"),
            ("Я", "ЙА", "состоит из Й + А. Если И оплодотворить райдой + Оду (точка судьбы, выбор)")
        ]
        
        if self.use_supabase_api:
            payload = [
                {"letter": letter, "name": name, "description": description}
                for letter, name, description in alphabet_data
            ]
            await self._sb(
                lambda: self._supabase.table("telegram_alphabet")
                .upsert(payload, on_conflict="letter")
                .execute()
            )
        elif self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                async with conn.transaction():
                    for letter, name, description in alphabet_data:
                        await conn.execute("""
                            INSERT INTO telegram_alphabet (letter, name, description)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (letter) DO NOTHING
                        """, letter, name, description)
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                for letter, name, description in alphabet_data:
                    await db.execute("""
                        INSERT OR IGNORE INTO alphabet (letter, name, description)
                        VALUES (?, ?, ?)
                    """, (letter, name, description))
                await db.commit()
    
    async def get_letter_meaning(self, letter: str):
        """Получение значения буквы"""
        if self.use_supabase_api:
            result = await self._sb(
                lambda: self._supabase.table("telegram_alphabet")
                .select("*")
                .eq("letter", letter.upper())
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                row = await conn.fetchrow(
                    "SELECT * FROM telegram_alphabet WHERE letter = $1", letter.upper()
                )
                return row
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM alphabet WHERE letter = ?", (letter.upper(),)
                )
                return await cursor.fetchone()
    
    async def get_all_alphabet(self):
        """Получение всего алфавита"""
        if self.use_supabase_api:
            result = await self._sb(
                lambda: self._supabase.table("telegram_alphabet")
                .select("*")
                .order("id")
                .execute()
            )
            return result.data
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                rows = await conn.fetch("SELECT * FROM telegram_alphabet ORDER BY id")
                return rows
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT * FROM alphabet ORDER BY id")
                return await cursor.fetchall()
    
    # ========== АДМИНИСТРАТИВНЫЕ ФУНКЦИИ ==========
    
    async def is_admin(self, user_id: int) -> bool:
        """Проверка прав администратора"""
        user = await self.get_user(user_id)
        if not user:
            return False
        # PostgreSQL возвращает boolean через asyncpg.Record, SQLite - integer через Row
        # asyncpg.Record поддерживает доступ как к словарю
        is_admin_value = user['is_admin']
        if isinstance(is_admin_value, bool):
            return is_admin_value
        return is_admin_value == 1
    
    async def set_admin(self, user_id: int, is_admin: bool = True):
        """Выдать/снять права администратора"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if self.use_supabase_api:
                existing = await self._sb(
                    lambda: self._supabase.table("telegram_users")
                    .select("user_id")
                    .eq("user_id", user_id)
                    .limit(1)
                    .execute()
                )
                if existing.data:
                    await self._sb(
                        lambda: self._supabase.table("telegram_users")
                        .update({"is_admin": is_admin})
                        .eq("user_id", user_id)
                        .execute()
                    )
                else:
                    registration_date = datetime.now().isoformat()
                    await self._sb(
                        lambda: self._supabase.table("telegram_users")
                        .insert(
                            {
                                "user_id": user_id,
                                "registration_date": registration_date,
                                "is_admin": is_admin,
                            }
                        )
                        .execute()
                    )
                logger.info(f"Права администратора для пользователя {user_id} успешно сохранены: {is_admin}")
            elif self.use_postgresql:
                conn = await self._get_pg_connection()
                try:
                    # Проверяем, существует ли пользователь
                    existing_user = await conn.fetchval(
                        "SELECT user_id FROM telegram_users WHERE user_id = $1", user_id
                    )
                    
                    if not existing_user:
                        # Пользователь не существует - создаем его с правами администратора
                        registration_date = datetime.now()
                        logger.info(f"Создание нового пользователя {user_id} с правами администратора")
                        async with conn.transaction():
                            await conn.execute("""
                                INSERT INTO telegram_users 
                                (user_id, username, first_name, registration_date, is_admin)
                                VALUES ($1, $2, $3, $4, $5)
                            """, user_id, None, None, registration_date, is_admin)
                    else:
                        # Пользователь существует - обновляем права
                        logger.info(f"Обновление прав администратора для пользователя {user_id}: {is_admin}")
                        async with conn.transaction():
                            await conn.execute(
                                "UPDATE telegram_users SET is_admin = $1 WHERE user_id = $2",
                                is_admin, user_id
                            )
                    
                    # Проверяем, что изменения сохранились
                    saved_is_admin = await conn.fetchval(
                        "SELECT is_admin FROM telegram_users WHERE user_id = $1", user_id
                    )
                    if saved_is_admin is None:
                        error_msg = f"Пользователь {user_id} не был сохранен в базу данных"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    logger.info(f"Права администратора для пользователя {user_id} успешно сохранены: {is_admin}")
                finally:
                    await self._release_pg_connection(conn)
            else:
                async with aiosqlite.connect(self.db_path) as db:
                    # Устанавливаем настройки для надежной записи
                    await db.execute("PRAGMA synchronous = NORMAL")
                    
                    # Проверяем, существует ли пользователь
                    cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
                    existing_user = await cursor.fetchone()
                    
                    if not existing_user:
                        # Пользователь не существует - создаем его с правами администратора
                        registration_date = datetime.now().isoformat()
                        logger.info(f"Создание нового пользователя {user_id} с правами администратора")
                        await db.execute("""
                            INSERT INTO users 
                            (user_id, username, first_name, registration_date, is_admin)
                            VALUES (?, ?, ?, ?, ?)
                        """, (user_id, None, None, registration_date, 1 if is_admin else 0))
                    else:
                        # Пользователь существует - обновляем права
                        logger.info(f"Обновление прав администратора для пользователя {user_id}: {is_admin}")
                        await db.execute(
                            "UPDATE users SET is_admin = ? WHERE user_id = ?",
                            (1 if is_admin else 0, user_id)
                        )
                    await db.commit()
                    
                    # Проверяем, что изменения сохранились
                    cursor = await db.execute("SELECT is_admin FROM users WHERE user_id = ?", (user_id,))
                    saved_user = await cursor.fetchone()
                    if not saved_user:
                        error_msg = f"Пользователь {user_id} не был сохранен в базу данных"
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    
                    logger.info(f"Права администратора для пользователя {user_id} успешно сохранены: {is_admin}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении прав администратора для пользователя {user_id}: {e}", exc_info=True)
            raise
    
    async def get_all_admins(self):
        """Получить список всех админов"""
        if self.use_postgresql:
            async with self._pg_connection_ctx() as conn:
                rows = await conn.fetch("""
                    SELECT user_id, username, first_name 
                    FROM telegram_users 
                    WHERE is_admin = TRUE
                """)
                return rows
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT user_id, username, first_name FROM users WHERE is_admin = 1"
                )
                return await cursor.fetchall()
    
    # ========== ПРОМОКОДЫ ==========
    
    async def create_promocode(self, code: str, promo_type: str, created_by: int,
                               discount_percent: int = None, subscription_days: int = None,
                               subscription_type: str = None, max_uses: int = None):
        """Создание промокода
        
        Args:
            code: Код промокода
            promo_type: Тип ('discount' или 'subscription')
            created_by: ID админа, создавшего промокод
            discount_percent: Процент скидки (для discount)
            subscription_days: Дни подписки (для subscription)
            subscription_type: Тип подписки ('pro' или 'orden') для subscription промокодов
            max_uses: Максимальное количество использований (None = безлимит)
        """
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            if self.use_supabase_api:
                created_date = datetime.now().isoformat()
                result = await self._sb(
                    lambda: self._supabase.table("telegram_promocodes")
                    .insert(
                        {
                            "code": code,
                            "type": promo_type,
                            "discount_percent": discount_percent,
                            "subscription_days": subscription_days,
                            "subscription_type": subscription_type,
                            "max_uses": max_uses,
                            "created_date": created_date,
                            "created_by": created_by,
                            "current_uses": 0,
                            "is_active": True,
                        }
                    )
                    .execute()
                )
                promo = result.data[0] if result.data else None
                if not promo:
                    raise Exception(f"Промокод {code} не был сохранен в базе данных")
                logger.info(f"Промокод {code} успешно создан с ID {promo.get('id')}")
            elif self.use_postgresql:
                # PostgreSQL
                conn = await self._get_pg_connection()
                try:
                    created_date = datetime.now()
                    async with conn.transaction():
                        promo_id = await conn.fetchval("""
                            INSERT INTO telegram_promocodes 
                            (code, type, discount_percent, subscription_days, subscription_type, max_uses, created_date, created_by)
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                            RETURNING id
                        """, code, promo_type, discount_percent, subscription_days, subscription_type, max_uses, created_date, created_by)
                    
                    # Проверяем, что промокод действительно сохранен
                    saved_promo = await conn.fetchrow(
                        "SELECT id, code FROM telegram_promocodes WHERE id = $1", promo_id
                    )
                    if not saved_promo:
                        raise Exception(f"Промокод {code} не был сохранен в базу данных")
                    
                    logger.info(f"Промокод {code} успешно создан с ID {promo_id}")
                finally:
                    await self._release_pg_connection(conn)
            else:
                # SQLite
                async with aiosqlite.connect(self.db_path) as conn:
                    # Устанавливаем настройки для надежной записи
                    await conn.execute("PRAGMA synchronous = NORMAL")
                    
                    created_date = datetime.now().isoformat()
                    cursor = await conn.execute("""
                        INSERT INTO promocodes 
                        (code, type, discount_percent, subscription_days, subscription_type, max_uses, created_date, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (code, promo_type, discount_percent, subscription_days, subscription_type, max_uses, created_date, created_by))
                    await conn.commit()
                    
                    # Получаем ID созданного промокода для проверки
                    promo_id = cursor.lastrowid
                    
                    # Проверяем, что промокод действительно сохранен
                    check_cursor = await conn.execute("SELECT id, code FROM promocodes WHERE id = ?", (promo_id,))
                    saved_promo = await check_cursor.fetchone()
                    if not saved_promo:
                        raise Exception(f"Промокод {code} не был сохранен в базу данных")
                    
                    logger.info(f"Промокод {code} успешно создан с ID {promo_id}")
                
        except Exception as e:
            logger.error(f"Ошибка при создании промокода {code}: {e}", exc_info=True)
            raise
    
    async def get_promocode(self, code: str):
        """Получение промокода по коду"""
        if self.use_supabase_api:
            result = await self._sb(
                lambda: self._supabase.table("telegram_promocodes")
                .select("*")
                .eq("code", code)
                .eq("is_active", True)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                row = await conn.fetchrow(
                    "SELECT * FROM telegram_promocodes WHERE code = $1 AND is_active = TRUE", code
                )
                return row
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM promocodes WHERE code = ? AND is_active = 1", (code,)
                )
                return await cursor.fetchone()
    
    async def check_user_used_promocode(self, user_id: int, promocode_id: int) -> bool:
        """Проверка, использовал ли пользователь промокод"""
        if self.use_supabase_api:
            result = await self._sb(
                lambda: self._supabase.table("telegram_promocode_usage")
                .select("id")
                .eq("user_id", user_id)
                .eq("promocode_id", promocode_id)
                .limit(1)
                .execute()
            )
            return bool(result.data)
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM telegram_promocode_usage 
                    WHERE user_id = $1 AND promocode_id = $2
                """, user_id, promocode_id)
                return count > 0
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("""
                    SELECT COUNT(*) as count FROM promocode_usage 
                    WHERE user_id = ? AND promocode_id = ?
                """, (user_id, promocode_id))
                result = await cursor.fetchone()
                return result[0] > 0
    
    async def use_promocode(self, user_id: int, promocode_id: int):
        """Зарегистрировать использование промокода"""
        if self.use_supabase_api:
            usage_date = datetime.now().isoformat()
            await self._sb(
                lambda: self._supabase.table("telegram_promocode_usage")
                .insert(
                    {
                        "promocode_id": promocode_id,
                        "user_id": user_id,
                        "usage_date": usage_date,
                    }
                )
                .execute()
            )
            current = await self._sb(
                lambda: self._supabase.table("telegram_promocodes")
                .select("current_uses")
                .eq("id", promocode_id)
                .limit(1)
                .execute()
            )
            current_uses = 0
            if current.data:
                current_uses = current.data[0].get("current_uses") or 0
            await self._sb(
                lambda: self._supabase.table("telegram_promocodes")
                .update({"current_uses": current_uses + 1})
                .eq("id", promocode_id)
                .execute()
            )
        elif self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                usage_date = datetime.now()
                
                async with conn.transaction():
                    # Добавляем запись об использовании
                    await conn.execute("""
                        INSERT INTO telegram_promocode_usage (promocode_id, user_id, usage_date)
                        VALUES ($1, $2, $3)
                    """, promocode_id, user_id, usage_date)
                    
                    # Увеличиваем счетчик использований
                    await conn.execute("""
                        UPDATE telegram_promocodes SET current_uses = current_uses + 1
                        WHERE id = $1
                    """, promocode_id)
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                usage_date = datetime.now().isoformat()
                
                # Добавляем запись об использовании
                await db.execute("""
                    INSERT INTO promocode_usage (promocode_id, user_id, usage_date)
                    VALUES (?, ?, ?)
                """, (promocode_id, user_id, usage_date))
                
                # Увеличиваем счетчик использований
                await db.execute("""
                    UPDATE promocodes SET current_uses = current_uses + 1
                    WHERE id = ?
                """, (promocode_id,))
                
                await db.commit()
    
    async def deactivate_promocode(self, code: str):
        """Деактивировать промокод"""
        if self.use_supabase_api:
            await self._sb(
                lambda: self._supabase.table("telegram_promocodes")
                .update({"is_active": False})
                .eq("code", code)
                .execute()
            )
        elif self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                async with conn.transaction():
                    await conn.execute(
                        "UPDATE telegram_promocodes SET is_active = FALSE WHERE code = $1", code
                    )
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE promocodes SET is_active = 0 WHERE code = ?", (code,)
                )
                await db.commit()
    
    async def delete_promocode(self, promo_id: int):
        """Удалить промокод из базы данных"""
        if self.use_supabase_api:
            await self._sb(
                lambda: self._supabase.table("telegram_promocode_usage")
                .delete()
                .eq("promocode_id", promo_id)
                .execute()
            )
            await self._sb(
                lambda: self._supabase.table("telegram_promocodes")
                .delete()
                .eq("id", promo_id)
                .execute()
            )
        elif self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                async with conn.transaction():
                    # Сначала удаляем все использования промокода
                    await conn.execute(
                        "DELETE FROM telegram_promocode_usage WHERE promocode_id = $1", promo_id
                    )
                    # Затем удаляем сам промокод
                    await conn.execute(
                        "DELETE FROM telegram_promocodes WHERE id = $1", promo_id
                    )
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                # Сначала удаляем все использования промокода
                await db.execute(
                    "DELETE FROM promocode_usage WHERE promocode_id = ?", (promo_id,)
                )
                # Затем удаляем сам промокод
                await db.execute(
                    "DELETE FROM promocodes WHERE id = ?", (promo_id,)
                )
                await db.commit()
    
    async def get_all_promocodes(self):
        """Получить список всех промокодов"""
        if self.use_supabase_api:
            result = await self._sb(
                lambda: self._supabase.table("telegram_promocodes")
                .select("*")
                .order("created_date", desc=True)
                .execute()
            )
            return result.data
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                rows = await conn.fetch("""
                    SELECT * FROM telegram_promocodes ORDER BY created_date DESC
                """)
                return rows
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM promocodes ORDER BY created_date DESC
                """)
                return await cursor.fetchall()
    
    async def get_promocode_stats(self, code: str):
        """Получить статистику по промокоду"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Получаем промокод
            promo_cursor = await db.execute(
                "SELECT * FROM promocodes WHERE code = ?", (code,)
            )
            promo = await promo_cursor.fetchone()
            
            if not promo:
                return None
            
            # Получаем список использований
            usage_cursor = await db.execute("""
                SELECT u.username, u.first_name, pu.usage_date
                FROM promocode_usage pu
                JOIN users u ON pu.user_id = u.user_id
                WHERE pu.promocode_id = ?
                ORDER BY pu.usage_date DESC
            """, (promo['id'],))
            usage_list = await usage_cursor.fetchall()
            
            return {
                'promocode': promo,
                'usage_list': usage_list
            }
    
    # ========== АЛХИМИЯ ДАРОВ (МА-ЖИ-КУН ПОЗИЦИИ И ПОЛЯ) ==========
    
    async def init_ma_zhi_kun_data(self):
        """Инициализация данных позиций Ма-Жи-Кун"""
        positions_data = [
            ("МА", "Мир непроявленного потенциала. Содержит идеи, желания, воспоминания — всё вне текущего фокуса внимания. Находится сзади/внутри. Соответствует будущему. Энергия: внутренний потенциал."),
            ("ЖИ", "Мир проявленной реальности. Всё, что наблюдаем и ощущаем прямо сейчас: предметы, мысли, эмоции. Находится впереди/снаружи. Соответствует прошлому. Энергия: внешняя материальность."),
            ("КУН", "Процесс творения и перехода между МА и ЖИ. Активный акт созидания в точке «здесь и сейчас». Осознанные действия и наблюдение. Находится посередине. Энергия: подвижная, творящая реальность.")
        ]
        
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                async with conn.transaction():
                    for name, description in positions_data:
                        await conn.execute("""
                            INSERT INTO telegram_ma_zhi_kun_positions (name, description)
                            VALUES ($1, $2)
                            ON CONFLICT (name) DO UPDATE SET description = $2
                        """, name, description)
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                for name, description in positions_data:
                    await db.execute("""
                        INSERT OR REPLACE INTO ma_zhi_kun_positions (name, description)
                        VALUES (?, ?)
                    """, (name, description))
                await db.commit()
    
    async def init_gift_fields_data(self):
        """Инициализация данных полей (1-9)"""
        fields_data = [
            (1, "Логос", "Структура, архитектура пространства. Форма - треугольник. В теле: копчик. Вкус: соленый. Ощущение: сухой, сохраниние, поглощающий. Цвет: красный. Стихия: внутренняя Земля, сохраниение."),
            (2, "Нима", "Пространство, бесконечность. В теле: таз, низ живота. Форма - пространство. Ощущение: мягкое, расширяющее. Цвет: голубой. Стихия: внутренний Воздух. Вкус: кислый."),
            (3, "Андра", "Соединение и разьединение. В теле: живот, поясница. Ощущение: Острое, треск/надлом. Цвет: зелёный. Форма: ветвистость. Стихия: внутренняя Вода. Вкус: острый."),
            (4, "Зингра", "Процесс горения и трансформации. Законы: необратимое изменение, испытание. В теле: солнечное сплетение. Ощущение: текстурное, стремлнение, изменяющий. Вкус: горький. Цвет: желтый. Стихия: внутренний Огонь. Драйв, смелость, сила прорыва, трансформация. Форма: спираль."),
            (5, "Луба", "Солнце, центр. Форма - точка. В теле: сердечный центр. Ощущение: наполняющее, творение. Цвет: белый. Стихия: Внешний Огонь. Вкус: широкий. Дар: единство, стремление к точке, энергия, воля. "),
            (6, "Тума", "Постоянное движение, синхронистичность, цикличность. В теле: грудная клетка. Ощущение: гладкое, притяжение, динамичный. Цвет: Синий, фиолетовый. Стихия: внешняя Вода (поток). Дар: Время, движение. Вкус: сладкий. Форма: волна."),
            (7, "Астра", "Канал между мирами. Путь, канал. В теле: горло. Ощущение: влажное, связующий, пряный. Цвет: фиолетовый. Стихия: Внешний воздух. Связи, коммуникация, каналы между обьектами. Форма: линия."),
            (8, "Битра", "Граница, форма, оболочка. В теле: лоб, третий глаз. Ощущение: твердое, обрамляющий, терпкий. Цвет: оранжевый. Стихия: внешняя Земля. Форма: круг."),
            (9, "Ома", "Пробуждение центральной силы (Кундалини). Всё есть Одно, прямое переживание, трансценденция. В теле: позвоночник. Ощущение: восходящий поток, экстатическая полнота. Цвет: радужный. Стихия: Эфир. Целостность, просветление, активация. Форма - любая, так как содержит в себе все.")
        ]
        
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                async with conn.transaction():
                    for field_id, name, description in fields_data:
                        await conn.execute("""
                            INSERT INTO telegram_gift_fields (id, name, description)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (id) DO UPDATE SET name = $2, description = $3
                        """, field_id, name, description)
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                for field_id, name, description in fields_data:
                    await db.execute("""
                        INSERT OR REPLACE INTO gift_fields (id, name, description)
                        VALUES (?, ?, ?)
                    """, (field_id, name, description))
                await db.commit()
    
    async def get_ma_zhi_kun_position(self, name: str):
        """Получение информации о позиции Ма-Жи-Кун"""
        if self.use_supabase_api:
            result = await self._sb(
                lambda: self._supabase.table("telegram_ma_zhi_kun_positions")
                .select("*")
                .eq("name", name)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                row = await conn.fetchrow(
                    "SELECT * FROM telegram_ma_zhi_kun_positions WHERE name = $1", name
                )
                return row
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM ma_zhi_kun_positions WHERE name = ?", (name,)
                )
                return await cursor.fetchone()
    
    async def get_gift_field(self, field_id: int):
        """Получение информации о поле по ID"""
        if self.use_supabase_api:
            result = await self._sb(
                lambda: self._supabase.table("telegram_gift_fields")
                .select("*")
                .eq("id", field_id)
                .limit(1)
                .execute()
            )
            return result.data[0] if result.data else None
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                row = await conn.fetchrow(
                    "SELECT * FROM telegram_gift_fields WHERE id = $1", field_id
                )
                return row
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM gift_fields WHERE id = ?", (field_id,)
                )
                return await cursor.fetchone()
    
    async def get_all_ma_zhi_kun_positions(self):
        """Получение всех позиций Ма-Жи-Кун"""
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                rows = await conn.fetch(
                    "SELECT * FROM telegram_ma_zhi_kun_positions ORDER BY name"
                )
                return rows
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM ma_zhi_kun_positions ORDER BY name"
                )
                return await cursor.fetchall()
    
    async def get_all_gift_fields(self):
        """Получение всех полей"""
        if self.use_postgresql:
            conn = await self._get_pg_connection()
            try:
                rows = await conn.fetch(
                    "SELECT * FROM telegram_gift_fields ORDER BY id"
                )
                return rows
            finally:
                await self._release_pg_connection(conn)
        else:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM gift_fields ORDER BY id"
                )
                return await cursor.fetchall()

