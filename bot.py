"""
Основной файл Telegram бота для работы с дарами
"""
import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import Config
from database import Database
from calculations import GiftsCalculator
from ai_handler import AIHandler
from keyboards import get_main_menu, get_subscription_menu, get_premium_options_menu

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

# Состояния FSM
class UserStates(StatesGroup):
    waiting_for_birth_date = State()
    waiting_for_question = State()

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Добавляем пользователя в базу данных
    await db.add_user(user_id, username, first_name)
    
    # Проверяем подписку
    subscription = await db.check_subscription(user_id)
    
    welcome_text = f"""👋 *Добро пожаловать, {first_name}!*

🎁 Я помогу вам раскрыть ваши дары, заложенные при рождении по древнеславянской системе *Ма-Жи-Кун*.

🔮 С помощью даты вашего рождения я рассчитаю ваш уникальный дар:
• *Ма* - энергия дня и месяца рождения
• *Жи* - энергия года рождения
• *Кун* - синтез энергий, ваш главный дар

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
    
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработка команды /help"""
    help_text = """❓ *Помощь по использованию бота*

*Доступные команды:*
/start - Начать работу с ботом
/calculate - Рассчитать свои дары
/subscription - Управление подпиской
/help - Показать эту справку

📊 *Система Ма-Жи-Кун*

Это древнеславянская система расчета даров по дате рождения:

🔢 *Ма* - сумма цифр дня и месяца рождения
🔢 *Жи* - сумма цифр года рождения
🎁 *Кун* - ваш главный дар (Ма + Жи)

✨ Всего в системе *64 уникальных дара*, каждый со своим названием, энергетикой и предназначением.

🤖 Бот использует ИИ для глубокого анализа вашего дара и практических рекомендаций.
"""
    await message.answer(help_text, reply_markup=get_main_menu(), parse_mode="Markdown")

@dp.message(Command("calculate"))
async def cmd_calculate(message: Message, state: FSMContext):
    """Начало расчета даров"""
    await message.answer(
        "📅 Введите вашу дату рождения в формате ДД.ММ.ГГГГ\n\nНапример: 15.05.1990",
        reply_markup=None
    )
    await state.set_state(UserStates.waiting_for_birth_date)

@dp.message(UserStates.waiting_for_birth_date)
async def process_birth_date(message: Message, state: FSMContext):
    """Обработка введенной даты рождения"""
    birth_date = message.text.strip()
    user_id = message.from_user.id
    
    # Проверяем подписку
    subscription = await db.check_subscription(user_id)
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
            month_price=Config.PREMIUM_MONTH_PRICE,
            year_price=Config.PREMIUM_YEAR_PRICE
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
        await message.answer(
            interpretation, 
            reply_markup=get_main_menu(),
            parse_mode="Markdown"
        )
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка при расчете даров: {e}")
        await message.answer(
            "❌ Произошла ошибка при расчете. Попробуйте еще раз.",
            reply_markup=get_main_menu()
        )
        await state.clear()

@dp.message(Command("subscription"))
async def cmd_subscription(message: Message):
    """Информация о подписке"""
    user_id = message.from_user.id
    subscription = await db.check_subscription(user_id)
    
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

💫 *Премиум подписка* - {Config.PREMIUM_PRICE_STARS} звезд
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
        month_price=Config.PREMIUM_MONTH_PRICE,
        year_price=Config.PREMIUM_YEAR_PRICE
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
    subscription = await db.check_subscription(user_id)
    
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
• Доступ ко всем базовым функциям

⭐️ *Премиум подписка*

*Что входит:*
• ✅ Безлимитные расчеты даров
• ✅ Полный анализ с помощью ИИ
• ✅ Подробные трактовки
• ✅ Персональные рекомендации
• ✅ Будущие функции (гадания, совместимость)

*Тарифы:*
🧪 Тест - {test_price} ⭐️ (1 день для тестирования)
📅 Месяц - {month_price} ⭐️
📆 Год - {year_price} ⭐️ (выгода ~17%)

