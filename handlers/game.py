import asyncio
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# States for FSM
class GameStates(StatesGroup):
    waiting_for_new_word = State()
    waiting_for_delete_word = State()

IT_WORDS = ["Атрибут", "Бекенд", "Конструктор", "Фреймворк", "Репозиторій", "Асинхронність"]
router = Router()
active_games = {}

# Keyboard for game control
def get_game_keyboard():
    # Adding control buttons below the word display
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Додати слово", callback_data="add_word"),
         InlineKeyboardButton(text="➖ Видалити слово", callback_data="del_word")],
        [InlineKeyboardButton(text="⏹ Зупинити гру", callback_data="stop_game")]
    ])

async def start_new_round(message: Message, starter_name: str, starter_id: int):
    chat_id = message.chat.id
    if chat_id in active_games:
        try:
            active_games[chat_id]["task"].cancel()
        except:
            pass

    word = random.choice(IT_WORDS)

    # Timer logic - now stops the game and doesn't auto-restart
    async def run_timer():
        await asyncio.sleep(300)
        if active_games.get(chat_id) and active_games.get(chat_id, {}).get("word") == word:
            await message.answer(f"⏰ Час вийшов! Ніхто не вгадав.\nПравильне слово було: **{word.upper()}**", parse_mode="Markdown")
            if chat_id in active_games:
                del active_games[chat_id]

    task = asyncio.create_task(run_timer())
    active_games[chat_id] = {"word": word, "starter_name": starter_name, "starter_id": starter_id, "task": task}

    # Combined keyboard: View word + control buttons
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁 Подивитися", callback_data="show")],
        [InlineKeyboardButton(text="➕ Додати", callback_data="add_word"),
         InlineKeyboardButton(text="➖ Видалити", callback_data="del_word")],
        [InlineKeyboardButton(text="⏹ Зупинити", callback_data="stop_game")]
    ])
    await message.answer(f"👤 Нове слово загадано! Ведучий: **{starter_name}**. ⌛️ 5 хв.", reply_markup=kb, parse_mode="Markdown")


@router.message(Command("start"))
async def cmd_start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Наступне слово")]], resize_keyboard=True, is_persistent=True)
    await message.answer("Бот Alias готовий! Тисни кнопку.", reply_markup=kb)


# --- Handlers for new buttons ---

@router.callback_query(F.data == "add_word")
async def cmd_new_word(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ Введи нове слово для гри:")
    await state.set_state(GameStates.waiting_for_new_word)
    await callback.answer()

@router.message(GameStates.waiting_for_new_word)
async def process_new_word(message: Message, state: FSMContext):
    new_word = message.text.strip()
    IT_WORDS.append(new_word)
    await message.answer(f"✅ Слово '{new_word}' успішно додано до словника!")
    await state.clear()

@router.callback_query(F.data == "del_word")
async def cmd_del_word(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🗑 Введи слово, яке хочеш видалити:")
    await state.set_state(GameStates.waiting_for_delete_word)
    await callback.answer()

@router.message(GameStates.waiting_for_delete_word)
async def process_delete_word(message: Message, state: FSMContext):
    word_to_del = message.text.strip().lower()
    found = False
    for word in IT_WORDS:
        if word.lower() == word_to_del:
            IT_WORDS.remove(word)
            await message.answer(f"🗑 Слово '{word}' видалено.")
            found = True
            break
    if not found:
        await message.answer("❌ Такого слова немає у списку.")
    await state.clear()

@router.callback_query(F.data == "stop_game")
@router.message(Command("stop"))
async def stop_game(message: Message | CallbackQuery):
    chat = message.message.chat if isinstance(message, CallbackQuery) else message.chat
    if chat.id in active_games:
        active_games[chat.id]["task"].cancel()
        del active_games[chat.id]
        await (message.message if isinstance(message, CallbackQuery) else message).answer("⏹ Гру зупинено.")
    else:
        await (message.message if isinstance(message, CallbackQuery) else message).answer("❌ Активна гра відсутня.")
    if isinstance(message, CallbackQuery): await message.answer()


# --- Original Game Logic ---

@router.message(F.text == "Наступне слово")
async def handle_next(message: Message):
    await start_new_round(message, starter_name=message.from_user.first_name, starter_id=message.from_user.id)


@router.callback_query(F.data == "show")
async def show_word(callback: CallbackQuery):
    data = active_games.get(callback.message.chat.id)
    if data and callback.from_user.id == data["starter_id"]:
        await callback.answer(f"Твоє слово: {data['word']}", show_alert=True)
    else:
        await callback.answer("❌ Це слово бачить лише ведучий!", show_alert=True)


@router.message(F.text)
async def check(message: Message):
    if message.text == "Наступне слово": return
    data = active_games.get(message.chat.id)
    if data:
        # Check guess (case-insensitive)
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