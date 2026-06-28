# C:\it_alias\main.py
import sys, os, asyncio
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.loader import dp, bot
from handlers.game import router

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())