💡 _Оплата через Telegram Stars_
🔒 _Безопасно и моментально_
""".format(
        trial_days=Config.TRIAL_DURATION_DAYS,
        test_price=Config.PREMIUM_TEST_PRICE,
        month_price=Config.PREMIUM_MONTH_PRICE,
        year_price=Config.PREMIUM_YEAR_PRICE
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=get_subscription_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_premium_test")
async def buy_premium_test(callback: CallbackQuery):
    """Покупка тестовой подписки на 1 день"""
    await send_invoice(
        callback.message,
        callback.from_user.id,
        "test",
        Config.PREMIUM_TEST_PRICE,
        "Тестовая подписка на 1 день"
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_premium_month")
async def buy_premium_month(callback: CallbackQuery):
    """Покупка подписки на месяц"""
    await send_invoice(
        callback.message,
        callback.from_user.id,
        "month",
        Config.PREMIUM_MONTH_PRICE,
        "Премиум подписка на 1 месяц"
    )
    await callback.answer()

@dp.callback_query(F.data == "buy_premium_year")
async def buy_premium_year(callback: CallbackQuery):
    """Покупка подписки на год"""
    await send_invoice(
        callback.message,
        callback.from_user.id,
        "year",
        Config.PREMIUM_YEAR_PRICE,
        "Премиум подписка на 1 год"
    )
    await callback.answer()

async def send_invoice(message: Message, user_id: int, subscription_type: str, 
                      price: int, description: str):
    """Отправка инвойса для оплаты"""
    
    # Формируем описание
    if subscription_type == "test":
        title = "🧪 ТЕСТ - 1 день"
        desc = "Тестовая подписка на 1 день для проверки системы оплаты"
    elif subscription_type == "month":
        title = "Премиум - 1 месяц"
        desc = "Доступ ко всем функциям бота на 30 дней"
    else:
        title = "Премиум - 1 год"
        desc = "Доступ ко всем функциям бота на 365 дней"
    
    # Создаем инвойс
    prices = [LabeledPrice(label=title, amount=price)]
    
    await bot.send_invoice(
        chat_id=user_id,
        title=title,
        description=desc,
        payload=f"premium_{subscription_type}_{user_id}",
        currency="XTR",  # Telegram Stars
        prices=prices
    )

@dp.pre_checkout_query()
async def pre_checkout_query_handler(pre_checkout_query: PreCheckoutQuery):
    """Обработка pre-checkout запроса"""
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: Message):
    """Обработка успешной оплаты"""
    payment = message.successful_payment
    user_id = message.from_user.id
    
    # Парсим payload для определения типа подписки
    payload_parts = payment.invoice_payload.split('_')
    subscription_type = payload_parts[1]  # test, month или year
    
    # Определяем длительность подписки
    if subscription_type == "test":
        days = Config.PREMIUM_TEST_DAYS
        type_name = "premium_test"
        period_text = "1 день (ТЕСТ)"
    elif subscription_type == "month":
        days = Config.PREMIUM_MONTH_DAYS
        type_name = "premium_month"
        period_text = "месяц"
    else:
        days = Config.PREMIUM_YEAR_DAYS
        type_name = "premium_year"
        period_text = "год"
    
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
    
    # Отправляем подтверждение
    text = f"""✅ *Оплата успешно выполнена!*

🎉 Ваша премиум подписка активирована!

📅 Тариф: *{period_text.capitalize()}*
💫 Действительна до: `{end_date.strftime('%d.%m.%Y %H:%M')}`
💰 Оплачено: *{payment.total_amount} ⭐️*

🎁 Теперь вам доступны все функции бота:
• Безлимитные расчеты даров
• Полный анализ с ИИ
• Персональные рекомендации
• Расширенные трактовки

Спасибо за поддержку! 🙏
"""
    
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_menu())

async def main():
    """Главная функция запуска бота"""
    logger.info("Инициализация базы данных...")
    await db.init_db()
    
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")

