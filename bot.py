import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router
from database import init_db, get_all_users
import os
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO)

ADMIN_ID = 5081890381
MSK = timezone(timedelta(hours=3))

async def daily_reminder(bot: Bot):
    while True:
        now = datetime.now(MSK)
        target = now.replace(hour=14, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        try:
            await bot.send_message(ADMIN_ID, "🔔 Не забудь добавить домашку на завтра!")
        except Exception as e:
            logging.error(f"Reminder error: {e}")

async def main():
    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await init_db()
    asyncio.create_task(daily_reminder(bot))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
