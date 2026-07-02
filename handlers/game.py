import asyncio
import random
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
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


# Keyboard for game control (Reply buttons)
def get_game_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="Наступне слово")],
        [KeyboardButton(text="➕ Додати слово"), KeyboardButton(text="➖ Видалити слово")],
        [KeyboardButton(text="⏹ Зупинити гру")]
    ], resize_keyboard=True, is_persistent=True)


async def start_new_round(message: Message, starter_name: str, starter_id: int):
    chat_id = message.chat.id
    if chat_id in active_games:
        try:
            active_games[chat_id]["task"].cancel()
        except:
            pass

    word = random.choice(IT_WORDS)

    # Timer logic
    async def run_timer():
        await asyncio.sleep(300)
        if active_games.get(chat_id) and active_games.get(chat_id, {}).get("word") == word:
            await message.answer(f"⏰ Час вийшов! Ніхто не вгадав.\nПравильне слово було: **{word.upper()}**",
                                 parse_mode="Markdown")
            if chat_id in active_games: del active_games[chat_id]

    task = asyncio.create_task(run_timer())
    active_games[chat_id] = {"word": word, "starter_name": starter_name, "starter_id": starter_id, "task": task}

    await message.answer(f"👤 Нове слово загадано! Ведучий: **{starter_name}**. ⌛️ 5 хв.", parse_mode="Markdown")


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Бот Alias готовий! Тисни кнопку.", reply_markup=get_game_keyboard())


# --- FSM Handlers ---

@router.message(F.text == "➕ Додати слово")
async def cmd_new_word(message: Message, state: FSMContext):
    await message.answer("✍️ Введи нове слово для гри:")
    await state.set_state(GameStates.waiting_for_new_word)


@router.message(GameStates.waiting_for_new_word)
async def process_new_word(message: Message, state: FSMContext):
    new_word = message.text.strip()
    IT_WORDS.append(new_word)
    await message.answer(f"✅ Слово '{new_word}' успішно додано!")
    await state.clear()


@router.message(F.text == "➖ Видалити слово")
async def cmd_del_word(message: Message, state: FSMContext):
    await message.answer("🗑 Введи слово, яке хочеш видалити:")
    await state.set_state(GameStates.waiting_for_delete_word)


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


@router.message(F.text == "⏹ Зупинити гру")
async def stop_game(message: Message):
    chat_id = message.chat.id
    if chat_id in active_games:
        active_games[chat_id]["task"].cancel()
        del active_games[chat_id]
        await message.answer("⏹ Гру зупинено.")
    else:
        await message.answer("❌ Активна гра відсутня.")


# --- Original Game Logic ---

@router.message(F.text == "Наступне слово")
async def handle_next(message: Message):
    await start_new_round(message, starter_name=message.from_user.first_name, starter_id=message.from_user.id)


@router.message(F.text)
async def check(message: Message):
    if message.text in ["Наступне слово", "➕ Додати слово", "➖ Видалити слово", "⏹ Зупинити гру"]: return

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