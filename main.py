import asyncio
import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

# Importing modules from your handlers and utils packages
from handlers import setup_handlers
from utils.word_loader import fetch_words


async def main():
    # Load environment variables (TOKEN) from .env file
    load_dotenv()

    # Initialize the bot and dispatcher
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher()

    # Prepare data (fetch IT terms from the web)
    fetch_words()

    # Register all command handlers
    setup_handlers(dp)

    print("--- Bot successfully started ---")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())