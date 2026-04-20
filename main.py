import asyncio
import os
import random
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, CallbackQuery
)
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


# ── Игры по возрасту ──────────────────────────────────────────────────────────
GAMES = {
    '1_2': [
        {
            'title': 'Сокровища в крупе',
            'desc': 'Спрячьте 5 мелких игрушек в миске с рисом. Ребёнок ищет руками. Развивает тактильное восприятие и мелкую моторику.',
            'time': 15,
            'items': 'миска, рис или гречка, мелкие игрушки',
        },
        {
            'title': 'Цветные комочки',
            'desc': 'Скомкайте листы цветной бумаги в шарики. Бросайте в таз — кто дальше? Развивает координацию и цветовосприятие.',
            'time': 10,
            'items': 'цветная бумага или салфетки, таз или коробка',
        },
    ],
    '3_4': [
        {
            'title': 'Цветной лёд',
            'desc': 'Заморозьте воду с пищевым красителем в формочках. Дайте ребёнку тёплую воду и кисточку — пусть «рисует» на льдинках. Развивает наблюдательность и понимание физических процессов.',
            'time': 20,
            'items': 'вода, пищевой краситель, формочки для льда, кисточка',
        },
        {
            'title': 'Строитель дорог',
            'desc': 'Сложите дорогу из книг, подушек и коробок. Прокатите машинки или шарики по маршруту. Ребёнок придумывает повороты и мосты. Развивает пространственное мышление.',
            'time': 25,
            'items': 'книги, подушки, коробки, машинки или мячики',
        },
    ],
    '5_6': [
        {
            'title': 'Карта квартиры',
            'desc': 'Попросите ребёнка нарисовать план квартиры сверху. Потом пройдитесь вместе и сравните с реальностью. Развивает пространственное мышление.',
            'time': 25,
            'items': 'бумага, карандаш',
        },
        {
            'title': 'Тайный агент',
            'desc': 'Напишите ребёнку задание на листочке: «найди 5 красных предметов» или «принеси что-то мягкое и круглое». Он выполняет и отчитывается. Развивает внимание и логику.',
            'time': 20,
            'items': 'бумага, ручка',
        },
    ],
    '7_8': [
        {
            'title': 'Магазин наоборот',
            'desc': 'Ребёнок — продавец, вы — покупатель. Он назначает цены на предметы в комнате, вы торгуетесь. Тренирует устный счёт и навыки общения.',
            'time': 20,
            'items': 'ничего не нужно',
        },
        {
            'title': 'Книга рецептов',
            'desc': 'Попросите ребёнка придумать и записать рецепт воображаемого блюда. Потом «приготовьте» его вместе из подручных предметов. Развивает творческое мышление.',
            'time': 30,
            'items': 'бумага, ручка',
        },
    ],
    '9_10': [
        {
            'title': 'Квест по квартире',
            'desc': 'Спрячьте небольшой «приз» и разложите по квартире 5 записок-подсказок. Каждая ведёт к следующей. Развивает логику и навык чтения.',
            'time': 30,
            'items': 'бумага, ручка, небольшой приз (конфета, наклейка)',
        },
        {
            'title': 'Интервью с родителем',
            'desc': 'Ребёнок берёт интервью у вас: как жили без интернета, во что играли, что ели. Записывает в «газету» или диктует на телефон. Развивает коммуникацию.',
            'time': 25,
            'items': 'бумага, ручка',
        },
    ],
    '11_12': [
        {
            'title': 'Дебаты',
            'desc': 'Выберите тему: «Домашние животные: за и против». Ребёнок защищает одну сторону, вы — другую. 5 минут подготовки, 10 минут дебатов. Развивает аргументацию и критическое мышление.',
            'time': 20,
            'items': 'ничего не нужно',
        },
        {
            'title': 'Мини-бизнес',
            'desc': 'Попросите ребёнка придумать бизнес-идею: что продавать, кому, по какой цене. Он делает мини-презентацию и «питчит» вам. Развивает предпринимательское мышление.',
            'time': 30,
            'items': 'бумага, ручка',
        },
    ],
}

