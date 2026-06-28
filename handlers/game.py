import random, asyncio, sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from words_list import IT_WORDS

router = Router()
active_game = {}


@router.message(Command("alias"))
async def cmd_alias(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Получить слово", callback_data="get_word")]])
    await message.answer("🎮 **Игра IT Alias началась!** Нажми кнопку для старта:", reply_markup=kb,
                         parse_mode="Markdown")


@router.callback_query(F.data == "get_word")
async def show_alert(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    if chat_id not in active_game: active_game[chat_id] = {"used_words": [], "word": None, "task": None}

    available = [w for w in IT_WORDS if w not in active_game[chat_id]["used_words"]]
    if not available:
        await callback.answer(text="⚠️ Список слов пуст! Сбрасываю...", show_alert=True)
        active_game[chat_id]["used_words"] = [];
        available = IT_WORDS

    word = random.choice(available)
    if active_game[chat_id].get("task"): active_game[chat_id]["task"].cancel()
    active_game[chat_id].update({"word": word.lower(), "used_words": active_game[chat_id]["used_words"] + [word]})

    await callback.answer(text=f"Твоё слово: {word.upper()}", show_alert=True)
    await callback.message.answer(f"👤 @{callback.from_user.username} загадал слово! ⏳ Есть 60 секунд!")
    active_game[chat_id]["task"] = asyncio.create_task(timer_task(callback.message, chat_id, word))


async def timer_task(message, chat_id, word):
    await asyncio.sleep(60)
    if chat_id in active_game and active_game[chat_id]["word"] == word.lower():
        await message.answer(f"⏰ **Время вышло!** Слово было: `{word.upper()}`", parse_mode="Markdown")
        active_game[chat_id]["word"] = None


@router.message(F.text)
async def check_answer(message: Message):
    chat_id = message.chat.id
    if chat_id not in active_game or active_game[chat_id]["word"] is None or message.text.startswith("/"): return

    if message.text.lower() == active_game[chat_id]["word"]:
        active_game[chat_id]["task"].cancel()
        await message.answer(
            f"✅ **Правильно!** @{message.from_user.username} угадал: `{active_game[chat_id]['word'].upper()}`!",
            parse_mode="Markdown")
        active_game[chat_id]["word"] = None