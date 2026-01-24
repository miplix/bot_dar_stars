"""
Основной файл Telegram бота для работы с дарами
"""
import asyncio
import logging
import json
import secrets
import string
import random
import re
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.exceptions import TelegramBadRequest

from src.config import Config
from src.database import Database
from src.calculations import GiftsCalculator
from src.ai_handler import AIHandler
from src.keyboards import get_main_menu, get_subscription_menu, get_premium_options_menu, get_mantras_menu, get_mantra_create_options_menu, get_alphabet_menu, get_admin_menu, get_predictions_menu
from src.mantras import create_mantra_random, create_mantra_by_request, parse_mantra
from src.alphabet_knowledge import AlphabetAnalyzer, check_if_gift_or_command

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация
bot = Bot(token=Config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
db = Database()
calculator = GiftsCalculator()
ai_handler = AIHandler()
alphabet_analyzer = AlphabetAnalyzer(db, ai_handler)

# Вспомогательная функция для безопасного редактирования сообщений
async def safe_edit_text(message, text: str, reply_markup=None, parse_mode=None, **kwargs):
    """
    Безопасное редактирование сообщения с обработкой ошибки 'message is not modified'
    
    Args:
        message: Сообщение для редактирования (Message или CallbackQuery.message)
        text: Текст сообщения
        reply_markup: Разметка клавиатуры (опционально)
        parse_mode: Режим парсинга (опционально)
        **kwargs: Дополнительные параметры для edit_text
    
    Returns:
        bool: True если редактирование успешно, False если сообщение не изменилось
    """
    try:
        await message.edit_text(text, reply_markup=reply_markup, parse_mode=parse_mode, **kwargs)
        return True
    except TelegramBadRequest as e:
        # Игнорируем ошибку "message is not modified" - это не критично
        if "message is not modified" in str(e).lower():
            return False
        # Если другая ошибка - логируем и пробрасываем
        logger.error(f"Ошибка при редактировании сообщения: {e}", exc_info=True)
        raise

# Состояния FSM
class UserStates(StatesGroup):
    waiting_for_birth_date = State()
    waiting_for_question = State()
    
    # Состояния для комплексного расчета
    waiting_for_complete_birth_date = State()
    waiting_for_birth_time = State()
    waiting_for_location = State()
    waiting_for_first_name = State()
    waiting_for_last_name = State()
    
    # Состояния для работы с сантрами
    waiting_for_mantra_request = State()
    waiting_for_mantra_by_theme = State()  # Ожидание выбора темы или ввода запроса
    waiting_for_mantra_to_analyze = State()
    
    # Состояния для работы с алфавитом
    waiting_for_word_to_analyze = State()
    
    # Состояния для промокодов
    waiting_for_promocode = State()
    
    # Состояния для админов
    waiting_for_promo_type = State()
    waiting_for_promo_sub_type = State()  # Выбор типа подписки (pro/orden) для промокода
    waiting_for_promo_value = State()
    waiting_for_promo_max_uses = State()
    
    # Состояния для алхимии даров
    waiting_for_alchemy_numbers = State()
    
    # Состояния для предсказаний
    waiting_for_prediction_birth_date = State()  # Дата рождения для предсказания
    waiting_for_prediction_event = State()  # Описание события
    waiting_for_prediction_partner_birth_date = State()  # Дата рождения партнера

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Добавляем пользователя в базу данных
    await db.add_user(user_id, username, first_name)
    
    # Проверяем подписку
    subscription = await check_subscription_with_admin(user_id)
    
    welcome_text = f"""👋 *Добро пожаловать, {first_name}!*

🎁 Я помогу вам раскрыть ваши дары, заложенные при рождении по древнеславянской системе *Ма-Жи-Кун*.

🔮 Доступны два типа расчета:

*1. Базовый расчет (Ода)* - по дате рождения
• *Ма* - энергия дня и месяца
• *Жи* - энергия года
• *Кун* - ваш главный дар

*2. Комплексный расчет* - полный профиль
• 🎁 *ОДА* - дата рождения (главное)
• 🌙 *ТУНА* - время рождения
• 🌍 *ТРИА* - место рождения
• 💫 *ЧИА* - имя и фамилия

✨ Всего существует *64 дара*, каждый из которых открывает уникальные способности и таланты.

🤖 Все расчеты анализируются с помощью ИИ для получения полной картины.

"""
    
    if subscription['active']:
        welcome_text += f"✅ У вас активна подписка: *{subscription['type'].upper()}*\n"
        if subscription.get('end_date'):
            welcome_text += f"Действительна до: `{subscription['end_date'].strftime('%d.%m.%Y')}`\n"
    else:
        welcome_text += f"🎁 У вас пробный период на *{Config.TRIAL_DURATION_DAYS} дней*!\n"
    
    welcome_text += "\n📝 Используйте меню ниже для начала работы:"
    
    await message.answer(welcome_text, reply_markup=get_main_menu(subscription), parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработка команды /help"""
    help_text = """❓ *Помощь по использованию бота*

*Доступные команды:*
/start - Начать работу с ботом
/calculate - Рассчитать свои дары (Ода)
/complete - Комплексный расчет всех даров
/subscription - Управление подпиской
/help - Показать эту справку

━━━━━━━━━━━━━━━━━━

📊 *Система Ма-Жи-Кун*

Это древнеславянская система расчета даров по дате рождения:

🔢 *Ма* - сумма цифр дня и месяца рождения
🔢 *Жи* - сумма цифр года рождения
🎁 *Кун* - ваш главный дар (Ма + Жи)

━━━━━━━━━━━━━━━━━━

🎭 *Комплексный расчет* включает 4 компонента:

🎁 *ОДА* - основные данные (дата рождения)
_Главное влияние на личность_

🌙 *ТУНА* - время рождения
_Временной аспект_

🌍 *ТРИА* - место рождения
_Энергия места_

💫 *ЧИА* - имя и фамилия
_Влияние имени на судьбу_

✨ Всего в системе *64 уникальных дара*, каждый со своим названием, энергетикой и предназначением.

🤖 Бот использует ИИ для глубокого анализа вашего дара и практических рекомендаций.
"""
    user_id = message.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    await message.answer(help_text, reply_markup=get_main_menu(subscription), parse_mode="Markdown")

@dp.message(Command("calculate"))
async def cmd_calculate(message: Message, state: FSMContext):
    """Начало расчета даров"""
    await message.answer(
        "📅 Введите вашу дату рождения в формате ДД.ММ.ГГГГ\n\nНапример: 15.05.1990",
        reply_markup=None
    )
    await state.set_state(UserStates.waiting_for_birth_date)

@dp.message(Command("complete"))
async def cmd_complete_calculate(message: Message, state: FSMContext):
    """Начало комплексного расчета всех даров"""
    user_id = message.from_user.id
    
    # Проверяем подписку
    subscription = await check_subscription_with_admin(user_id)
    if not subscription['active']:
        text = """⚠️ *Подписка не активна*

Для комплексного расчета необходима активная подписка.

⭐️ *Премиум подписка:*
📅 Месяц - {month_price} ⭐️
📆 Год - {year_price} ⭐️

🎁 Что вы получите:
• Безлимитные расчеты даров
• Полный анализ с ИИ
• Персональные рекомендации
• Расширенные трактовки

_Нажмите кнопку ниже для оформления подписки_
""".format(
            month_price=Config.PRO_MONTH_PRICE,
            year_price=Config.PRO_YEAR_PRICE
        )
        await message.answer(
            text,
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        return
    
    welcome_msg = """🔮 *Комплексный расчет всех даров*

Я рассчитаю для вас полный профиль по четырем компонентам:

🎁 *ОДА* - основные данные (дата рождения)
_Главное влияние на личность_

🌙 *ТУНА* - второстепенные (время рождения)
_Влияние временного аспекта_

🌍 *ТРИА* - третьестепенные (место рождения)
_Энергия места_

💫 *ЧИА* - четверостепенные (имя и фамилия)
_Влияние имени на судьбу_

━━━━━━━━━━━━━━━━━━

Начнем! 📅 Введите вашу дату рождения в формате ДД.ММ.ГГГГ

Например: 15.05.1990"""
    
    await message.answer(welcome_msg, parse_mode="Markdown")
    await state.set_state(UserStates.waiting_for_complete_birth_date)

@dp.message(UserStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    """Обработка введенной даты рождения"""
    birth_date = message.text.strip()
    user_id = message.from_user.id
    
    # Проверяем подписку
    subscription = await check_subscription_with_admin(user_id)
    if not subscription['active']:
        text = """⚠️ *Подписка не активна*

Для расчета даров необходима активная подписка.

⭐️ *Премиум подписка:*
📅 Месяц - {month_price} ⭐️
📆 Год - {year_price} ⭐️

🎁 Что вы получите:
• Безлимитные расчеты даров
• Полный анализ с ИИ
• Персональные рекомендации
• Расширенные трактовки

_Нажмите кнопку ниже для оформления подписки_
""".format(
            month_price=Config.PRO_MONTH_PRICE,
            year_price=Config.PRO_YEAR_PRICE
        )
        await message.answer(
            text,
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    try:
        # Рассчитываем все дары
        results = calculator.calculate_all_gifts(birth_date)
        
        if results['status'] == 'error':
            await message.answer(
                f"❌ Ошибка: {results['error']}\n\nПопробуйте еще раз в формате ДД.ММ.ГГГГ"
            )
            return
        
        # Сохраняем дату рождения пользователя
        await db.update_user_birth_date(user_id, birth_date)
        
        # Сохраняем результаты расчета
        await db.save_calculation(
            user_id, 
            'full_calculation',
            birth_date,
            json.dumps(results, ensure_ascii=False)
        )
        
        # Отправляем сообщение о начале анализа
        processing_msg = await message.answer("🔮 Анализирую ваши дары с помощью ИИ...")
        
        # Получаем трактовку от ИИ
        interpretation = await ai_handler.get_gift_interpretation(results)
        
        # Удаляем сообщение о обработке
        await processing_msg.delete()
        
        # Отправляем результат с Markdown форматированием
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            interpretation, 
            reply_markup=get_main_menu(subscription),
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при расчете даров: {e}")
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            "❌ Произошла ошибка при расчете. Попробуйте еще раз.",
            reply_markup=get_main_menu(subscription)
        )
        await state.clear()

@dp.message(Command("subscription"))
async def cmd_subscription(message: Message):
    """Информация о подписке"""
    user_id = message.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    if subscription['active']:
        text = f"""✅ *Ваша подписка активна*

Тип: *{subscription['type'].upper()}*
"""
        if subscription.get('end_date'):
            text += f"Действительна до: `{subscription['end_date'].strftime('%d.%m.%Y %H:%M')}`\n"
        
        text += "\n🎁 Вам доступны все функции бота!"
    else:
        text = f"""⚠️ *Подписка не активна*

Для продолжения работы с ботом необходимо оформить подписку.

💫 *Премиум подписка* - от {Config.PRO_MONTH_PRICE} звезд
• Безлимитные расчеты даров
• Полный анализ с помощью ИИ
• Доступ к гаданиям
• Расширенные трактовки
"""
    
    await message.answer(text, reply_markup=get_subscription_menu(), parse_mode="Markdown")

@dp.message(F.text == "🎁 Рассчитать дары")
async def button_calculate(message: Message, state: FSMContext):
    """Кнопка расчета даров"""
    await cmd_calculate(message, state)

@dp.message(F.text == "💎 Подписка")
async def button_subscription(message: Message):
    """Кнопка подписки"""
    await cmd_subscription(message)

@dp.message(F.text == "❓ Помощь")
async def button_help(message: Message):
    """Кнопка помощи"""
    await cmd_help(message)

@dp.message(F.text == "🎭 Полный профиль")
async def button_complete_profile(message: Message, state: FSMContext):
    """Кнопка комплексного расчета"""
    await cmd_complete_calculate(message, state)

# ============= ОБРАБОТЧИКИ КОМПЛЕКСНОГО РАСЧЕТА =============

@dp.message(UserStates.waiting_for_complete_birth_date)
async def process_complete_birth_date(message: Message, state: FSMContext):
    """Обработка даты рождения для комплексного расчета"""
    birth_date = message.text.strip()
    
    # Проверяем формат даты
    try:
        day, month, year = calculator.parse_date(birth_date)
        
        # Сохраняем дату в состояние
        await state.update_data(birth_date=birth_date)
        
        await message.answer(
            "⏰ Отлично! Теперь введите время вашего рождения в формате ЧЧ:ММ\n\nНапример: 14:30",
            parse_mode="Markdown"
        )
        await state.set_state(UserStates.waiting_for_birth_time)
        
    except ValueError as e:
        await message.answer(
            f"❌ {str(e)}\n\nПопробуйте еще раз в формате ДД.ММ.ГГГГ",
            parse_mode="Markdown"
        )

@dp.message(UserStates.waiting_for_birth_time)
async def process_birth_time(message: Message, state: FSMContext):
    """Обработка времени рождения"""
    birth_time = message.text.strip()
    
    # Проверяем формат времени
    try:
        hour, minute = calculator.parse_time(birth_time)
        
        # Сохраняем время в состояние
        await state.update_data(birth_time=birth_time)
        
        # Создаем клавиатуру с кнопкой для отправки геолокации
        from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
        
        location_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
                [KeyboardButton(text="❌ Отмена")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            "🌍 Отлично! Теперь отправьте вашу геолокацию места рождения.\n\n"
            "Нажмите кнопку *'📍 Отправить геолокацию'* ниже или просто отправьте координаты вручную в формате:\n"
            "`широта, долгота`\n\n"
            "Например: `49.9904, 36.2439`",
            reply_markup=location_keyboard,
            parse_mode="Markdown"
        )
        await state.set_state(UserStates.waiting_for_location)
        
    except ValueError as e:
        await message.answer(
            f"❌ {str(e)}\n\nПопробуйте еще раз в формате ЧЧ:ММ",
            parse_mode="Markdown"
        )

@dp.message(UserStates.waiting_for_location, F.location)
async def process_location_geo(message: Message, state: FSMContext):
    """Обработка геолокации"""
    latitude = message.location.latitude
    longitude = message.location.longitude
    
    # Сохраняем координаты в состояние
    await state.update_data(latitude=latitude, longitude=longitude)
    
    # Убираем клавиатуру с кнопками геолокации
    from aiogram.types import ReplyKeyboardRemove
    
    await message.answer(
        f"✅ Геолокация получена: `{latitude:.4f}, {longitude:.4f}`\n\n"
        "👤 Теперь введите ваше *имя*:",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    await state.set_state(UserStates.waiting_for_first_name)

@dp.message(UserStates.waiting_for_location, F.text)
async def process_location_text(message: Message, state: FSMContext):
    """Обработка координат в текстовом формате"""
    text = message.text.strip()
    
    # Проверяем на отмену
    if text == "❌ Отмена":
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            "❌ Комплексный расчет отменен.",
            reply_markup=get_main_menu(subscription)
        )
        await state.clear()
        return
    
    # Парсим координаты
    try:
        parts = text.replace(" ", "").split(",")
        if len(parts) != 2:
            raise ValueError("Неверный формат")
        
        latitude = float(parts[0])
        longitude = float(parts[1])
        
        # Проверяем диапазоны
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            raise ValueError("Координаты вне допустимого диапазона")
        
        # Сохраняем координаты в состояние
        await state.update_data(latitude=latitude, longitude=longitude)
        
        # Убираем клавиатуру с кнопками геолокации
        from aiogram.types import ReplyKeyboardRemove
        
        await message.answer(
            f"✅ Координаты получены: `{latitude:.4f}, {longitude:.4f}`\n\n"
            "👤 Теперь введите ваше *имя*:",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="Markdown"
        )
        await state.set_state(UserStates.waiting_for_first_name)
        
    except (ValueError, IndexError):
        await message.answer(
            "❌ Неверный формат координат.\n\n"
            "Введите координаты в формате: `широта, долгота`\n"
            "Например: `49.9904, 36.2439`\n\n"
            "Или нажмите кнопку '📍 Отправить геолокацию'",
            parse_mode="Markdown"
        )

@dp.message(UserStates.waiting_for_first_name)
async def process_first_name(message: Message, state: FSMContext):
    """Обработка имени"""
    first_name = message.text.strip()
    
    if not first_name:
        await message.answer("❌ Имя не может быть пустым. Попробуйте еще раз:")
        return
    
    # Сохраняем имя в состояние
    await state.update_data(first_name=first_name)
    
    await message.answer(
        f"✅ Имя: *{first_name}*\n\n"
        "👥 Теперь введите вашу *фамилию*:",
        parse_mode="Markdown"
    )
    await state.set_state(UserStates.waiting_for_last_name)

@dp.message(UserStates.waiting_for_last_name)
async def process_last_name(message: Message, state: FSMContext):
    """Обработка фамилии и выполнение комплексного расчета"""
    last_name = message.text.strip()
    
    if not last_name:
        await message.answer("❌ Фамилия не может быть пустой. Попробуйте еще раз:")
        return
    
    # Получаем все данные из состояния
    data = await state.get_data()
    birth_date = data.get('birth_date')
    birth_time = data.get('birth_time')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    first_name = data.get('first_name')
    
    user_id = message.from_user.id
    
    try:
        # Отправляем сообщение о начале расчета
        processing_msg = await message.answer(
            "🔮 Выполняю комплексный расчет всех даров...\n\n"
            "⏳ Это может занять несколько секунд...",
            parse_mode="Markdown"
        )
        
        # Выполняем комплексный расчет
        results = calculator.calculate_complete_profile(
            birth_date=birth_date,
            birth_time=birth_time,
            latitude=latitude,
            longitude=longitude,
            first_name=first_name,
            last_name=last_name
        )
        
        if results['status'] == 'error':
            await processing_msg.delete()
            user_id = message.from_user.id
            subscription = await check_subscription_with_admin(user_id)
            await message.answer(
                f"❌ Ошибка при расчете: {results['error']}",
                reply_markup=get_main_menu(subscription)
            )
            await state.clear()
            return
        
        # Сохраняем дату рождения пользователя
        await db.update_user_birth_date(user_id, birth_date)
        
        # Сохраняем результаты расчета
        await db.save_calculation(
            user_id, 
            'complete_profile',
            birth_date,
            json.dumps(results, ensure_ascii=False)
        )
        
        # Обновляем сообщение о процессе
        await processing_msg.edit_text(
            "🤖 Расчет завершен! Анализирую данные с помощью ИИ...\n\n"
            "⏳ Пожалуйста, подождите...\n"
            "⏱ Это может занять 10-30 секунд"
        )
        
        # Получаем трактовку от ИИ
        try:
            interpretation = await ai_handler.get_complete_profile_interpretation(results)
            
            # Проверяем, что получили реальный анализ, а не базовую трактовку
            if not interpretation or len(interpretation.strip()) < 100:
                logger.warning("Получен слишком короткий ответ от ИИ")
                raise ValueError("Ответ от ИИ слишком короткий")
            
            # Проверяем, что это не базовая трактовка
            if "━━━━━━━━━━━━━━━━━━" in interpretation and "Комплексный анализ даров" in interpretation:
                logger.warning("Получена базовая трактовка вместо ИИ анализа")
                raise ValueError("Получена базовая трактовка вместо ИИ анализа")
            
            # Удаляем сообщение о обработке
            await processing_msg.delete()
            
            # Отправляем результат
            # Разбиваем на части если текст слишком длинный (Telegram лимит 4096 символов)
            max_length = 4000
            if len(interpretation) > max_length:
                parts = [interpretation[i:i+max_length] for i in range(0, len(interpretation), max_length)]
                for i, part in enumerate(parts):
                    if i == 0:
                        await message.answer(part, parse_mode="Markdown")
                    else:
                        await message.answer(part, parse_mode="Markdown")
            else:
                user_id = message.from_user.id
                subscription = await check_subscription_with_admin(user_id)
                await message.answer(
                    interpretation,
                    reply_markup=get_main_menu(subscription),
                    parse_mode="Markdown"
                )
            
            await state.clear()
            
        except Exception as ai_error:
            logger.error(f"Ошибка при анализе ИИ: {ai_error}", exc_info=True)
            
            # Удаляем сообщение о процессе
            try:
                await processing_msg.delete()
            except:
                pass
            
            # Показываем базовую трактовку с предупреждением
            basic_interpretation = ai_handler._get_basic_complete_interpretation(results)
            
            error_notice = """⚠️ *Не удалось получить анализ от ИИ*

Возвращаю базовые данные из базы знаний.

*Причина ошибки:* {error}

Попробуйте позже или обратитесь к администратору.

━━━━━━━━━━━━━━━━━━

""".format(error=str(ai_error)[:200])
            
            user_id = message.from_user.id
            subscription = await check_subscription_with_admin(user_id)
            await message.answer(
                error_notice + basic_interpretation,
                reply_markup=get_main_menu(subscription),
                parse_mode="Markdown"
            )
            
            await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при комплексном расчете: {e}", exc_info=True)
        
        # Удаляем сообщение о процессе если есть
        try:
            if 'processing_msg' in locals():
                await processing_msg.delete()
        except:
            pass
        
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            f"❌ Произошла ошибка при расчете:\n\n`{str(e)[:300]}`\n\nПопробуйте еще раз позже.",
            reply_markup=get_main_menu(subscription),
            parse_mode="Markdown"
        )
        await state.clear()

# ============= ОБРАБОТЧИКИ CALLBACK'ОВ ДЛЯ ПОДПИСКИ =============

@dp.callback_query(F.data == "show_premium_options")
async def show_premium_options(callback: CallbackQuery):
    """Показ вариантов премиум подписки"""
    text = """⭐️ *Премиум подписка*

Выберите подходящий тариф:

🧪 *ТЕСТ (1 день)* - {test_price} ⭐️
• Для тестирования системы оплаты
• Доступ ко всем функциям на 1 день

📅 *Месяц* - {month_price} ⭐️
• Доступ ко всем функциям на 30 дней
• Безлимитные расчеты даров
• Полный анализ с ИИ

📆 *Год* - {year_price} ⭐️
• Доступ ко всем функциям на 365 дней
• Безлимитные расчеты даров
• Полный анализ с ИИ
• *Выгода ~17%* 🎉

💡 _После оплаты подписка активируется автоматически_
""".format(
        test_price=Config.PREMIUM_TEST_PRICE,
        month_price=Config.PRO_MONTH_PRICE,
        year_price=Config.PRO_YEAR_PRICE
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_premium_options_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_subscription")
async def back_to_subscription(callback: CallbackQuery):
    """Возврат к меню подписки"""
    user_id = callback.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    if subscription['active']:
        level = subscription.get('level', 'trial')
        level_name = {'trial': 'Trial', 'pro': 'PRO', 'orden': 'ORDEN'}.get(level, subscription['type'].upper())
        
        text = f"""✅ *Ваша подписка активна*

Тип: *{level_name}*
"""
        if subscription.get('end_date'):
            text += f"Действительна до: `{subscription['end_date'].strftime('%d.%m.%Y %H:%M')}`\n"
        
        if level == 'orden':
            text += "\n👑 Вам доступны ВСЕ функции бота, включая алхимию, сантры и анализ слов!"
        elif level == 'pro' or level == 'trial':
            # TRIAL имеет те же права что PRO
            level_text = 'PRO' if level == 'pro' else 'Trial'
            text += f"\n⭐ Вам доступны функции {level_text}. Для алхимии, сантр и анализа слов нужна подписка ORDEN."
        else:
            text += "\n🎁 Вам доступны базовые функции. Оформите подписку для расширенного доступа."
    else:
        text = f"""⚠️ *Подписка не активна*

Для продолжения работы с ботом необходимо оформить подписку.

💫 *Премиум подписка*
• Безлимитные расчеты даров
• Полный анализ с помощью ИИ
• Доступ к гаданиям (скоро)
• Расширенные трактовки
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=get_subscription_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "subscription_info")
async def subscription_info(callback: CallbackQuery):
    """Информация о подписках"""
    text = """📋 *Информация о подписках*

🎁 *Пробный период*
• Длительность: {trial_days} дней
• Предоставляется каждому новому пользователю
• Доступ к базовым функциям

⭐️ *PRO подписка*

*Что входит:*
• ✅ Безлимитные расчеты даров (Ода, Туна, Триа, Чиа)
• ✅ Полный анализ с помощью ИИ
• ✅ Подробные трактовки
• ✅ Предсказания
• ✅ Мантры
• ❌ Алхимия даров (только ORDEN)
• ❌ Сантры (только ORDEN)
• ❌ Анализ слов (только ORDEN)

*Тарифы PRO:*
📅 Месяц - {pro_month_price} ⭐️
📆 Год - {pro_year_price} ⭐️

👑 *ORDEN подписка*

*Что входит:*
• ✅ Всё из PRO
• ✅ ⚗️ Алхимия даров
• ✅ 📿 Сантры
• ✅ 🔮 Анализ слов через алфавит
• ✅ Полный доступ ко всем функциям

👑 *ORDEN подписка* (только через промокоды)

*Что входит:*
• ✅ Всё из PRO
• ✅ ⚗️ Алхимия даров
• ✅ 📿 Сантры
• ✅ 🔮 Анализ слов через алфавит
• ✅ Полный доступ ко всем функциям

💡 ORDEN подписка доступна только через промокоды от администраторов.

*Тестовая подписка:*
🧪 Тест - {test_price} ⭐️ (1 день для тестирования)

💡 _Оплата через Telegram Stars_
🔒 _Безопасно и моментально_
""".format(
        trial_days=Config.TRIAL_DURATION_DAYS,
        test_price=Config.PREMIUM_TEST_PRICE,
        pro_month_price=Config.PRO_MONTH_PRICE,
        pro_year_price=Config.PRO_YEAR_PRICE,
        orden_month_price=Config.ORDEN_MONTH_PRICE,
        orden_year_price=Config.ORDEN_YEAR_PRICE
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_subscription_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_premium_test")
async def buy_premium_test(callback: CallbackQuery, state: FSMContext):
    """Покупка тестовой подписки на 1 день"""
    data = await state.get_data()
    discount = data.get('active_discount', 0)
    promo_id = data.get('promo_id')
    
    await send_invoice(
        callback.message,
        callback.from_user.id,
        "test",
        Config.PREMIUM_TEST_PRICE,
        "Тестовая подписка на 1 день",
        discount=discount,
        promo_id=promo_id
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_premium_month")
async def buy_premium_month(callback: CallbackQuery, state: FSMContext):
    """Покупка подписки на месяц (старая версия - перенаправляем на PRO)"""
    data = await state.get_data()
    discount = data.get('active_discount', 0)
    promo_id = data.get('promo_id')
    
    await send_invoice(
        callback.message,
        callback.from_user.id,
        "pro_month",
        Config.PRO_MONTH_PRICE,
        "PRO подписка на 1 месяц",
        discount=discount,
        promo_id=promo_id
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_premium_year")
async def buy_premium_year(callback: CallbackQuery, state: FSMContext):
    """Покупка подписки на год (старая версия - оставляем для совместимости)"""
    # Перенаправляем на PRO год
    data = await state.get_data()
    discount = data.get('active_discount', 0)
    promo_id = data.get('promo_id')
    
    await send_invoice(
        callback.message,
        callback.from_user.id,
        "pro_year",
        Config.PRO_YEAR_PRICE,
        "PRO подписка на 1 год",
        discount=discount,
        promo_id=promo_id
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_pro_month")
async def buy_pro_month(callback: CallbackQuery, state: FSMContext):
    """Покупка PRO подписки на месяц"""
    data = await state.get_data()
    discount = data.get('active_discount', 0)
    promo_id = data.get('promo_id')
    
    await send_invoice(
        callback.message,
        callback.from_user.id,
        "pro_month",
        Config.PRO_MONTH_PRICE,
        "PRO подписка на 1 месяц",
        discount=discount,
        promo_id=promo_id
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_pro_year")
async def buy_pro_year(callback: CallbackQuery, state: FSMContext):
    """Покупка PRO подписки на год"""
    data = await state.get_data()
    discount = data.get('active_discount', 0)
    promo_id = data.get('promo_id')
    
    await send_invoice(
        callback.message,
        callback.from_user.id,
        "pro_year",
        Config.PRO_YEAR_PRICE,
        "PRO подписка на 1 год",
        discount=discount,
        promo_id=promo_id
    )
    await callback.answer()


async def send_invoice(message: Message, user_id: int, subscription_type: str, 
                      price: int, description: str, discount: int = 0, promo_id: int = None):
    """Отправка инвойса для оплаты"""
    
    # Формируем описание
    if subscription_type == "test":
        title = "🧪 ТЕСТ - 1 день"
        desc = "Тестовая подписка на 1 день для проверки системы оплаты"
    elif subscription_type == "pro_month":
        title = "⭐ PRO - 1 месяц"
        desc = "PRO подписка: базовые расчеты, предсказания, мантры. Без алхимии, сантр и анализа слов."
    elif subscription_type == "pro_year":
        title = "⭐ PRO - 1 год"
        desc = "PRO подписка: базовые расчеты, предсказания, мантры. Без алхимии, сантр и анализа слов."
    elif subscription_type == "orden_month":
        title = "👑 ORDEN - 1 месяц"
        desc = "ORDEN подписка: полный доступ ко всем функциям включая алхимию, сантры и анализ слов."
    elif subscription_type == "orden_year":
        title = "👑 ORDEN - 1 год"
        desc = "ORDEN подписка: полный доступ ко всем функциям включая алхимию, сантры и анализ слов."
    elif subscription_type == "month":
        # Старая версия - перенаправляем на PRO
        title = "⭐ PRO - 1 месяц"
        desc = "PRO подписка: базовые расчеты, предсказания, мантры. Без алхимии, сантр и анализа слов."
    else:  # year - старая версия
        title = "⭐ PRO - 1 год"
        desc = "PRO подписка: базовые расчеты, предсказания, мантры. Без алхимии, сантр и анализа слов."
    
    # Применяем скидку если есть
    final_price = price
    if discount > 0:
        final_price = int(price * (100 - discount) / 100)
        desc += f"\n💰 Скидка {discount}% применена!"
        title += f" (скидка {discount}%)"
    
    # Создаем инвойс
    prices = [LabeledPrice(label=title, amount=final_price)]
    
    # Сохраняем promo_id в payload если есть
    payload = f"premium_{subscription_type}_{user_id}"
    if promo_id:
        payload += f"_promo{promo_id}"
    
    await bot.send_invoice(
        chat_id=user_id,
        title=title,
        description=desc,
        payload=payload,
        currency="XTR",  # Telegram Stars
        prices=prices
    )

@dp.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    """Обработка pre-checkout запроса"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message, state: FSMContext):
    """Обработка успешной оплаты"""
    payment = message.successful_payment
    user_id = message.from_user.id
    
    # Парсим payload для определения типа подписки и промокода
    payload_parts = payment.invoice_payload.split('_')
    subscription_type = payload_parts[1]  # test, pro_month, pro_year, orden_month, orden_year, month, year
    
    # Проверяем, был ли использован промокод со скидкой
    promo_id = None
    if len(payload_parts) > 3 and payload_parts[3].startswith('promo'):
        promo_id = int(payload_parts[3].replace('promo', ''))
    
    # Определяем длительность подписки
    if subscription_type == "test":
        days = Config.PREMIUM_TEST_DAYS
        type_name = "premium_test"
        period_text = "1 день (ТЕСТ)"
    elif subscription_type == "pro_month":
        days = Config.PRO_MONTH_DAYS
        type_name = "pro_month"
        period_text = "месяц (PRO)"
    elif subscription_type == "pro_year":
        days = Config.PRO_YEAR_DAYS
        type_name = "pro_year"
        period_text = "год (PRO)"
    elif subscription_type == "orden_month":
        days = Config.ORDEN_MONTH_DAYS
        type_name = "orden_month"
        period_text = "месяц (ORDEN)"
    elif subscription_type == "orden_year":
        days = Config.ORDEN_YEAR_DAYS
        type_name = "orden_year"
        period_text = "год (ORDEN)"
    elif subscription_type == "month":
        # Старая версия - перенаправляем на PRO
        days = Config.PRO_MONTH_DAYS
        type_name = "pro_month"
        period_text = "месяц (PRO)"
    else:  # year - старая версия
        days = Config.PRO_YEAR_DAYS
        type_name = "pro_year"
        period_text = "год (PRO)"
    
    # Обновляем подписку
    end_date = await db.update_subscription(user_id, type_name, days)
    
    # Сохраняем информацию о платеже
    await db.add_payment(
        user_id=user_id,
        amount=payment.total_amount,
        currency=payment.currency,
        subscription_type=type_name,
        status='completed'
    )
    
    # Если был использован промокод со скидкой, регистрируем использование
    if promo_id:
        await db.use_promocode(user_id, promo_id)
        # Очищаем скидку из состояния
        await state.update_data(active_discount=None, promo_id=None)
    
    # Определяем уровень подписки для сообщения
    level = Config.SUBSCRIPTION_LEVELS.get(type_name, 'trial')
    level_name = {'trial': 'Trial', 'pro': 'PRO', 'orden': 'ORDEN'}.get(level, 'Premium')
    
    # Отправляем подтверждение
    text = f"""✅ *Оплата успешно выполнена!*

🎉 Ваша подписка *{level_name}* активирована!

📅 Тариф: *{period_text}*
💫 Действительна до: `{end_date.strftime('%d.%m.%Y %H:%M')}`
💰 Оплачено: *{payment.total_amount} ⭐️*

"""
    
    if level == 'orden':
        text += """👑 Теперь вам доступны ВСЕ функции бота:
• Безлимитные расчеты даров
• Полный анализ с ИИ
• ⚗️ Алхимия даров
• 📿 Сантры
• 🔮 Анализ слов
• Предсказания и рекомендации"""
    elif level == 'pro' or level == 'trial':
        # TRIAL имеет те же права что PRO
        level_text = 'PRO' if level == 'pro' else 'Trial'
        text += f"""⭐ Теперь вам доступны функции {level_text}:
• Безлимитные расчеты даров
• Полный анализ с ИИ
• Предсказания и рекомендации
• Мантры

💡 Для доступа к алхимии, сантрам и анализу слов оформите подписку ORDEN"""
    else:
        text += """🎁 Теперь вам доступны базовые функции:
• Безлимитные расчеты даров
• Полный анализ с ИИ
• Персональные рекомендации"""
    
    text += "\n\nСпасибо за поддержку! 🙏"
    
    user_id = message.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_menu(subscription))

# ============= ОБРАБОТЧИКИ САНТР =============

@dp.message(F.text == "📿 Сантры")
async def button_mantras(message: Message):
    """Кнопка работы с сантрами"""
    user_id = message.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    # Проверка доступа - требуется уровень ORDEN
    if not check_feature_access(subscription, 'orden'):
        text = """📿 *Работа с сантрами*

❌ *Доступ ограничен*

Сантры доступны только для подписки *ORDEN*.

*ORDEN* включает:
• ⚗️ Алхимия даров
• 📿 Сантры
• 🔮 Анализ слов
• ✨ Все остальные функции

Оформите подписку ORDEN для доступа к этой функции."""
        await message.answer(text, reply_markup=get_subscription_menu(), parse_mode="Markdown")
        return
    
    text = """📿 *Работа с сантрами*

Сантра - это комбинация команд и даров, созданная для достижения определенных целей.

*Примеры:*
• `Ши Ду Ма-На` - сантра с 1 даром
• `Ши Ду Ма-На Ду Ра-Ма` - сантра с 2 дарами

*Доступные функции:*
✨ Создать случайную сантру
📝 Создать сантру по вашему запросу
🔍 Проанализировать существующую сантру"""
    
    await message.answer(text, reply_markup=get_mantras_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "back_to_mantras")
async def back_to_mantras(callback: CallbackQuery):
    """Возврат к меню сантр"""
    text = """📿 *Работа с сантрами*

Сантра - это комбинация команд и даров, созданная для достижения определенных целей.

*Примеры:*
• `Ши Ду Ма-На` - сантра с 1 даром
• `Ши Ду Ма-На Ду Ра-Ма` - сантра с 2 дарами

*Доступные функции:*
✨ Создать случайную сантру
📝 Создать сантру по вашему запросу
🔍 Проанализировать существующую сантру"""
    
    await callback.message.edit_text(text, reply_markup=get_mantras_menu(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    await callback.message.delete()
    await callback.answer()

@dp.callback_query(F.data == "back_to_main_alchemy")
async def back_to_main_alchemy(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню из алхимии"""
    await state.clear()
    await callback.message.delete()
    welcome_text = """👋 *Добро пожаловать!*

🎁 Я помогу вам раскрыть ваши дары, заложенные при рождении по древнеславянской системе *Ма-Жи-Кун*.

📝 Используйте меню ниже для начала работы:"""
    user_id = callback.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    await callback.message.answer(welcome_text, reply_markup=get_main_menu(subscription), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data.startswith("mantra_create_"))
async def handle_mantra_create(callback: CallbackQuery, state: FSMContext):
    """Обработка создания сантры"""
    user_id = callback.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    # Проверка доступа - требуется уровень ORDEN
    if not check_feature_access(subscription, 'orden'):
        await callback.answer("❌ Сантры доступны только для подписки ORDEN", show_alert=True)
        await callback.message.edit_text(
            "❌ *Доступ ограничен*\n\nСантры доступны только для подписки *ORDEN*.\n\nОформите подписку ORDEN для доступа к этой функции.",
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        return
    
    num_gifts = int(callback.data.split("_")[-1])  # 1 или 2
    
    # Создаем сантру сразу (без самовоспроизведения)
    mantra_data = create_mantra_random(num_gifts, include_end=False)
    
    if "error" in mantra_data:
        await callback.message.edit_text(
            f"❌ Ошибка: {mantra_data['error']}",
            reply_markup=get_mantras_menu()
        )
        await callback.answer()
        return
    
    mantra_text = mantra_data.get("mantra", "")
    
    # Формируем ответ без списка элементов
    result = f"""✨ *Сантра создана!*

📿 *Сантра:* `{mantra_text}`

💡 Хотите проанализировать эту сантру через ИИ?"""
    
    # Отправляем текст сантры
    await callback.message.edit_text(result, parse_mode="Markdown")
    
    # Сохраняем текст сантры в state для анализа
    await state.update_data(created_mantra=mantra_text)
    
    # Отправляем кнопки отдельным сообщением
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Анализировать с ИИ", callback_data="mantra_analyze_created")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_mantras")]
    ])
    
    await callback.message.answer("Выберите действие:", reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "mantra_create_request")
async def handle_mantra_create_request(callback: CallbackQuery, state: FSMContext):
    """Создание сантры по запросу пользователя"""
    user_id = callback.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    # Проверка доступа - требуется уровень ORDEN
    if not check_feature_access(subscription, 'orden'):
        await callback.answer("❌ Сантры доступны только для подписки ORDEN", show_alert=True)
        await callback.message.edit_text(
            "❌ *Доступ ограничен*\n\nСантры доступны только для подписки *ORDEN*.\n\nОформите подписку ORDEN для доступа к этой функции.",
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        return
    
    text = """📝 *Создание сантры по запросу*

Опишите, для чего вам нужна сантра или задайте вопрос.

*Примеры запросов:*
• "Нужна сантра для привлечения денег"
• "Создай сантру для защиты"
• "Хочу сантру для улучшения здоровья"

Введите ваш запрос:"""
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(UserStates.waiting_for_mantra_request)
    await callback.answer()

@dp.message(UserStates.waiting_for_mantra_request)
async def process_mantra_request(message: Message, state: FSMContext):
    """Обработка запроса пользователя для создания сантры"""
    user_question = message.text.strip()
    
    if not user_question:
        await message.answer("❌ Запрос не может быть пустым. Попробуйте еще раз:")
        return
    
    # Сохраняем вопрос в состоянии
    await state.update_data(user_question=user_question)
    
    # Спрашиваем количество даров
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 дар", callback_data="mantra_request_1")],
        [InlineKeyboardButton(text="2 дара", callback_data="mantra_request_2")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_mantras")]
    ])
    
    await message.answer(
        "📿 Выберите количество даров в сантре:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("mantra_request_"))
async def handle_mantra_request_create(callback: CallbackQuery, state: FSMContext):
    """Создание сантры по запросу"""
    num_gifts = int(callback.data.split("_")[-1])  # 1 или 2
    
    # Получаем вопрос из состояния
    data = await state.get_data()
    user_question = data.get("user_question", "")
    
    # Создаем сантру
    mantra_data = create_mantra_by_request(user_question, num_gifts, include_end=False)
    
    if "error" in mantra_data:
        await callback.message.edit_text(
            f"❌ Ошибка: {mantra_data['error']}",
            reply_markup=get_mantras_menu()
        )
        await callback.answer()
        return
    
    mantra_text = mantra_data.get("mantra", "")
    
    # Формируем ответ без списка элементов
    result = f"""✨ *Сантра создана!*

📿 *Сантра:* `{mantra_text}`

*Запрос:* {user_question}

💡 Хотите проанализировать эту сантру через ИИ?"""
    
    # Сохраняем текст сантры в state для анализа
    await state.update_data(created_mantra=mantra_text)
    
    # Отправляем текст сантры
    await callback.message.edit_text(result, parse_mode="Markdown")
    
    # Отправляем кнопки отдельным сообщением
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Анализировать с ИИ", callback_data="mantra_analyze_created")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_mantras")]
    ])
    
    await callback.message.answer("Выберите действие:", reply_markup=keyboard)
    await callback.answer()