AGE_LABELS = {
    '1_2': '1-2 года', '3_4': '3-4 года', '5_6': '5-6 лет',
    '7_8': '7-8 лет', '9_10': '9-10 лет', '11_12': '11-12 лет',
}

AGE_TO_KEY = {
    1: '1_2', 2: '1_2', 3: '3_4', 4: '3_4',
    5: '5_6', 6: '5_6', 7: '7_8', 8: '7_8',
    9: '9_10', 10: '9_10', 11: '11_12', 12: '11_12',
}

AGE_KEY_TO_INT = {
    '1_2': 1, '3_4': 3, '5_6': 5,
    '7_8': 7, '9_10': 9, '11_12': 11,
}


def get_game(age_int: int, exclude_title: str = None) -> dict:
    key = AGE_TO_KEY.get(age_int, '3_4')
    games = GAMES.get(key, GAMES['3_4'])
    available = [g for g in games if g['title'] != exclude_title]
    return random.choice(available if available else games)


# ── Клавиатуры ────────────────────────────────────────────────────────────────
def age_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👶 1-2 года", callback_data="age_1_2"),
            InlineKeyboardButton(text="🧒 3-4 года", callback_data="age_3_4"),
        ],
        [
            InlineKeyboardButton(text="🧒 5-6 лет", callback_data="age_5_6"),
            InlineKeyboardButton(text="👦 7-8 лет", callback_data="age_7_8"),
        ],
        [
            InlineKeyboardButton(text="👦 9-10 лет", callback_data="age_9_10"),
            InlineKeyboardButton(text="🧑 11-12 лет", callback_data="age_11_12"),
        ],
    ])


def app_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🧸 Открыть «Займи малыша»",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )
    ]])


def welcome_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🧸 Открыть приложение (3 дня бесплатно)",
            web_app=WebAppInfo(url=MINI_APP_URL)
        )],
        [InlineKeyboardButton(text="🎓 Войти в клуб бесплатно", url=CLUB_URL)],
    ])


def feedback_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Да, понравилось!", callback_data="feedback_positive"),
        InlineKeyboardButton(text="⏳ Пока не пробовали", callback_data="feedback_negative"),
    ]])


# ── /start ────────────────────────────────────────────────────────────────────
@dp.message(CommandStart())
async def cmd_start(message: types.Message, command: CommandObject):
    args = command.args or "direct"
    tg_id = message.from_user.id
    now_iso = datetime.now(timezone.utc).isoformat()

    result = supabase.from_('users').select('telegram_id, child_age').eq('telegram_id', tg_id).execute()

    if result.data:
        user = result.data[0]
        if user.get('child_age'):
            # Возвращающийся пользователь — возраст уже известен
            await message.answer(
                "С возвращением! 👋\n\nОткрой приложение — подберём игру для сегодня 👇",
                reply_markup=app_keyboard()
            )
            return
        # Есть в базе (зашёл через приложение), но возраст не указан
        supabase.from_('users').update({
            'source': args,
            'funnel_started_at': now_iso,
            'first_name': message.from_user.first_name or '',
            'username': message.from_user.username or '',
        }).eq('telegram_id', tg_id).execute()
    else:
        # Новый пользователь
        supabase.from_('users').insert({
            'telegram_id': tg_id,
            'first_name': message.from_user.first_name or '',
            'last_name': message.from_user.last_name or '',
            'username': message.from_user.username or '',
            'source': args,
            'funnel_started_at': now_iso,
        }).execute()

    await message.answer(
        "Привет! 👋\n\n"
        "Я помогу занять ребёнка за 5 минут — без экранов и дорогих игрушек.\n\n"
        "Сколько лет твоему ребёнку?",
        reply_markup=age_keyboard()
    )


