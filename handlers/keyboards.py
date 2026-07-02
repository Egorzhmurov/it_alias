from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_game_keyboard():
    # Основна кнопка видачі
    btn_next = InlineKeyboardButton(text="🔑 Наступне слово", callback_data="get_word")

    # Кнопки адміністрування
    btn_add = InlineKeyboardButton(text="➕ Додати слово", callback_data="add_word")
    btn_del = InlineKeyboardButton(text="➖ Видалити слово", callback_data="delete_word")

    # Розміщуємо: видачу зверху, додавання та видалення в один ряд під нею
    return InlineKeyboardMarkup(inline_keyboard=[
        [btn_next],
        [btn_add, btn_del]
    ])