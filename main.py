import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
# O'zgartirish: Importni to'g'irladik
from aiogram.client.bot import DefaultBotProperties 
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database import create_tables
from handlers import router
from scheduler import start_scheduler

async def main():
    # Loglarni yoqish (Terminalda ma'lumot ko'rinishi uchun)
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    
    # Botni yaratish (ParseMode ni to'g'ri sozlash)
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    dp = Dispatcher()
    
    # Routerlarni ulash
    dp.include_router(router)
    
    # Bazani yaratish
    await create_tables()
    
    # Scheduler (vaqt bo'yicha ishlarni) ishga tushirish
    start_scheduler(bot)
    
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        if sys.platform == "win32":
            # Windowsda 'Event loop is closed' xatosini oldini olish uchun
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi")