import asyncio
import os
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import create_client

BOT_TOKEN = os.environ['BOT_TOKEN']
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_SERVICE_KEY = os.environ['SUPABASE_SERVICE_KEY']
MINI_APP_URL = os.environ['MINI_APP_URL']

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def app_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🧸 Открыть Займи малыша",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]])


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! 👋\n\n"
        "«Займи малыша» — быстрые игры для детей из подручных вещей, без экранов.\n\n"
        "У тебя есть <b>3 дня бесплатного доступа</b>. Попробуй прямо сейчас! 👇",
        reply_markup=app_keyboard(),
        parse_mode="HTML"
    )


async def send_reminders():
    now = datetime.now(timezone.utc)

    # Напоминание на 2-й день: до конца триала 24–48 часов
    day2_from = (now + timedelta(hours=24)).isoformat()
    day2_to = (now + timedelta(hours=48)).isoformat()

    result = supabase.from_('users') \
        .select('telegram_id, first_name') \
        .is_('paid_at', 'null') \
        .eq('reminded_day2', False) \
        .gte('trial_expires_at', day2_from) \
        .lte('trial_expires_at', day2_to) \
        .execute()

    for user in result.data:
        try:
            await bot.send_message(
                user['telegram_id'],
                f"👋 {user['first_name']}, завтра заканчивается твой пробный период!\n\n"
                "Не теряй доступ к 200 играм — оформи доступ сегодня 👇",
                reply_markup=app_keyboard()
            )
            supabase.from_('users') \
                .update({'reminded_day2': True}) \
                .eq('telegram_id', user['telegram_id']) \
                .execute()
        except Exception as e:
            print(f"Day2 reminder failed for {user['telegram_id']}: {e}")

    # Напоминание на 3-й день: до конца триала < 24 часов
    day3_to = (now + timedelta(hours=24)).isoformat()

    result = supabase.from_('users') \
        .select('telegram_id, first_name') \
        .is_('paid_at', 'null') \
        .eq('reminded_day3', False) \
        .gte('trial_expires_at', now.isoformat()) \
        .lte('trial_expires_at', day3_to) \
        .execute()

    for user in result.data:
        try:
            await bot.send_message(
                user['telegram_id'],
                f"⏰ {user['first_name']}, сегодня последний день пробного периода!\n\n"
                "Открой приложение и оформи доступ за <b>490 ₽</b> — навсегда 👇",
                reply_markup=app_keyboard(),
                parse_mode="HTML"
            )
            supabase.from_('users') \
                .update({'reminded_day3': True}) \
                .eq('telegram_id', user['telegram_id']) \
                .execute()
        except Exception as e:
            print(f"Day3 reminder failed for {user['telegram_id']}: {e}")


async def main():
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(send_reminders, 'interval', hours=1)
    scheduler.start()
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
