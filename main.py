import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.game import router
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")


async def main():
    bot = Bot(token=TOKEN)
    # MemoryStorage дозволяє боту "пам'ятати" стан додавання слова
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    print("Бот запущено!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())