# ── Выбор возраста ────────────────────────────────────────────────────────────
@dp.callback_query(F.data.startswith('age_'))
async def handle_age(callback: CallbackQuery):
    age_key = callback.data[4:]  # убираем 'age_'
    tg_id = callback.from_user.id
    age_label = AGE_LABELS.get(age_key, '3-4 года')
    child_age = AGE_KEY_TO_INT.get(age_key, 3)

    supabase.from_('users').update({
        'child_age': child_age,
    }).eq('telegram_id', tg_id).execute()

    await callback.message.edit_text(
        f"Отлично! Для ребёнка {age_label} у нас 200+ игр 🎯\n\n"
        f"Вот твой бесплатный доступ на 3 дня — выбери что есть дома "
        f"и получи готовую игру за 5 секунд 👇",
        reply_markup=welcome_keyboard()
    )
    await callback.answer()


# ── Обратная связь День 2 ─────────────────────────────────────────────────────
@dp.callback_query(F.data == 'feedback_positive')
async def feedback_positive(callback: CallbackQuery):
    supabase.from_('users').update(
        {'day2_response': 'positive'}
    ).eq('telegram_id', callback.from_user.id).execute()

    await callback.message.edit_text(
        "Здорово! 🎉\n\n"
        "В приложении ещё 200+ таких игр — каждая подобрана под то, что есть дома. "
        "Укажи что под рукой, получи список за 5 секунд 👇",
        reply_markup=app_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data == 'feedback_negative')
async def feedback_negative(callback: CallbackQuery):
    tg_id = callback.from_user.id
    supabase.from_('users').update(
        {'day2_response': 'negative'}
    ).eq('telegram_id', tg_id).execute()

    result = supabase.from_('users').select('trial_expires_at').eq('telegram_id', tg_id).execute()
    days_left = 2
    if result.data and result.data[0].get('trial_expires_at'):
        exp = result.data[0]['trial_expires_at']
        expires = datetime.fromisoformat(exp.replace('Z', '+00:00'))
        delta = expires - datetime.now(timezone.utc)
        days_left = max(1, delta.days)

    await callback.message.edit_text(
        f"Ничего страшного — сохрани, пригодится когда будет момент! 🙌\n\n"
        f"Доступ к приложению активен ещё {days_left} дн. "
        f"Там игру можно подобрать за 10 секунд 👇",
        reply_markup=app_keyboard()
    )
    await callback.answer()


# ── /stats (только для админа) ────────────────────────────────────────────────
@dp.message(Command('stats'))
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    now = datetime.now(timezone.utc)
    week_ago = (now - timedelta(days=7)).isoformat()

    total_r = supabase.from_('users').select('*', count='exact').execute()
    paid_r = supabase.from_('users').select('*', count='exact').not_.is_('paid_at', 'null').execute()
    trial_r = supabase.from_('users').select('*', count='exact').is_('paid_at', 'null').gte('trial_expires_at', now.isoformat()).execute()
    new_r = supabase.from_('users').select('*', count='exact').gte('created_at', week_ago).execute()
    funnel_r = supabase.from_('users').select('*', count='exact').not_.is_('funnel_started_at', 'null').execute()

    total = total_r.count or 0
    paid = paid_r.count or 0
    trial = trial_r.count or 0
    new_week = new_r.count or 0
    in_funnel = funnel_r.count or 0
    conv = f"{paid / total * 100:.1f}%" if total else "0%"
    revenue = paid * 490

    await message.answer(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{total}</b>\n"
        f"🆕 Новых за 7 дней: <b>{new_week}</b>\n"
        f"🤖 Прошли бот-воронку: <b>{in_funnel}</b>\n"
        f"⏳ На активном триале: <b>{trial}</b>\n"
        f"💳 Купили доступ: <b>{paid}</b>\n"
        f"💰 Выручка: <b>{revenue} ₽</b>\n"
        f"📈 Конверсия: <b>{conv}</b>",
        parse_mode="HTML"
    )


# ── /broadcast (только для админа) ───────────────────────────────────────────
@dp.message(Command('broadcast'))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    text = message.text.removeprefix('/broadcast').strip()
    if not text:
        await message.answer('Укажи текст:\n/broadcast Ваш текст')
        return

    result = supabase.from_('users').select('telegram_id').execute()
    total = len(result.data)
    sent = failed = 0
    await message.answer(f'Начинаю рассылку для {total} пользователей...')

    for user in result.data:
        try:
            await bot.send_message(user['telegram_id'], text, parse_mode='HTML')
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)

    await message.answer(f'✅ Готово\nОтправлено: {sent}\nОшибок: {failed}')


