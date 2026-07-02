import asyncio
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


# Стан для команди /newword
class GameStates(StatesGroup):
    waiting_for_new_word = State()


IT_WORDS = ["Атрибут", "Бекенд", "Конструктор", "Фреймворк", "Репозиторій", "Асинхронність"]
router = Router()
active_games = {}


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
            await message.answer(f"⏰ Час вийшов! Ніхто не вгадав.\nПравильне слово було: **{word.upper()}**",
                                 parse_mode="Markdown")
            await start_new_round(message, starter_name="Система", starter_id=0)

    task = asyncio.create_task(run_timer())
    active_games[chat_id] = {"word": word, "starter_name": starter_name, "starter_id": starter_id, "task": task}

    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="👁 Подивитися", callback_data="show")]])
    await message.answer(f"👤 Нове слово загадано! Ведучий: **{starter_name}**. ⌛️ 5 хв.", reply_markup=kb,
                         parse_mode="Markdown")


@router.message(Command("start"))
async def cmd_start(message: Message):
    kb = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Наступне слово")]], resize_keyboard=True,
                             is_persistent=True)
    await message.answer("Бот Alias готовий! Тисни кнопку.", reply_markup=kb)


# Команда для додавання нового слова
@router.message(Command("newword"))
async def cmd_new_word(message: Message, state: FSMContext):
    await message.answer("✍️ Введи нове слово для гри:")
    await state.set_state(GameStates.waiting_for_new_word)


@router.message(GameStates.waiting_for_new_word)
async def process_new_word(message: Message, state: FSMContext):
    new_word = message.text.strip()
    IT_WORDS.append(new_word)
    await message.answer(f"✅ Слово '{new_word}' успішно додано до словника!")
    await state.clear()


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
        # Логіка вгадування
        if message.text.strip().lower() == data["word"].strip().lower():
            if message.from_user.id == data["starter_id"]: return

            data["task"].cancel()
            try:
                await message.react(emoji="✅")
            except:
                pass

            await message.answer(f"✅ ПРАВИЛЬНО! {message.from_user.first_name} вгадав: {data['word'].upper()}!")

        elif message.from_user.id != data["starter_id"]:
            try:
                await message.react(emoji="❌")
            except:
                pass