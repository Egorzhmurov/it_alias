import asyncio
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


# States
class GameStates(StatesGroup):
    waiting_for_new_word = State()


IT_WORDS = ["Атрибут", "Бекенд", "Конструктор", "Фреймворк", "Репозиторій", "Асинхронність"]
router = Router()
active_games = {}


# --- Keyboards ---

# Main menu (Reply)
def get_game_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Наступне слово")],
        [KeyboardButton(text="➕ Додати слово"), KeyboardButton(text="➖ Видалити слово")],
        [KeyboardButton(text="⏹ Зупинити гру")]
    ], resize_keyboard=True, is_persistent=True)


# Inline keyboard for deletion
def get_delete_word_keyboard():
    keyboard = [[InlineKeyboardButton(text=word, callback_data=f"del_{word}")] for word in IT_WORDS]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Inline button for show word alert
def get_show_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Подивитися слово", callback_data="show_alert")]
    ])


# --- Game Logic ---

async def start_new_round(message: Message, starter_name: str, starter_id: int):
    chat_id = message.chat.id
    if chat_id in active_games:
        try:
            active_games[chat_id]["task"].cancel()
        except:
            pass

    word = random.choice(IT_WORDS)

    async def run_timer():
        await asyncio.sleep(300)
        if active_games.get(chat_id) and active_games.get(chat_id, {}).get("word") == word:
            await message.answer(f"⏰ Час вийшов! Правильне слово: **{word.upper()}**", parse_mode="Markdown")
            if chat_id in active_games: del active_games[chat_id]

    task = asyncio.create_task(run_timer())
    active_games[chat_id] = {"word": word, "starter_name": starter_name, "starter_id": starter_id, "task": task}

    await message.answer(
        f"👤 Нове слово загадано! Ведучий: **{starter_name}**.",
        reply_markup=get_show_button(),
        parse_mode="Markdown"
    )


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Бот Alias готовий! Обери дію:", reply_markup=get_game_keyboard())


# --- Handlers ---

@router.callback_query(F.data == "show_alert")
async def show_alert(callback: CallbackQuery):
    data = active_games.get(callback.message.chat.id)
    if data and callback.from_user.id == data["starter_id"]:
        await callback.answer(f"Твоє слово: {data['word']}", show_alert=True)
    else:
        await callback.answer("❌ Це слово бачить лише ведучий!", show_alert=True)


@router.message(F.text == "➕ Додати слово")
async def cmd_new_word(message: Message, state: FSMContext):
    await message.answer("✍️ Введи нове слово для гри:")
    await state.set_state(GameStates.waiting_for_new_word)


@router.message(GameStates.waiting_for_new_word)
async def process_new_word(message: Message, state: FSMContext):
    IT_WORDS.append(message.text.strip())
    await message.answer(f"✅ Слово '{message.text.strip()}' додано!")
    await state.clear()


@router.message(F.text == "➖ Видалити слово")
async def cmd_del_word(message: Message):
    if not IT_WORDS:
        await message.answer("❌ Список слів порожній.")
        return
    await message.answer("🗑 Обери слово для видалення:", reply_markup=get_delete_word_keyboard())


@router.callback_query(F.data.startswith("del_"))
async def process_delete_callback(callback: CallbackQuery):
    word_to_del = callback.data.split("_", 1)[1]
    if word_to_del in IT_WORDS:
        IT_WORDS.remove(word_to_del)
        await callback.message.edit_text(f"✅ Слово '{word_to_del}' видалено.")
    else:
        await callback.answer("❌ Слово вже видалено.")
    await callback.answer()


@router.message(F.text == "⏹ Зупинити гру")
async def stop_game(message: Message):
    chat_id = message.chat.id
    if chat_id in active_games:
        active_games[chat_id]["task"].cancel()
        del active_games[chat_id]
        await message.answer("⏹ Гру зупинено.")
    else:
        await message.answer("❌ Активна гра відсутня.")


@router.message(F.text == "Наступне слово")
async def handle_next(message: Message):
    await start_new_round(message, starter_name=message.from_user.first_name, starter_id=message.from_user.id)


@router.message(F.text)
async def check(message: Message):
    if message.text in ["Наступне слово", "➕ Додати слово", "➖ Видалити слово", "⏹ Зупинити гру"]: return

    data = active_games.get(message.chat.id)
    if data:
        if message.text.strip().lower() == data["word"].strip().lower():
            if message.from_user.id == data["starter_id"]: return
            data["task"].cancel()
            try:
                await message.react(emoji="✅")
            except:
                pass
            await message.answer(f"✅ ПРАВИЛЬНО! {message.from_user.first_name} вгадав: {data['word'].upper()}!")
            del active_games[message.chat.id]
        elif message.from_user.id != data["starter_id"]:
            try:
                await message.react(emoji="❌")
            except:
                pass