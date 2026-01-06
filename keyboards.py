"""
Клавиатуры для Telegram бота
"""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config

def get_main_menu() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = [
        [KeyboardButton(text="🎁 Рассчитать дары")],
        [KeyboardButton(text="🎭 Полный профиль")],
        [KeyboardButton(text="📿 Сантры")],
        [KeyboardButton(text="🔮 Анализ слов")],
        [KeyboardButton(text="💎 Подписка"), KeyboardButton(text="❓ Помощь")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

def get_subscription_menu() -> InlineKeyboardMarkup:
    """Меню подписок"""
    keyboard = [
        [InlineKeyboardButton(text="⭐️ Оформить премиум", callback_data="show_premium_options")],
        [InlineKeyboardButton(text="ℹ️ О подписках", callback_data="subscription_info")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_premium_options_menu() -> InlineKeyboardMarkup:
    """Меню выбора тарифа премиум подписки"""
    keyboard = [
        [InlineKeyboardButton(
            text=f"🧪 ТЕСТ (1 день) - {Config.PREMIUM_TEST_PRICE} ⭐️",
            callback_data="buy_premium_test"
        )],
        [InlineKeyboardButton(
            text=f"📅 Месяц - {Config.PREMIUM_MONTH_PRICE} ⭐️",
            callback_data="buy_premium_month"
        )],
        [InlineKeyboardButton(
            text=f"📆 Год - {Config.PREMIUM_YEAR_PRICE} ⭐️",
            callback_data="buy_premium_year"
        )],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_subscription")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_calculation_type_menu() -> InlineKeyboardMarkup:
    """Меню выбора типа расчета"""
    keyboard = [
        [InlineKeyboardButton(text="🎁 Полный расчет (все дары)", callback_data="calc_all")],
        [InlineKeyboardButton(text="🔮 Только Ода", callback_data="calc_oda")],
        [InlineKeyboardButton(text="🌙 Только Туна", callback_data="calc_tuna")],
        [InlineKeyboardButton(text="✨ Только Триа", callback_data="calc_tria")],
        [InlineKeyboardButton(text="💎 Только Чиа", callback_data="calc_chia")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_mantras_menu() -> InlineKeyboardMarkup:
    """Меню работы с сантрами"""
    keyboard = [
        [InlineKeyboardButton(text="✨ Создать сантру (1 дар)", callback_data="mantra_create_1")],
        [InlineKeyboardButton(text="✨ Создать сантру (2 дара)", callback_data="mantra_create_2")],
        [InlineKeyboardButton(text="📝 Создать по запросу", callback_data="mantra_create_request")],
        [InlineKeyboardButton(text="🔍 Анализировать сантру", callback_data="mantra_analyze")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_mantra_create_options_menu() -> InlineKeyboardMarkup:
    """Меню опций создания сантры"""
    keyboard = [
        [InlineKeyboardButton(text="✅ С самовоспроизведением", callback_data="mantra_with_end")],
        [InlineKeyboardButton(text="❌ Без самовоспроизведения", callback_data="mantra_without_end")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_mantras")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_alphabet_menu() -> InlineKeyboardMarkup:
    """Меню анализа слов через алфавит"""
    keyboard = [
        [InlineKeyboardButton(text="✍️ Проанализировать слово", callback_data="alphabet_analyze")],
        [InlineKeyboardButton(text="« Назад", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

