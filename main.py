import asyncio
import os
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from supabase import create_client

BOT_TOKEN = os.environ['BOT_TOKEN']
SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_SERVICE_KEY = os.environ['SUPABASE_SERVICE_KEY']
MINI_APP_URL = os.environ['MINI_APP_URL']
CLUB_URL = os.environ['CLUB_URL']
ADMIN_ID = int(os.environ['ADMIN_ID'])

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def start_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎓 Войти в клуб бесплатно",
                url=CLUB_URL
            )
        ],
        [
            InlineKeyboardButton(
                text="🧸 Попробовать приложение 3 дня бесплатно",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ]
    ])


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
        "Я помогу тебе занять ребёнка за 5 минут — без экранов и дорогих игрушек.\n\n"
        "Что тебя ждёт:\n"
        "🎓 <b>Клуб «Развитие для детей»</b> — 800+ шаблонов для печати, планы занятий, идеи игр и поделок. Бесплатно навсегда.\n\n"
        "🧸 <b>Приложение «Займи малыша»</b> — выбираешь возраст ребёнка и что есть дома, получаешь готовую игру за 5 секунд. 3 дня бесплатно.\n\n"
        "Выбирай 👇",
        reply_markup=start_keyboard(),
        parse_mode="HTML"
    )


# ── Рассылка (только для админа) ──────────────────────────────────────────────
@dp.message(Command('broadcast'))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.removeprefix('/broadcast').strip()
    if not text:
        await message.answer('Укажи текст сообщения:\n/broadcast Ваш текст')
        return

    result = supabase.from_('users').select('telegram_id').execute()
    total = len(result.data)
    sent = 0
    failed = 0

    await message.answer(f'Начинаю рассылку для {total} пользователей...')

    for user in result.data:
        try:
            await bot.send_message(user['telegram_id'], text, parse_mode='HTML')
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)  # защита от флуд-лимита

    await message.answer(f'✅ Рассылка завершена\nОтправлено: {sent}\nОшибок: {failed}')


# ── Обратная связь ─────────────────────────────────────────────────────────────
@dp.message(F.text & ~F.text.startswith('/'))
async def handle_feedback(message: types.Message):
    username = f"@{message.from_user.username}" if message.from_user.username else "без username"
    name = message.from_user.first_name or ""

    await bot.send_message(
        ADMIN_ID,
        f"💬 <b>Отзыв от {name} ({username})</b>\n"
        f"ID: <code>{message.from_user.id}</code>\n\n"
        f"{message.text}",
        parse_mode="HTML"
    )
    await message.answer("Спасибо за отзыв! 🙏\nМы обязательно прочитаем.")


# ── Напоминания о триале ───────────────────────────────────────────────────────
async def send_reminders():
    now = datetime.now(timezone.utc)

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