# ============= СОЗДАНИЕ САНТРЫ ПО ЗАПРОСУ С ВЫБОРОМ ТЕМЫ =============

@dp.callback_query(F.data == "mantra_create_by_theme")
async def handle_create_mantra_by_theme(callback: CallbackQuery, state: FSMContext):
    """Начало создания сантры по запросу - показ тем"""
    user_id = callback.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    # Проверка доступа - требуется уровень ORDEN
    if not check_feature_access(subscription, 'orden'):
        await callback.answer("❌ Создание сантр по запросу доступно только для подписки ORDEN", show_alert=True)
        await callback.message.edit_text(
            "❌ *Доступ ограничен*\n\nСоздание сантр по запросу доступно только для подписки *ORDEN*.\n\nОформите подписку ORDEN для доступа к этой функции.",
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        return
    # Все доступные темы
    all_themes = [
        "здоровье", "семья", "деньги", "бизнес", "отношения",
        "решение события", "ясность", "позиция здесь и сейчас",
        "актуальная практика для меня"
    ]
    
    # Выбираем случайно 3-4 темы
    num_themes = random.randint(3, 4)
    selected_themes = random.sample(all_themes, num_themes)
    
    # Создаем кнопки с темами
    keyboard_buttons = []
    for theme in selected_themes:
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"💫 {theme.capitalize()}",
            callback_data=f"theme_select_{theme}"
        )])
    
    keyboard_buttons.append([InlineKeyboardButton(text="« Назад", callback_data="back_to_mantras")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    text = """📝 *Создание сантры по запросу*

Выберите тему из предложенных ниже или напишите свой запрос:

*Примеры своего запроса:*
• "Нужна сантра для привлечения денег"
• "Помоги с защитой"
• "Хочу улучшить здоровье"

Вы можете нажать на кнопку или написать свой запрос:"""
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="Markdown")
    await state.set_state(UserStates.waiting_for_mantra_by_theme)
    await callback.answer()

@dp.callback_query(F.data.startswith("theme_select_"))
async def handle_theme_selected(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора темы кнопкой"""
    theme = callback.data.replace("theme_select_", "")
    
    # Сохраняем тему и создаем сантру
    await create_and_analyze_mantra_by_theme(callback.message, state, theme, callback)

@dp.message(UserStates.waiting_for_mantra_by_theme)
async def handle_theme_text_input(message: Message, state: FSMContext):
    """Обработка текстового ввода запроса"""
    user_request = message.text.strip()
    
    if not user_request:
        await message.answer("❌ Запрос не может быть пустым. Попробуйте еще раз:")
        return
    
    # Создаем сантру по текстовому запросу
    await create_and_analyze_mantra_by_theme(message, state, user_request, None)

async def create_and_analyze_mantra_by_theme(message: Message, state: FSMContext, user_request: str, callback: CallbackQuery = None):
    """Создание сантры по запросу и её анализ"""
    user_id = message.from_user.id if callback is None else callback.from_user.id
    
    # Проверяем подписку и уровень доступа
    subscription = await check_subscription_with_admin(user_id)
    if not check_feature_access(subscription, 'orden'):
        text = """❌ *Доступ ограничен*

Создание сантр по запросу доступно только для подписки *ORDEN*.

👑 *ORDEN подписка включает:*
• ⚗️ Алхимия даров
• 📿 Сантры (включая создание по запросу)
• 🔮 Анализ слов
• ✨ Все остальные функции

*Тарифы ORDEN:*
📅 Месяц - {orden_month_price} ⭐️
📆 Год - {orden_year_price} ⭐️

_Нажмите кнопку ниже для оформления подписки_""".format(
            orden_month_price=Config.ORDEN_MONTH_PRICE,
            orden_year_price=Config.ORDEN_YEAR_PRICE
        )
        
        if callback:
            await callback.message.edit_text(text, reply_markup=get_subscription_menu(), parse_mode="Markdown")
        else:
            await message.answer(text, reply_markup=get_subscription_menu(), parse_mode="Markdown")
        
        await state.clear()
        return
    
    # Создаем сантру (начало + между + дар + между + дар)
    mantra_data = create_mantra_random(num_gifts=2, include_end=False)
    
    if "error" in mantra_data:
        error_text = f"❌ Ошибка при создании сантры: {mantra_data['error']}"
        if callback:
            await callback.message.edit_text(error_text, reply_markup=get_mantras_menu())
        else:
            await message.answer(error_text, reply_markup=get_mantras_menu())
        await state.clear()
        return
    
    mantra_text = mantra_data.get("mantra", "")
    
    # Сохраняем в состояние для анализа
    await state.update_data(
        created_mantra=mantra_text,
        user_request=user_request,
        mantra_data=mantra_data
    )
    
    # Формируем ответ с сантрой и запросом
    result = f"""✨ *Сантра создана!*

📝 *Ваш запрос:* _{user_request}_

📿 *Сантра:* `{mantra_text}`

💡 Нажмите кнопку ниже для анализа сантры с помощью ИИ в контексте вашего запроса."""
    
    # Кнопка для анализа
    analyze_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤖 Анализировать с ИИ", callback_data="analyze_mantra_by_theme")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_mantras")]
    ])
    
    # Отправляем результат
    if callback:
        await callback.message.edit_text(result, parse_mode="Markdown")
        await callback.message.answer("Выберите действие:", reply_markup=analyze_keyboard)
    else:
        await message.answer(result, parse_mode="Markdown")
        await message.answer("Выберите действие:", reply_markup=analyze_keyboard)
    
    await state.clear()
    if callback:
        await callback.answer()

@dp.callback_query(F.data == "analyze_mantra_by_theme")
async def handle_analyze_mantra_by_theme(callback: CallbackQuery, state: FSMContext):
    """Анализ созданной сантры с учетом запроса пользователя"""
    # Получаем данные из состояния
    data = await state.get_data()
    mantra_text = data.get("created_mantra", "")
    user_request = data.get("user_request", "")
    mantra_data = data.get("mantra_data", {})
    
    if not mantra_text or not mantra_data:
        await callback.answer("❌ Данные сантры не найдены. Создайте новую сантру.", show_alert=True)
        return
    
    # Отправляем сообщение о начале анализа
    processing_msg = await callback.message.edit_text(
        "🔮 Анализирую сантру с помощью ИИ в контексте вашего запроса...\n⏳ Пожалуйста, подождите..."
    )
    
    try:
        # Получаем анализ от ИИ с учетом запроса
        interpretation = await ai_handler.analyze_mantra_with_request(mantra_data, user_request)
        
        # Удаляем сообщение о процессе
        await processing_msg.delete()
        
        # Формируем полный ответ
        full_result = f"""✨ *Анализ сантры по вашему запросу*

📝 *Запрос:* _{user_request}_

📿 *Сантра:* `{mantra_text}`

━━━━━━━━━━━━━━━━━━

{interpretation}"""
        
        # Отправляем результат
        await callback.message.answer(full_result, parse_mode="Markdown")
        
        # Кнопки для дальнейших действий
        next_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Создать еще", callback_data="mantra_create_by_theme")],
            [InlineKeyboardButton(text="« Назад в меню", callback_data="back_to_mantras")]
        ])
        
        await callback.message.answer("Выберите действие:", reply_markup=next_keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при анализе сантры: {e}")
        await processing_msg.edit_text(
            f"❌ Произошла ошибка при анализе: {str(e)}",
            reply_markup=get_mantras_menu()
        )
    
    await callback.answer()

@dp.callback_query(F.data == "mantra_analyze")
async def handle_mantra_analyze(callback: CallbackQuery, state: FSMContext):
    """Начало анализа сантры"""
    user_id = callback.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    # Проверка доступа - требуется уровень ORDEN
    if not check_feature_access(subscription, 'orden'):
        await callback.answer("❌ Анализ сантр доступен только для подписки ORDEN", show_alert=True)
        await callback.message.edit_text(
            "❌ *Доступ ограничен*\n\nАнализ сантр доступен только для подписки *ORDEN*.\n\nОформите подписку ORDEN для доступа к этой функции.",
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        return
    
    text = """🔍 *Анализ сантры*

Отправьте сантру для анализа.

*Формат:* просто перечислите элементы через пробел
*Пример:* `Ши ду мана`

*Примечание:* 
• Регистр не важен
• Для даров можно указывать упрощенное имя (например, "мана" вместо "дар Ма-На")"""
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(UserStates.waiting_for_mantra_to_analyze)
    await callback.answer()

@dp.callback_query(F.data == "mantra_analyze_created")
async def handle_mantra_analyze_created(callback: CallbackQuery, state: FSMContext):
    """Анализ созданной сантры через ИИ"""
    user_id = callback.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    # Проверка доступа - требуется уровень ORDEN
    if not check_feature_access(subscription, 'orden'):
        await callback.answer("❌ Анализ сантр доступен только для подписки ORDEN", show_alert=True)
        return
    data = await state.get_data()
    mantra_text = data.get("created_mantra", "")
    
    if not mantra_text:
        await callback.answer("❌ Сантра не найдена", show_alert=True)
        return
    
    # Парсим сантру
    mantra_data = parse_mantra(mantra_text)
    
    # Отправляем сообщение о начале анализа
    processing_msg = await callback.message.answer("🔮 Анализирую сантру с помощью ИИ...")
    
    # Получаем анализ от ИИ
    interpretation = await ai_handler.analyze_mantra(mantra_data)
    
    # Удаляем сообщение о обработке
    await processing_msg.delete()
    
    # Отправляем результат
    await callback.message.answer(interpretation, parse_mode="Markdown")
    
    # Отправляем кнопки отдельным сообщением
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_mantras")]
    ])
    
    await callback.message.answer("Выберите действие:", reply_markup=keyboard)
    await callback.answer()

@dp.message(UserStates.waiting_for_mantra_to_analyze)
async def process_mantra_to_analyze(message: Message, state: FSMContext):
    """Обработка сантры для анализа"""
    user_id = message.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    # Проверка доступа - требуется уровень ORDEN
    if not check_feature_access(subscription, 'orden'):
        await message.answer(
            "❌ *Доступ ограничен*\n\nАнализ сантр доступен только для подписки *ORDEN*.\n\nОформите подписку ORDEN для доступа к этой функции.",
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        await state.clear()
        return
    mantra_text = message.text.strip()
    
    if not mantra_text:
        await message.answer("❌ Сантра не может быть пустой. Попробуйте еще раз:")
        return
    
    # Парсим сантру
    mantra_data = parse_mantra(mantra_text)
    
    # Отправляем сообщение о начале анализа
    processing_msg = await message.answer("🔮 Анализирую сантру с помощью ИИ...")
    
    # Получаем анализ от ИИ
    interpretation = await ai_handler.analyze_mantra(mantra_data)
    
    # Удаляем сообщение о обработке
    await processing_msg.delete()
    
    # Отправляем результат без кнопок
    await message.answer(interpretation, parse_mode="Markdown")
    
    # Отправляем кнопки отдельным сообщением
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_mantras")]
    ])
    
    await message.answer("Выберите действие:", reply_markup=keyboard)
    await state.clear()

# =============================================================================
# ОБРАБОТЧИКИ ДЛЯ АНАЛИЗА СЛОВ ЧЕРЕЗ АЛФАВИТ
# =============================================================================

@dp.message(F.text == "🔮 Анализ слов")
async def button_alphabet(message: Message):
    """Кнопка анализа слов через алфавит"""
    user_id = message.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    # Проверка доступа - требуется уровень ORDEN
    if not check_feature_access(subscription, 'orden'):
        text = """🔮 *Анализ слов через алфавит*

❌ *Доступ ограничен*

Анализ слов доступен только для подписки *ORDEN*.

*ORDEN* включает:
• ⚗️ Алхимия даров
• 📿 Сантры
• 🔮 Анализ слов
• ✨ Все остальные функции

Оформите подписку ORDEN для доступа к этой функции."""
        await message.answer(text, reply_markup=get_subscription_menu(), parse_mode="Markdown")
        return
    
    text = """🔮 *Анализ слов через алфавит*

Каждая буква несет в себе особую энергию и значение. Я могу проанализировать любое слово, имя или фразу, раскрыв их глубинный смысл.

*Что можно анализировать:*
• 📝 Имена и фамилии
• 🎁 Названия даров (например "Мана")
• 📿 Сантры и мантры
• 💬 Любые слова и фразы

*⚠️ ВАЖНО:* Анализ производится только для одного слова за раз! Если задать больше слов, их значение может исказиться.

*Как это работает:*
1. Каждая буква переводится в её значение
2. ИИ синтезирует общий смысл
3. Вы получаете глубинное толкование

Выберите действие ниже:"""
    
    await message.answer(text, reply_markup=get_alphabet_menu(), parse_mode="Markdown")

@dp.message(F.text == "🌟 Дар дня")
async def button_day_gift(message: Message):
    """Кнопка дара дня"""
    user_id = message.from_user.id
    
    # Проверяем подписку
    subscription = await check_subscription_with_admin(user_id)
    if not subscription['active']:
        text = """⚠️ *Подписка не активна*

Для получения дара дня необходима активная подписка.

⭐️ *Премиум подписка:*
📅 Месяц - {month_price} ⭐️
📆 Год - {year_price} ⭐️

🎁 Что вы получите:
• Безлимитные расчеты даров
• Дар дня с ИИ анализом
• Полный анализ
• Персональные рекомендации

_Нажмите кнопку ниже для оформления подписки_""".format(
            month_price=Config.PRO_MONTH_PRICE,
            year_price=Config.PRO_YEAR_PRICE
        )
        await message.answer(text, reply_markup=get_subscription_menu(), parse_mode="Markdown")
        return
    
    try:
        # Отправляем сообщение о начале обработки
        processing_msg = await message.answer(
            "🔮 ИИ обрабатывает запрос...\n⏳ Пожалуйста, подождите...",
            parse_mode="Markdown"
        )
        
        # Рассчитываем дар дня (используется текущая дата)
        day_gift_data = calculator.calculate_day_gift()
        
        if day_gift_data['status'] == 'error':
            await processing_msg.delete()
            user_id = message.from_user.id
            subscription = await check_subscription_with_admin(user_id)
            await message.answer(
                f"❌ Ошибка при расчете: {day_gift_data['error']}",
                reply_markup=get_main_menu(subscription)
            )
            return
        
        # Получаем трактовку от ИИ
        interpretation = await ai_handler.get_day_gift_interpretation(day_gift_data)
        
        # Удаляем сообщение о обработке
        await processing_msg.delete()
        
        # Отправляем результат
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            interpretation,
            reply_markup=get_main_menu(subscription),
            parse_mode="Markdown"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при расчете дара дня: {e}", exc_info=True)
        try:
            if 'processing_msg' in locals():
                await processing_msg.delete()
        except:
            pass
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            f"❌ Произошла ошибка при расчете:\n\n`{str(e)[:300]}`\n\nПопробуйте еще раз позже.",
            reply_markup=get_main_menu(subscription),
            parse_mode="Markdown"
        )

@dp.message(F.text == "🔮 Предсказания")
async def button_predictions(message: Message):
    """Кнопка предсказаний"""
    user_id = message.from_user.id
    
    # Проверяем подписку
    subscription = await check_subscription_with_admin(user_id)
    if not subscription['active']:
        text = """⚠️ *Подписка не активна*

Для предсказаний необходима активная подписка.

⭐️ *Премиум подписка:*
📅 Месяц - {month_price} ⭐️
📆 Год - {year_price} ⭐️

🎁 Что вы получите:
• Безлимитные расчеты даров
• Предсказания на день, событие и совместимость
• Полный анализ с ИИ
• Персональные рекомендации

_Нажмите кнопку ниже для оформления подписки_""".format(
            month_price=Config.PRO_MONTH_PRICE,
            year_price=Config.PRO_YEAR_PRICE
        )
        await message.answer(text, reply_markup=get_subscription_menu(), parse_mode="Markdown")
        return
    
    text = """🔮 *Предсказания*

Выберите тип предсказания:

*📅 На день* - предсказание на сегодня
Расчет по текущей дате и вашей дате рождения

*🎯 На событие* - предсказание на конкретное событие
Случайные энергии для анализа события

*💑 Совместимость пары* - анализ совместимости двух людей
Сравнение даров для понимания взаимодействия

Выберите тип:"""
    
    await message.answer(text, reply_markup=get_predictions_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "prediction_day")
async def handle_prediction_day(callback: CallbackQuery, state: FSMContext):
    """Обработка предсказания на день"""
    user_id = callback.from_user.id
    
    # Проверяем подписку
    subscription = await check_subscription_with_admin(user_id)
    if not subscription['active']:
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📅 *Предсказание на день*\n\n"
        "Введите вашу дату рождения в формате ДД.ММ.ГГГГ\n\n"
        "Например: 15.05.1990",
        parse_mode="Markdown"
    )
    await state.update_data(prediction_type="day")
    await state.set_state(UserStates.waiting_for_prediction_birth_date)
    await callback.answer()

@dp.callback_query(F.data == "prediction_event")
async def handle_prediction_event(callback: CallbackQuery, state: FSMContext):
    """Обработка предсказания на событие"""
    user_id = callback.from_user.id
    
    # Проверяем подписку
    subscription = await check_subscription_with_admin(user_id)
    if not subscription['active']:
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🎯 *Предсказание на событие*\n\n"
        "Введите вашу дату рождения в формате ДД.ММ.ГГГГ\n\n"
        "Например: 15.05.1990",
        parse_mode="Markdown"
    )
    await state.update_data(prediction_type="event")
    await state.set_state(UserStates.waiting_for_prediction_birth_date)
    await callback.answer()

@dp.callback_query(F.data == "prediction_compatibility")
async def handle_prediction_compatibility(callback: CallbackQuery, state: FSMContext):
    """Обработка совместимости пары"""
    user_id = callback.from_user.id
    
    # Проверяем подписку
    subscription = await check_subscription_with_admin(user_id)
    if not subscription['active']:
        await callback.answer("⚠️ Необходима активная подписка", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💑 *Совместимость пары*\n\n"
        "Введите вашу дату рождения в формате ДД.ММ.ГГГГ\n\n"
        "Например: 15.05.1990",
        parse_mode="Markdown"
    )
    await state.update_data(prediction_type="compatibility")
    await state.set_state(UserStates.waiting_for_prediction_birth_date)
    await callback.answer()

@dp.message(UserStates.waiting_for_prediction_birth_date)
async def process_prediction_birth_date(message: Message, state: FSMContext):
    """Обработка даты рождения для предсказания"""
    birth_date = message.text.strip()
    user_id = message.from_user.id
    data = await state.get_data()
    prediction_type = data.get('prediction_type')
    
    # Проверяем формат даты
    try:
        day, month, year = calculator.parse_date(birth_date)
        await state.update_data(user_birth_date=birth_date)
        
        if prediction_type == "compatibility":
            # Для совместимости запрашиваем дату партнера
            await message.answer(
                "👤 Теперь введите дату рождения партнера в формате ДД.ММ.ГГГГ\n\n"
                "Например: 20.08.1992",
                parse_mode="Markdown"
            )
            await state.set_state(UserStates.waiting_for_prediction_partner_birth_date)
        elif prediction_type == "event":
            # Для события запрашиваем описание события
            await message.answer(
                "🎯 На какое событие вы хотите получить предсказание?\n\n"
                "Например: свадьба, переезд, новая работа, экзамен",
                parse_mode="Markdown"
            )
            await state.set_state(UserStates.waiting_for_prediction_event)
        else:
            # Для дня - сразу обрабатываем
            await process_prediction_day_calculation(message, state, birth_date)
            
    except ValueError as e:
        await message.answer(
            f"❌ {str(e)}\n\nПопробуйте еще раз в формате ДД.ММ.ГГГГ",
            parse_mode="Markdown"
        )

@dp.message(UserStates.waiting_for_prediction_event)
async def process_prediction_event_text(message: Message, state: FSMContext):
    """Обработка описания события"""
    event_text = message.text.strip()
    data = await state.get_data()
    user_birth_date = data.get('user_birth_date')
    
    if not event_text:
        await message.answer("❌ Описание события не может быть пустым. Попробуйте еще раз:")
        return
    
    await state.update_data(event_text=event_text)
    
    # Обрабатываем предсказание на событие
    processing_msg = await message.answer(
        "🔮 Генерирую предсказание на событие...\n⏳ Пожалуйста, подождите...",
        parse_mode="Markdown"
    )
    
    try:
        # Генерируем случайные ма и жи (от 1 до 8)
        ma_random = random.randint(1, 8)
        ji_random = random.randint(1, 8)
        kun_random = calculator.calculate_kun(ma_random, ji_random)
        
        # Рассчитываем Ода для пользователя
        user_oda = calculator.calculate_oda(user_birth_date)
        
        # Получаем информацию о дарах из базы
        from src.gifts_knowledge import get_gift_info
        random_gift_code = f"{ma_random}-{ji_random}-{kun_random}"
        random_gift_info = get_gift_info(random_gift_code)
        user_gift_info = get_gift_info(user_oda['gift_code'])
        
        # Формируем данные для ИИ
        prediction_data = {
            'prediction_type': 'event',
            'event': event_text,
            'user_birth_date': user_birth_date,
            'user_oda': user_oda,
            'user_gift_info': user_gift_info,
            'random_ma': ma_random,
            'random_ji': ji_random,
            'random_kun': kun_random,
            'random_gift_code': random_gift_code,
            'random_gift_info': random_gift_info
        }
        
        # Получаем предсказание от ИИ
        interpretation = await ai_handler.get_prediction(prediction_data)
        
        await processing_msg.delete()
        
        # Отправляем результат
        max_length = 4000
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        if len(interpretation) > max_length:
            parts = [interpretation[i:i+max_length] for i in range(0, len(interpretation), max_length)]
            for part in parts:
                await message.answer(part, parse_mode="Markdown")
        else:
            await message.answer(interpretation, reply_markup=get_main_menu(subscription), parse_mode="Markdown")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при предсказании на событие: {e}", exc_info=True)
        try:
            await processing_msg.delete()
        except:
            pass
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            f"❌ Произошла ошибка:\n\n`{str(e)[:300]}`\n\nПопробуйте еще раз позже.",
            reply_markup=get_main_menu(subscription),
            parse_mode="Markdown"
        )
        await state.clear()

@dp.message(UserStates.waiting_for_prediction_partner_birth_date)
async def process_prediction_partner_birth_date(message: Message, state: FSMContext):
    """Обработка даты рождения партнера"""
    partner_birth_date = message.text.strip()
    data = await state.get_data()
    user_birth_date = data.get('user_birth_date')
    
    # Проверяем формат даты
    try:
        day, month, year = calculator.parse_date(partner_birth_date)
        
        # Обрабатываем совместимость
        processing_msg = await message.answer(
            "💑 Анализирую совместимость пары...\n⏳ Пожалуйста, подождите...",
            parse_mode="Markdown"
        )
        
        try:
            # Рассчитываем Ода для обоих
            user_oda = calculator.calculate_oda(user_birth_date)
            partner_oda = calculator.calculate_oda(partner_birth_date)
            
            # Получаем информацию о дарах из базы
            from src.gifts_knowledge import get_gift_info
            user_gift_info = get_gift_info(user_oda['gift_code'])
            partner_gift_info = get_gift_info(partner_oda['gift_code'])
            
            # Формируем данные для ИИ
            prediction_data = {
                'prediction_type': 'compatibility',
                'user_birth_date': user_birth_date,
                'partner_birth_date': partner_birth_date,
                'user_oda': user_oda,
                'partner_oda': partner_oda,
                'user_gift_info': user_gift_info,
                'partner_gift_info': partner_gift_info
            }
            
            # Получаем предсказание от ИИ
            interpretation = await ai_handler.get_prediction(prediction_data)
            
            await processing_msg.delete()
            
            # Отправляем результат
            max_length = 4000
            user_id = message.from_user.id
            subscription = await check_subscription_with_admin(user_id)
            if len(interpretation) > max_length:
                parts = [interpretation[i:i+max_length] for i in range(0, len(interpretation), max_length)]
                for part in parts:
                    await message.answer(part, parse_mode="Markdown")
            else:
                await message.answer(interpretation, reply_markup=get_main_menu(subscription), parse_mode="Markdown")
            
            await state.clear()
            
        except Exception as e:
            logger.error(f"Ошибка при анализе совместимости: {e}", exc_info=True)
            try:
                await processing_msg.delete()
            except:
                pass
            user_id = message.from_user.id
            subscription = await check_subscription_with_admin(user_id)
            await message.answer(
                f"❌ Произошла ошибка:\n\n`{str(e)[:300]}`\n\nПопробуйте еще раз позже.",
                reply_markup=get_main_menu(subscription),
                parse_mode="Markdown"
            )
            await state.clear()
            
    except ValueError as e:
        await message.answer(
            f"❌ {str(e)}\n\nПопробуйте еще раз в формате ДД.ММ.ГГГГ",
            parse_mode="Markdown"
        )

async def process_prediction_day_calculation(message: Message, state: FSMContext, birth_date: str):
    """Обработка предсказания на день"""
    user_id = message.from_user.id
    
    processing_msg = await message.answer(
        "📅 Рассчитываю предсказание на день...\n⏳ Пожалуйста, подождите...",
        parse_mode="Markdown"
    )
    
    try:
        # Рассчитываем Ода для пользователя
        user_oda = calculator.calculate_oda(birth_date)
        
        # Рассчитываем дар дня (по текущей дате)
        day_gift_data = calculator.calculate_day_gift()
        
        # Получаем информацию о дарах из базы
        from src.gifts_knowledge import get_gift_info
        user_gift_info = get_gift_info(user_oda['gift_code'])
        day_gift_info = get_gift_info(day_gift_data['gift_code'])
        
        # Формируем данные для ИИ
        prediction_data = {
            'prediction_type': 'day',
            'user_birth_date': birth_date,
            'user_oda': user_oda,
            'user_gift_info': user_gift_info,
            'day_gift': day_gift_data,
            'day_gift_info': day_gift_info
        }
        
        # Получаем предсказание от ИИ
        interpretation = await ai_handler.get_prediction(prediction_data)
        
        await processing_msg.delete()
        
        # Отправляем результат
        max_length = 4000
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        if len(interpretation) > max_length:
            parts = [interpretation[i:i+max_length] for i in range(0, len(interpretation), max_length)]
            for part in parts:
                await message.answer(part, parse_mode="Markdown")
        else:
            await message.answer(interpretation, reply_markup=get_main_menu(subscription), parse_mode="Markdown")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при предсказании на день: {e}", exc_info=True)
        try:
            await processing_msg.delete()
        except:
            pass
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            f"❌ Произошла ошибка:\n\n`{str(e)[:300]}`\n\nПопробуйте еще раз позже.",
            reply_markup=get_main_menu(subscription),
            parse_mode="Markdown"
        )
        await state.clear()

@dp.message(F.text == "⚗️ Алхимия даров")
async def button_alchemy(message: Message, state: FSMContext):
    """Кнопка алхимии даров"""
    user_id = message.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    # Проверка доступа - требуется уровень ORDEN
    if not check_feature_access(subscription, 'orden'):
        text = """⚗️ *Алхимия даров*

❌ *Доступ ограничен*

Алхимия даров доступна только для подписки *ORDEN*.

*ORDEN* включает:
• ⚗️ Алхимия даров
• 📿 Сантры
• 🔮 Анализ слов
• ✨ Все остальные функции

Оформите подписку ORDEN для доступа к этой функции."""
        await message.answer(text, reply_markup=get_subscription_menu(), parse_mode="Markdown")
        return
    
    text = """⚗️ *Алхимия даров*

Расчет по системе Ма-Жи-Кун с использованием полей от 1 до 9.

*Как это работает:*
Введите три цифры, соответствующие позициям:
• *МА* (потенциал) - первая цифра
• *ЖИ* (проявленность) - вторая цифра  
• *КУН* (творение) - третья цифра

*Формат ввода:*
• `111` или `1-1-1` или любым другим способом
• ⚠️ Если вы введете больше цифр - будут восприняты только первые 3

*Примеры:*
• `123` - МА=1, ЖИ=2, КУН=3
• `5-7-9` - МА=5, ЖИ=7, КУН=9

Введите три цифры:"""
    
    await message.answer(text, parse_mode="Markdown")
    await state.set_state(UserStates.waiting_for_alchemy_numbers)

@dp.message(UserStates.waiting_for_alchemy_numbers)
async def process_alchemy_numbers(message: Message, state: FSMContext):
    """Обработка введенных цифр для алхимии"""
    user_id = message.from_user.id
    input_text = message.text.strip()
    
    # Проверяем подписку
    subscription = await check_subscription_with_admin(user_id)
    if not subscription['active']:
        text = """⚠️ *Подписка не активна*

Для алхимии даров необходима активная подписка.

⭐️ *Премиум подписка:*
📅 Месяц - {month_price} ⭐️
📆 Год - {year_price} ⭐️

🎁 Что вы получите:
• Безлимитные расчеты даров
• Алхимия даров с ИИ
• Полный анализ
• Персональные рекомендации

_Нажмите кнопку ниже для оформления подписки_""".format(
            month_price=Config.PRO_MONTH_PRICE,
            year_price=Config.PRO_YEAR_PRICE
        )
        await message.answer(text, reply_markup=get_subscription_menu(), parse_mode="Markdown")
        await state.clear()
        return
    
    # Извлекаем все цифры из введенного текста
    digits = re.findall(r'\d', input_text)
    
    # Проверяем количество цифр
    if len(digits) < 3:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="« Назад в главное меню", callback_data="back_to_main_alchemy")]
        ])
        await message.answer(
            "❌ *Недостаточно цифр*\n\n"
            "Пожалуйста, введите 3 цифры для позиций МА-ЖИ-КУН.\n\n"
            "Например: `111` или `1-2-3`",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return
    
    # Берем первые 3 цифры
    ma_num = int(digits[0])
    zhi_num = int(digits[1])
    kun_num = int(digits[2])
    
    # Проверяем диапазон (должны быть от 1 до 9)
    if not (1 <= ma_num <= 9) or not (1 <= zhi_num <= 9) or not (1 <= kun_num <= 9):
        await message.answer(
            "❌ *Неверный диапазон*\n\n"
            "Цифры должны быть от 1 до 9 включительно.\n\n"
            "Попробуйте еще раз.",
            parse_mode="Markdown"
        )
        return
    
    # ОБЯЗАТЕЛЬНО отправляем временное сообщение об обработке СРАЗУ после получения валидных цифр
    processing_msg = await message.answer(
        "⚗️ Ваши данные обрабатываются с помощью ИИ...\n⏳ Пожалуйста, подождите...",
        parse_mode="Markdown"
    )
    
    # Если было больше 3 цифр, предупреждаем (после сообщения об обработке)
    warning_msg = None
    if len(digits) > 3:
        warning_msg = await message.answer(
            f"⚠️ Введено {len(digits)} цифр. Будут использованы только первые 3: {ma_num}-{zhi_num}-{kun_num}",
            parse_mode="Markdown"
        )
    
    # Получаем данные из базы
    ma_position = await db.get_ma_zhi_kun_position("МА")
    zhi_position = await db.get_ma_zhi_kun_position("ЖИ")
    kun_position = await db.get_ma_zhi_kun_position("КУН")
    
    ma_field = await db.get_gift_field(ma_num)
    zhi_field = await db.get_gift_field(zhi_num)
    kun_field = await db.get_gift_field(kun_num)
    
    if not ma_position or not zhi_position or not kun_position:
        # Удаляем сообщение о обработке при ошибке
        try:
            await processing_msg.delete()
        except:
            pass
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            "❌ Ошибка: не найдены позиции Ма-Жи-Кун в базе данных.\n"
            "Обратитесь к администратору.",
            reply_markup=get_main_menu(subscription)
        )
        await state.clear()
        return
    
    if not ma_field or not zhi_field or not kun_field:
        # Удаляем сообщение о обработке при ошибке
        try:
            await processing_msg.delete()
        except:
            pass
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            f"❌ Ошибка: не найдены поля в базе данных.\n"
            f"Проверьте, что поля {ma_num}, {zhi_num}, {kun_num} существуют.\n"
            "Обратитесь к администратору.",
            reply_markup=get_main_menu(subscription)
        )
        await state.clear()
        return
    
    # Обновляем сообщение о начале анализа (меняем текст на более конкретный перед отправкой к ИИ)
    try:
        await processing_msg.edit_text(
            "⚗️ Анализирую алхимию даров с помощью ИИ...\n⏳ Пожалуйста, подождите...",
            parse_mode="Markdown"
        )
    except:
        # Если не удалось отредактировать, оставляем как есть
        pass
    
    try:
        # Формируем данные для ИИ
        alchemy_data = {
            'ma': {
                'position': {
                    'name': ma_position['name'],
                    'description': ma_position['description']
                },
                'field': {
                    'id': ma_field['id'],
                    'name': ma_field['name'],
                    'description': ma_field['description']
                }
            },
            'zhi': {
                'position': {
                    'name': zhi_position['name'],
                    'description': zhi_position['description']
                },
                'field': {
                    'id': zhi_field['id'],
                    'name': zhi_field['name'],
                    'description': zhi_field['description']
                }
            },
            'kun': {
                'position': {
                    'name': kun_position['name'],
                    'description': kun_position['description']
                },
                'field': {
                    'id': kun_field['id'],
                    'name': kun_field['name'],
                    'description': kun_field['description']
                }
            }
        }
        
        # Получаем анализ от ИИ
        interpretation = await ai_handler.get_alchemy_interpretation(alchemy_data)
        
        # Удаляем сообщение о обработке
        await processing_msg.delete()
        
        # Отправляем результат
        max_length = 4000
        if len(interpretation) > max_length:
            parts = [interpretation[i:i+max_length] for i in range(0, len(interpretation), max_length)]
            for i, part in enumerate(parts):
                if i == 0:
                    await message.answer(part, parse_mode="Markdown")
                else:
                    await message.answer(part, parse_mode="Markdown")
        else:
            user_id = message.from_user.id
            subscription = await check_subscription_with_admin(user_id)
            await message.answer(interpretation, reply_markup=get_main_menu(subscription), parse_mode="Markdown")
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при анализе алхимии: {e}", exc_info=True)
        
        try:
            await processing_msg.delete()
        except:
            pass
        
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            f"❌ Произошла ошибка при анализе:\n\n`{str(e)[:300]}`\n\nПопробуйте еще раз позже.",
            reply_markup=get_main_menu(subscription),
            parse_mode="Markdown"
        )
        await state.clear()

@dp.callback_query(F.data == "alphabet_analyze")
async def handle_alphabet_analyze_start(callback: CallbackQuery, state: FSMContext):
    """Начало анализа слова"""
    user_id = callback.from_user.id
    subscription = await check_subscription_with_admin(user_id)
    
    # Проверка доступа - требуется уровень ORDEN
    if not check_feature_access(subscription, 'orden'):
        await callback.answer("❌ Анализ слов доступен только для подписки ORDEN", show_alert=True)
        await callback.message.edit_text(
            "❌ *Доступ ограничен*\n\nАнализ слов доступен только для подписки *ORDEN*.\n\nОформите подписку ORDEN для доступа к этой функции.",
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        return
    
    text = """✍️ *Анализ слова или фразы*

Отправьте мне слово, которое хотите проанализировать.

*Что можно отправить:*
• Одно слово (например: "Любовь")
• Имя (например: "Мария")
• Название дара (например: "Мана")
• Число дара (например: "42")
• Фразу (будет проанализирована целиком)

*⚠️ ВАЖНО:* 
• Лучше всего анализировать ОДНО слово за раз
• Если отправите фразу - каждое слово будет проанализировано отдельно, затем дан общий смысл
• Регистр не важен

Отправьте слово для анализа:"""
    
    await callback.message.edit_text(text, parse_mode="Markdown")
    await state.set_state(UserStates.waiting_for_word_to_analyze)
    await callback.answer()

@dp.message(UserStates.waiting_for_word_to_analyze)
async def process_word_to_analyze(message: Message, state: FSMContext):
    """Обработка слова для анализа"""
    word_text = message.text.strip()
    
    if not word_text:
        await message.answer("❌ Слово не может быть пустым. Попробуйте еще раз:")
        return
    
    # Проверяем количество слов
    words = word_text.split()
    
    if len(words) > 3:
        await message.answer(
            "⚠️ Вы отправили слишком много слов!\n\n"
            "Для качественного анализа рекомендуется анализировать по одному слову.\n"
            "Продолжить анализ всей фразы? Это может занять время.",
            reply_markup=get_alphabet_menu()
        )
        await state.clear()
        return
    
    # Отправляем сообщение о начале анализа
    processing_msg = await message.answer("🔮 Анализирую через алфавит с помощью ИИ...\n⏳ Это может занять 10-20 секунд...")
    
    try:
        # Выполняем анализ
        if len(words) == 1:
            analysis = await alphabet_analyzer.analyze_word(word_text, message.from_user.id)
            result_text = await alphabet_analyzer.format_result_for_user(analysis)
        else:
            analysis = await alphabet_analyzer.analyze_phrase(word_text, message.from_user.id)
            result_text = await alphabet_analyzer.format_phrase_result(analysis)
        
        # Редактируем сообщение о завершении
        try:
            await processing_msg.edit_text("✅ Анализ завершен!")
        except:
            pass  # Если не удалось отредактировать, просто продолжаем
        
        # Отправляем результат
        # Разбиваем на части если текст слишком длинный
        max_length = 4000
        if len(result_text) > max_length:
            parts = [result_text[i:i+max_length] for i in range(0, len(result_text), max_length)]
            for part in parts:
                await message.answer(part, parse_mode="HTML")
        else:
            await message.answer(result_text, parse_mode="HTML")
        
        # Отправляем кнопки отдельным сообщением
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Проанализировать еще", callback_data="alphabet_analyze")],
            [InlineKeyboardButton(text="« Назад", callback_data="back_to_main")]
        ])
        
        await message.answer("Выберите действие:", reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Ошибка при анализе слова: {e}", exc_info=True)
        try:
            await processing_msg.edit_text("❌ Произошла ошибка при анализе")
        except:
            pass
        await message.answer(
            f"❌ Произошла ошибка при анализе:\n<code>{str(e)}</code>\n\nПопробуйте еще раз или обратитесь к администратору.",
            reply_markup=get_alphabet_menu(),
            parse_mode="HTML"
        )
    
    await state.clear()

@dp.callback_query(F.data == "back_to_alphabet")
async def back_to_alphabet(callback: CallbackQuery):
    """Возврат к меню алфавита"""
    text = """🔮 *Анализ слов через алфавит*

Каждая буква несет в себе особую энергию и значение. Я могу проанализировать любое слово, имя или фразу, раскрыв их глубинный смысл.

Выберите действие:"""
    
    await callback.message.edit_text(text, reply_markup=get_alphabet_menu(), parse_mode="Markdown")
    await callback.answer()

# ========== ПРОМОКОДЫ ==========

@dp.callback_query(F.data == "enter_promocode")
async def enter_promocode_handler(callback: CallbackQuery, state: FSMContext):
    """Начало ввода промокода"""
    await callback.message.answer(
        "🎁 *Введите промокод*\n\nОтправьте код для активации скидки или бесплатной подписки:",
        parse_mode="Markdown"
    )
    await state.set_state(UserStates.waiting_for_promocode)
    await callback.answer()

@dp.message(UserStates.waiting_for_promocode)
async def process_promocode(message: Message, state: FSMContext):
    """Обработка введенного промокода"""
    user_id = message.from_user.id
    code = message.text.strip().upper()
    
    # Получаем промокод
    promo = await db.get_promocode(code)
    
    if not promo:
        await message.answer(
            "❌ *Промокод не найден*\n\nПроверьте правильность ввода и попробуйте снова.",
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    # Проверяем, использовал ли пользователь этот промокод
    if await db.check_user_used_promocode(user_id, promo['id']):
        await message.answer(
            "❌ *Промокод уже использован*\n\nВы уже активировали этот промокод ранее.",
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    # Проверяем лимит использований
    if promo['max_uses'] is not None and promo['current_uses'] >= promo['max_uses']:
        await message.answer(
            "❌ *Промокод исчерпан*\n\nЭтот промокод больше недоступен для использования.",
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
        await state.clear()
        return
    
    # Применяем промокод
    if promo['type'] == 'subscription':
        # Выдаем подписку
        days = promo['subscription_days']
        sub_type = promo['subscription_type'] if promo['subscription_type'] is not None else 'pro'  # По умолчанию pro
        
        # Определяем тип подписки для сохранения
        if sub_type == 'orden':
            # Определяем длительность для ORDEN
            if days >= 365:
                type_name = 'orden_year'
            else:
                type_name = 'orden_month'
        else:
            # Определяем длительность для PRO
            if days >= 365:
                type_name = 'pro_year'
            else:
                type_name = 'pro_month'
        
        end_date = await db.update_subscription(user_id, type_name, days)
        
        # Регистрируем использование
        await db.use_promocode(user_id, promo['id'])
        
        sub_type_name = "ORDEN" if sub_type == 'orden' else "PRO"
        access_text = "полный доступ ко всем функциям, включая алхимию, сантры и анализ слов" if sub_type == 'orden' else "доступ к базовым функциям (без алхимии, сантр и анализа слов)"
        
        user_id = message.from_user.id
        subscription = await check_subscription_with_admin(user_id)
        await message.answer(
            f"✅ *Промокод активирован!*\n\n"
            f"🎉 Вам выдана подписка *{sub_type_name}* на *{days} дней*!\n"
            f"💫 Действительна до: `{end_date.strftime('%d.%m.%Y %H:%M')}`\n\n"
            f"Теперь у вас {access_text}!",
            reply_markup=get_main_menu(subscription),
            parse_mode="Markdown"
        )
    
    elif promo['type'] == 'discount':
        # Сохраняем скидку в состоянии для следующей оплаты
        await state.update_data(active_discount=promo['discount_percent'], promo_id=promo['id'])
        
        await message.answer(
            f"✅ *Промокод активирован!*\n\n"
            f"💰 Вам доступна скидка *{promo['discount_percent']}%* на следующую покупку!\n\n"
            f"Перейдите в меню оформления подписки для применения скидки.",
            reply_markup=get_subscription_menu(),
            parse_mode="Markdown"
        )
    
    await state.clear()

# ========== АДМИН-ПАНЕЛЬ ==========

@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    """Админ-панель"""
    user_id = message.from_user.id
    
    if not await db.is_admin(user_id):
        await message.answer("❌ У вас нет прав доступа к админ-панели.")
        return
    
    text = """👑 *Админ-панель*

Управление промокодами и статистика бота.

Выберите действие:"""
    
    await message.answer(text, reply_markup=get_admin_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "admin_create_promo")
async def admin_create_promo_start(callback: CallbackQuery, state: FSMContext):
    """Начало создания промокода"""
    user_id = callback.from_user.id
    
    if not await db.is_admin(user_id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    keyboard = [
        [InlineKeyboardButton(text="🎁 Подписка", callback_data="promo_type_subscription")],
        [InlineKeyboardButton(text="💰 Скидка", callback_data="promo_type_discount")],
        [InlineKeyboardButton(text="« Отмена", callback_data="admin_cancel")]
    ]
    
    await callback.message.edit_text(
        "📝 *Создание промокода*\n\nВыберите тип промокода:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("promo_type_"))
async def admin_promo_type_selected(callback: CallbackQuery, state: FSMContext):
    """Выбор типа промокода"""
    user_id = callback.from_user.id
    
    if not await db.is_admin(user_id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    promo_type = callback.data.replace("promo_type_", "")
    await state.update_data(promo_type=promo_type)
    
    if promo_type == "subscription":
        keyboard = [
            [InlineKeyboardButton(text="⭐ PRO", callback_data="promo_sub_type_pro")],
            [InlineKeyboardButton(text="👑 ORDEN", callback_data="promo_sub_type_orden")],
            [InlineKeyboardButton(text="« Назад", callback_data="admin_create_promo")]
        ]
        await callback.message.edit_text(
            "📝 *Создание промокода: Подписка*\n\n"
            "Выберите тип подписки:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        await state.set_state(UserStates.waiting_for_promo_sub_type)
        await callback.answer()
        return
    else:
        await callback.message.edit_text(
            "📝 *Создание промокода: Скидка*\n\n"
            "Введите процент скидки (например: 20):",
            parse_mode="Markdown"
        )
        await state.set_state(UserStates.waiting_for_promo_value)
    
    await callback.answer()

@dp.callback_query(F.data.startswith("promo_sub_type_"))
async def admin_promo_sub_type_selected(callback: CallbackQuery, state: FSMContext):
    """Выбор типа подписки для промокода"""
    user_id = callback.from_user.id
    
    if not await db.is_admin(user_id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    sub_type = callback.data.replace("promo_sub_type_", "")  # pro или orden
    await state.update_data(promo_sub_type=sub_type)
    
    await callback.message.edit_text(
        f"📝 *Создание промокода: Подписка {sub_type.upper()}*\n\n"
        "Введите количество дней подписки (например: 30):",
        parse_mode="Markdown"
    )
    await state.set_state(UserStates.waiting_for_promo_value)
    await callback.answer()

@dp.message(UserStates.waiting_for_promo_value)
async def admin_promo_value_entered(message: Message, state: FSMContext):
    """Обработка значения промокода"""
    user_id = message.from_user.id
    
    if not await db.is_admin(user_id):
        await message.answer("❌ Нет доступа")
        await state.clear()
        return
    
    try:
        value = int(message.text.strip())
        
        data = await state.get_data()
        promo_type = data['promo_type']
        
        if promo_type == 'discount' and (value < 1 or value > 100):
            await message.answer("❌ Скидка должна быть от 1 до 100%")
            return
        
        if promo_type == 'subscription' and value < 1:
            await message.answer("❌ Количество дней должно быть больше 0")
            return
        
        await state.update_data(promo_value=value)
        
        await message.answer(
            "📝 *Ограничение использований*\n\n"
            "Введите максимальное количество использований промокода\n"
            "(отправьте 0 для безлимита):",
            parse_mode="Markdown"
        )
        await state.set_state(UserStates.waiting_for_promo_max_uses)
        
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.message(UserStates.waiting_for_promo_max_uses)
async def admin_promo_max_uses_entered(message: Message, state: FSMContext):
    """Обработка лимита использований и создание промокода"""
    user_id = message.from_user.id
    
    if not await db.is_admin(user_id):
        await message.answer("❌ Нет доступа")
        await state.clear()
        return
    
    try:
        max_uses = int(message.text.strip())
        
        if max_uses < 0:
            await message.answer("❌ Количество должно быть >= 0")
            return
        
        # Генерируем код
        code = generate_promocode()
        
        data = await state.get_data()
        promo_type = data['promo_type']
        value = data['promo_value']
        
        # Создаем промокод
        try:
            if promo_type == 'subscription':
                sub_type = data.get('promo_sub_type', 'pro')  # По умолчанию pro
                await db.create_promocode(
                    code=code,
                    promo_type='subscription',
                    created_by=user_id,
                    subscription_days=value,
                    subscription_type=sub_type,
                    max_uses=max_uses if max_uses > 0 else None
                )
                sub_type_name = "PRO" if sub_type == 'pro' else "ORDEN"
                type_desc = f"🎁 Подписка {sub_type_name} на {value} дней"
            else:
                await db.create_promocode(
                    code=code,
                    promo_type='discount',
                    created_by=user_id,
                    discount_percent=value,
                    max_uses=max_uses if max_uses > 0 else None
                )
                type_desc = f"💰 Скидка {value}%"
            
            uses_desc = "♾ Безлимит" if max_uses == 0 else f"🔢 {max_uses} использований"
            
            await message.answer(
                f"✅ *Промокод создан!*\n\n"
                f"🎟 Код: `{code}`\n"
                f"{type_desc}\n"
                f"{uses_desc}\n\n"
                f"Пользователи могут ввести этот код в разделе подписок.",
                reply_markup=get_admin_menu(),
                parse_mode="Markdown"
            )
            
            await state.clear()
        except Exception as e:
            logger.error(f"Ошибка при создании промокода: {e}", exc_info=True)
            await message.answer(
                f"❌ *Ошибка при создании промокода*\n\n"
                f"Произошла ошибка: `{str(e)[:200]}`\n\n"
                f"Попробуйте еще раз или обратитесь к администратору.",
                reply_markup=get_admin_menu(),
                parse_mode="Markdown"
            )
            await state.clear()
        
    except ValueError:
        await message.answer("❌ Введите число!")

@dp.callback_query(F.data == "admin_list_promos")
async def admin_list_promos(callback: CallbackQuery):
    """Список промокодов"""
    user_id = callback.from_user.id
    
    if not await db.is_admin(user_id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    promos = await db.get_all_promocodes()
    
    if not promos:
        await callback.message.edit_text(
            "📋 *Список промокодов*\n\nПромокодов пока нет.",
            reply_markup=get_admin_menu(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    text = "📋 *Список промокодов*\n\n"
    
    keyboard = []
    
    for promo in promos[:20]:  # Показываем первые 20
        status = "✅" if promo['is_active'] else "❌"
        
        if promo['type'] == 'subscription':
            sub_type = promo['subscription_type'] if promo['subscription_type'] is not None else 'pro'
            sub_type_name = "PRO" if sub_type == 'pro' else "ORDEN"
            type_desc = f"🎁 {sub_type_name} {promo['subscription_days']}д"
        else:
            type_desc = f"💰 {promo['discount_percent']}%"
        
        uses = f"{promo['current_uses']}"
        if promo['max_uses']:
            uses += f"/{promo['max_uses']}"
        else:
            uses += "/∞"
        
        text += f"{status} `{promo['code']}` - {type_desc} ({uses})\n"
        
        # Добавляем кнопку удаления для каждого промокода
        keyboard.append([
            InlineKeyboardButton(
                text=f"🗑️ Удалить {promo['code']}",
                callback_data=f"admin_delete_promo_{promo['id']}"
            )
        ])
    
    if len(promos) > 20:
        text += f"\n_... и еще {len(promos) - 20} кодов_"
    
    # Добавляем кнопку "Назад"
    keyboard.append([InlineKeyboardButton(text="« Назад", callback_data="admin_cancel")])
    
    await callback.message.edit_text(
        text, 
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard), 
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_delete_promo_"))
async def admin_delete_promo(callback: CallbackQuery):
    """Удаление промокода"""
    user_id = callback.from_user.id
    
    if not await db.is_admin(user_id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    # Извлекаем ID промокода из callback_data
    promo_id = int(callback.data.replace("admin_delete_promo_", ""))
    
    # Получаем информацию о промокоде
    promos = await db.get_all_promocodes()
    promo = None
    for p in promos:
        if p['id'] == promo_id:
            promo = p
            break
    
    if not promo:
        await callback.answer("❌ Промокод не найден", show_alert=True)
        return
    
    # Удаляем промокод
    try:
        await db.delete_promocode(promo_id)
        await callback.answer(f"✅ Промокод {promo['code']} удален", show_alert=True)
        
        # Обновляем список промокодов
        await admin_list_promos(callback)
    except Exception as e:
        logger.error(f"Ошибка при удалении промокода: {e}", exc_info=True)
        await callback.answer("❌ Ошибка при удалении промокода", show_alert=True)

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    """Статистика"""
    user_id = callback.from_user.id
    
    if not await db.is_admin(user_id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    # Получаем статистику подписок
    stats = await db.get_subscription_stats()
    
    text = "📊 *Статистика бота*\n\n"
    
    total_users = 0
    active_users = 0
    
    for row in stats:
        sub_type = row[0]
        count = row[1]
        active_count = row[2]
        
        total_users += count
        active_users += active_count
        
        text += f"*{sub_type}*: {count} ({active_count} активных)\n"
    
    text += f"\n*Всего*: {total_users} пользователей\n"
    text += f"*Активных*: {active_users} подписок"
    
    await safe_edit_text(callback.message, text, reply_markup=get_admin_menu(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "admin_list_users")
async def admin_list_users(callback: CallbackQuery):
    """Список пользователей с подписками"""
    user_id = callback.from_user.id
    
    if not await db.is_admin(user_id):
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    users = await db.get_all_users_with_subscriptions(limit=50)
    
    if not users:
        text = "👥 *Пользователи*\n\n❌ Пользователи не найдены"
        await callback.message.edit_text(text, reply_markup=get_admin_menu(), parse_mode="Markdown")
        await callback.answer()
        return
    
    from datetime import datetime
    
    text = f"👥 *Пользователи* ({len(users)})\n\n"
    
    active_count = 0
    expired_count = 0
    trial_count = 0
    premium_count = 0
    
    for user in users[:20]:  # Показываем первые 20
        user_id_val = user['user_id']
        username = user['username'] or "—"
        first_name = user['first_name'] or "—"
        sub_type = user['subscription_type'] or "—"
        sub_end = user['subscription_end_date']
        is_admin = "👑" if user['is_admin'] == 1 else ""
        
        # Определяем статус подписки
        status = ""
        if sub_end:
            try:
                end_date = datetime.fromisoformat(sub_end)
                now = datetime.now()
                if end_date > now:
                    days_left = (end_date - now).days
                    status = f"🟢 ({days_left}д)"
                    active_count += 1
                    if sub_type.startswith('premium'):
                        premium_count += 1
                else:
                    status = "🔴"
                    expired_count += 1
            except:
                status = "⚠️"
        elif sub_type == "trial":
            status = "🟡"
            trial_count += 1
        else:
            status = "⚪"
        
        text += f"{is_admin} *{user_id_val}* | @{username}\n"
        text += f"   {first_name} | {sub_type} {status}\n\n"
    
    if len(users) > 20:
        text += f"\n... и еще {len(users) - 20} пользователей\n"
    
    text += f"\n📊 *Статистика:*\n"
    text += f"🟢 Активных: {active_count}\n"
    text += f"🟡 Trial: {trial_count}\n"
    text += f"⭐ Premium: {premium_count}\n"
    text += f"🔴 Истекших: {expired_count}"
    
    await safe_edit_text(callback.message, text, reply_markup=get_admin_menu(), parse_mode="Markdown")
    await callback.answer()

@dp.callback_query(F.data == "admin_cancel")
async def admin_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена админской операции"""
    await state.clear()
    await safe_edit_text(
        callback.message,
        "👑 *Админ-панель*\n\nОперация отменена.",
        reply_markup=get_admin_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

def generate_promocode(length: int = 12) -> str:
    """Генерация случайного промокода"""
    # Используем буквы и цифры, исключая похожие символы (0, O, I, 1, l)
    chars = string.ascii_uppercase.replace('O', '').replace('I', '') + string.digits.replace('0', '').replace('1', '')
    return ''.join(secrets.choice(chars) for _ in range(length))

# ========== ПРОВЕРКА АДМИНА ПРИ ПОДПИСКЕ ==========

async def check_subscription_with_admin(user_id: int) -> dict:
    """Проверка подписки с учетом админских прав"""
    # Админы имеют безлимитный доступ (уровень ORDEN)
    if await db.is_admin(user_id):
        return {
            "active": True, 
            "type": "admin", 
            "level": "orden",
            "end_date": None
        }
    
    # Обычная проверка подписки
    subscription = await db.check_subscription(user_id)
    
    # Определяем уровень доступа
    if subscription.get('active'):
        sub_type = subscription.get('type', '')
        level = Config.SUBSCRIPTION_LEVELS.get(sub_type, 'trial')
        subscription['level'] = level
    else:
        subscription['level'] = 'trial'
    
    return subscription

def check_feature_access(subscription: dict, required_level: str) -> bool:
    """
    Проверка доступа к функции по уровню подписки
    
    Args:
        subscription: Результат check_subscription_with_admin
        required_level: Требуемый уровень ('trial', 'pro', 'orden')
    
    Returns:
        bool: True если доступ разрешен
    """
    if not subscription.get('active'):
        return False
    
    level = subscription.get('level', 'trial')
    
    # Иерархия уровней: trial = pro < orden
    # TRIAL имеет те же права что PRO для доступа к функциям
    level_hierarchy = {'trial': 1, 'pro': 1, 'orden': 2}
    user_level = level_hierarchy.get(level, 0)
    required = level_hierarchy.get(required_level, 0)
    
    return user_level >= required

async def init_bot_components():
    """Инициализация компонентов бота (база данных, данные и т.д.)"""
    logger.info("Инициализация базы данных...")
    try:
        await db.init_db()
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при инициализации БД (продолжаю): {e}")
    
    logger.info("Инициализация данных алфавита...")
    try:
        await db.init_alphabet_data()
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при инициализации алфавита (продолжаю): {e}")
    
    logger.info("Инициализация данных позиций Ма-Жи-Кун...")
    try:
        await db.init_ma_zhi_kun_data()
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при инициализации позиций Ма-Жи-Кун (продолжаю): {e}")
    
    logger.info("Инициализация данных полей (1-9)...")
    try:
        await db.init_gift_fields_data()
    except Exception as e:
        logger.warning(f"⚠️ Ошибка при инициализации полей (продолжаю): {e}")
    
    # Инициализация админов из конфига
    if Config.ADMIN_IDS:
        logger.info(f"Инициализация администраторов: {Config.ADMIN_IDS}")
        for admin_id in Config.ADMIN_IDS:
            await db.set_admin(admin_id, True)
            logger.info(f"✅ Админ {admin_id} добавлен")
    else:
        logger.warning("⚠️ Администраторы не настроены! Добавьте ADMIN_IDS в переменные окружения.")

async def main():
    """Главная функция запуска бота (для polling режима)"""
    logger.info("=" * 50)
    logger.info("ЗАПУСК БОТА (POLLING MODE)")
    logger.info("=" * 50)
    
    # Проверка переменных окружения
    logger.info(f"BOT_TOKEN: {'✅ Установлен' if Config.BOT_TOKEN else '❌ НЕ УСТАНОВЛЕН'}")
    logger.info(f"DEEPSEEK_API_KEY: {'✅ Установлен' if Config.DEEPSEEK_API_KEY else '❌ НЕ УСТАНОВЛЕН'}")
    logger.info(f"ADMIN_IDS: {Config.ADMIN_IDS if Config.ADMIN_IDS else '❌ НЕ УСТАНОВЛЕНЫ'}")
    
    # Инициализация компонентов
    await init_bot_components()
    
    logger.info("=" * 50)
    logger.info("Запуск бота (polling)...")
    logger.info("=" * 50)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")

