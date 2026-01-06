"""
Управление SQLite базой данных для бота
"""
import aiosqlite
import os
from datetime import datetime, timedelta
from config import Config

class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.DATABASE_PATH
        
    async def init_db(self):
        """Инициализация базы данных и создание таблиц"""
        # Создаем директорию для базы данных, если её нет
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
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
                    is_active INTEGER DEFAULT 1
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
            
            await db.commit()
    
    async def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Добавление нового пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            registration_date = datetime.now().isoformat()
            trial_end = (datetime.now() + timedelta(days=Config.TRIAL_DURATION_DAYS)).isoformat()
            
            await db.execute("""
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, registration_date, subscription_type, subscription_end_date)
                VALUES (?, ?, ?, ?, 'trial', ?)
            """, (user_id, username, first_name, registration_date, trial_end))
            await db.commit()
    
    async def get_user(self, user_id: int):
        """Получение данных пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
            return await cursor.fetchone()
    
    async def update_user_birth_date(self, user_id: int, birth_date: str):
        """Обновление даты рождения пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET birth_date = ? WHERE user_id = ?",
                (birth_date, user_id)
            )
            await db.commit()
    
    async def save_calculation(self, user_id: int, calc_type: str, birth_date: str, result_data: str):
        """Сохранение результата расчета"""
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
            end_date = datetime.fromisoformat(user['subscription_end_date'])
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
        async with aiosqlite.connect(self.db_path) as db:
            # Получаем текущую подписку
            user = await self.get_user(user_id)
            
            # Если есть активная подписка, продлеваем от её окончания
            # Иначе начинаем с текущего момента
            if user and user['subscription_end_date']:
                current_end = datetime.fromisoformat(user['subscription_end_date'])
                if current_end > datetime.now():
                    new_end = current_end + timedelta(days=days)
                else:
                    new_end = datetime.now() + timedelta(days=days)
            else:
                new_end = datetime.now() + timedelta(days=days)
            
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
        async with aiosqlite.connect(self.db_path) as db:
            payment_date = datetime.now().isoformat()
            await db.execute("""
                INSERT INTO payments 
                (user_id, amount, currency, payment_date, subscription_type, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, amount, currency, payment_date, subscription_type, status))
            await db.commit()
    
    async def get_user_payments(self, user_id: int):
        """Получение истории платежей пользователя"""
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
            ("Ю", "ЙУ", "состоит из Й + У. Если И оплодотворить райдой + точка входа"),
            ("Я", "ЙА", "состоит из Й + А. Если И оплодотворить райдой + Оду (точка судьбы, выбор)")
        ]
        
        async with aiosqlite.connect(self.db_path) as db:
            for letter, name, description in alphabet_data:
                await db.execute("""
                    INSERT OR IGNORE INTO alphabet (letter, name, description)
                    VALUES (?, ?, ?)
                """, (letter, name, description))
            await db.commit()
    
    async def get_letter_meaning(self, letter: str):
        """Получение значения буквы"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM alphabet WHERE letter = ?", (letter.upper(),)
            )
            return await cursor.fetchone()
    
    async def get_all_alphabet(self):
        """Получение всего алфавита"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM alphabet ORDER BY id")
            return await cursor.fetchall()

