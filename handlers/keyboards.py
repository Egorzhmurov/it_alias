from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_game_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Наступне слово"), KeyboardButton(text="Пропустити")]
        ],
        resize_keyboard=True
    )