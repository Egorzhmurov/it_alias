from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_game_keyboard():
    btn_next = InlineKeyboardButton(text="Наступне слово", callback_data="next_word")
    btn_skip = InlineKeyboardButton(text="Пропустити", callback_data="skip_word")
    return InlineKeyboardMarkup(inline_keyboard=[[btn_next, btn_skip]])