# ── Обратная связь (текстовые сообщения) ─────────────────────────────────────
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
    await message.answer("Спасибо за отзыв! 🙏 Мы обязательно прочитаем.")


# ── Воронка + напоминания о триале (каждый час) ───────────────────────────────
async def send_scheduled_messages():
    now = datetime.now(timezone.utc)

    # ── День 1: через 24ч после старта воронки ────────────────────────────────
    to_dt = (now - timedelta(hours=24)).isoformat()
    r = supabase.from_('users').select('telegram_id, first_name, child_age') \
        .not_.is_('funnel_started_at', 'null') \
        .is_('paid_at', 'null') \
        .eq('day1_sent', False) \
        .lte('funnel_started_at', to_dt) \
        .execute()

    for u in r.data:
        if not u.get('child_age'):
            continue
        game = get_game(u['child_age'])
        age_label = AGE_LABELS.get(AGE_TO_KEY.get(u['child_age'], '3_4'), '')
        try:
            await bot.send_message(
                u['telegram_id'],
                f"Доброе утро! ☀️\n\n"
                f"Игра для ребёнка {age_label} на сегодня:\n\n"
                f"🎮 <b>«{game['title']}»</b>\n\n"
                f"{game['desc']}\n\n"
                f"⏱ Займёт: {game['time']} минут\n"
                f"📦 Что нужно: {game['items']}\n\n"
                f"Попробуйте сегодня — и загляните в приложение, "
                f"там ещё 200+ таких идей 👇",
                reply_markup=app_keyboard(),
                parse_mode="HTML"
            )
            supabase.from_('users').update({'day1_sent': True}).eq('telegram_id', u['telegram_id']).execute()
        except Exception as e:
            print(f"[Day1] failed {u['telegram_id']}: {e}")

    # ── День 2: через 48ч — вопрос с кнопками ─────────────────────────────────
    to_dt = (now - timedelta(hours=48)).isoformat()
    r = supabase.from_('users').select('telegram_id') \
        .not_.is_('funnel_started_at', 'null') \
        .is_('paid_at', 'null') \
        .eq('day1_sent', True) \
        .eq('day2_sent', False) \
        .lte('funnel_started_at', to_dt) \
        .execute()

    for u in r.data:
        try:
            await bot.send_message(
                u['telegram_id'],
                "Как прошло вчера? Попробовали игру с ребёнком? 🤗",
                reply_markup=feedback_keyboard()
            )
            supabase.from_('users').update({'day2_sent': True}).eq('telegram_id', u['telegram_id']).execute()
        except Exception as e:
            print(f"[Day2] failed {u['telegram_id']}: {e}")

    # ── День 3: через 72ч — оффер покупки ─────────────────────────────────────
    to_dt = (now - timedelta(hours=72)).isoformat()
    r = supabase.from_('users').select('telegram_id, first_name') \
        .not_.is_('funnel_started_at', 'null') \
        .is_('paid_at', 'null') \
        .eq('day2_sent', True) \
        .eq('day3_sent', False) \
        .lte('funnel_started_at', to_dt) \
        .execute()

    for u in r.data:
        name = u.get('first_name') or ''
        greeting = f"{name}, " if name else ""
        try:
            await bot.send_message(
                u['telegram_id'],
                f"⏰ {greeting}бесплатный период «Займи малыша» заканчивается!\n\n"
                f"За эти 3 дня ты мог убедиться: игру можно подобрать за 5 секунд — "
                f"без покупки ничего лишнего.\n\n"
                f"<b>Полный доступ — 490 ₽ навсегда</b> (не подписка, разовый платёж).\n\n"
                f"Это 16 ₽ в день — меньше, чем стаканчик кофе, "
                f"но зато тишина и занятый ребёнок ☕️",
                reply_markup=app_keyboard(),
                parse_mode="HTML"
            )
            supabase.from_('users').update({'day3_sent': True}).eq('telegram_id', u['telegram_id']).execute()
        except Exception as e:
            print(f"[Day3] failed {u['telegram_id']}: {e}")

    # ── День 7: через 168ч — социальное доказательство + скидка ──────────────
    to_dt = (now - timedelta(hours=168)).isoformat()
    r = supabase.from_('users').select('telegram_id, first_name') \
        .not_.is_('funnel_started_at', 'null') \
        .is_('paid_at', 'null') \
        .eq('day3_sent', True) \
        .eq('day7_sent', False) \
        .lte('funnel_started_at', to_dt) \
        .execute()

    for u in r.data:
        name = u.get('first_name') or ''
        greeting = f"{name}, з" if name else "З"
        try:
            await bot.send_message(
                u['telegram_id'],
                f"{greeting}наешь что чаще всего пишут родители?\n\n"
                f"💬 «Я теперь спокойно готовлю ужин — ребёнок занят, "
                f"а я не чувствую вину за мультики»\n"
                f"— Марина, мама двойняшек 4 года\n\n"
                f"💬 «Сын сам просит "давай поиграем в то, что в телефоне". "
                f"Играем без телефона» 😄\n"
                f"— Алексей, папа 6-летнего Артёма\n\n"
                f"Приложением пользуются <b>160+ родителей</b>.\n\n"
                f"Специально для тебя — <b>доступ за 290 ₽</b> вместо 490 ₽.\n"
                f"Предложение действует 48 часов 👇",
                reply_markup=app_keyboard(),
                parse_mode="HTML"
            )
            supabase.from_('users').update({'day7_sent': True}).eq('telegram_id', u['telegram_id']).execute()
        except Exception as e:
            print(f"[Day7] failed {u['telegram_id']}: {e}")

    # ── Напоминания о триале (для пользователей зашедших напрямую через приложение) ──

    # За 1-2 дня до конца триала
    day2_from = (now + timedelta(hours=24)).isoformat()
    day2_to = (now + timedelta(hours=48)).isoformat()
    r = supabase.from_('users').select('telegram_id, first_name') \
        .is_('paid_at', 'null') \
        .eq('reminded_day2', False) \
        .gte('trial_expires_at', day2_from) \
        .lte('trial_expires_at', day2_to) \
        .execute()

    for u in r.data:
        name = u.get('first_name') or ''
        greeting = f"{name}, " if name else ""
        try:
            await bot.send_message(
                u['telegram_id'],
                f"👋 {greeting}завтра заканчивается пробный период!\n\n"
                "Не теряй доступ к 200 играм — оформи доступ сегодня 👇",
                reply_markup=app_keyboard()
            )
            supabase.from_('users').update({'reminded_day2': True}).eq('telegram_id', u['telegram_id']).execute()
        except Exception as e:
            print(f"[Reminder2] failed {u['telegram_id']}: {e}")

    # В последний день триала
    r = supabase.from_('users').select('telegram_id, first_name') \
        .is_('paid_at', 'null') \
        .eq('reminded_day3', False) \
        .gte('trial_expires_at', now.isoformat()) \
        .lte('trial_expires_at', (now + timedelta(hours=24)).isoformat()) \
        .execute()

    for u in r.data:
        name = u.get('first_name') or ''
        greeting = f"{name}, " if name else ""
        try:
            await bot.send_message(
                u['telegram_id'],
                f"⏰ {greeting}сегодня последний день пробного периода!\n\n"
                "Оформи доступ за <b>490 ₽</b> — навсегда 👇",
                reply_markup=app_keyboard(),
                parse_mode="HTML"
            )
            supabase.from_('users').update({'reminded_day3': True}).eq('telegram_id', u['telegram_id']).execute()
        except Exception as e:
            print(f"[Reminder3] failed {u['telegram_id']}: {e}")


async def main():
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(send_scheduled_messages, 'interval', hours=1)
    scheduler.start()
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
