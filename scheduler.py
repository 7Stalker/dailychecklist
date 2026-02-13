from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from database import reset_daily_habits, get_users_with_pending_habits
import logging

async def send_hourly_reminders(bot: Bot):
    """Bajarilmagan ishlari borlarni ogohlantirish"""
    try:
        user_ids = await get_users_with_pending_habits()
        for user_id in user_ids:
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text="🔔 <b>Eslatma:</b> Sizda bugun bajarilmagan odatlar qoldi. \nIltimos, tekshirib ko'ring! /start ni bosing."
                )
            except Exception as e:
                # Agar user botni bloklagan bo'lsa, xatoni o'tkazib yuboramiz
                logging.error(f"Foydalanuvchiga xabar yuborib bo'lmadi {user_id}: {e}")
    except Exception as e:
        logging.error(f"Scheduler xatosi: {e}")

async def daily_reset_job(bot: Bot):
    """Yarim tunda barcha ishlarni 'bajarilmadi' qilib yangilash"""
    await reset_daily_habits()
    # Ixtiyoriy: Reset bo'lgani haqida xabar berish mumkin, lekin shart emas.

def start_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler()
    
    # Har 1 soatda eslatma (soat 09:00 dan 23:00 gacha)
    scheduler.add_job(
        send_hourly_reminders, 
        'cron', 
        hour='9-23', 
        minute=0, 
        args=[bot]
    )
    
    # Har kuni 00:00 da odatlarni ❌ holatiga qaytarish
    scheduler.add_job(
        daily_reset_job,
        'cron',
        hour=0,
        minute=0,
        args=[bot]
    )
    
    scheduler.start()