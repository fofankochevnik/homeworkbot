from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from datetime import date, timedelta
from database import add_homework, get_homework, clear_homework, get_all_users, add_user

router = Router()
ADMIN_ID = 5081890387

class AddHomework(StatesGroup):
    task = State()

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📆 На завтра", callback_data="tomorrow")],
        [InlineKeyboardButton(text="➕ Добавить домашку", callback_data="add")]
    ])

def admin_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📆 На завтра", callback_data="tomorrow")],
        [InlineKeyboardButton(text="➕ Добавить домашку", callback_data="add")],
        [InlineKeyboardButton(text="🗑 Очистить домашку на завтра", callback_data="delete")]
    ])

def get_menu(user_id: int) -> InlineKeyboardMarkup:
    if user_id == ADMIN_ID:
        return admin_main_menu()
    return main_menu()

async def format_homework(date_str: str, label: str) -> str:
    task = await get_homework(date_str)
    if not task:
        return f"📭 Домашки на {label} нет!"
    return f"📚 Домашка на {label}:\n\n{task}"

@router.message(Command("start"))
async def cmd_start(message: Message):
    await add_user(message.from_user.id)
    await message.answer(
        "👋 Привет, 4Б!\n\nЯ бот для домашних заданий. Выбирай что хочешь:",
        reply_markup=get_menu(message.from_user.id),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back")
async def cb_back(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "Выбирай что хочешь:",
        reply_markup=get_menu(call.from_user.id)
    )

@router.callback_query(F.data == "tomorrow")
async def cb_tomorrow(call: CallbackQuery):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    text = await format_homework(tomorrow, "завтра")
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ]))

@router.callback_query(F.data == "add")
async def cb_add(call: CallbackQuery, state: FSMContext):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Только администратор может добавлять домашку!", show_alert=True)
        return
    await state.set_state(AddHomework.task)
    await call.message.edit_text(
        "📝 Напиши домашку на завтра одним сообщением.\n\nНапример:\nМатематика: стр. 45 №1,2,3\nРусский: упр. 34\nЧтение: стр. 67-70",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
        ])
    )

@router.message(AddHomework.task)
async def process_task(message: Message, state: FSMContext, bot=None):
    if message.from_user.id != ADMIN_ID:
        return
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    await add_homework(message.text, tomorrow)
    await state.clear()

    tomorrow_label = (date.today() + timedelta(days=1)).strftime("%d.%m")
    notification_text = f"✅ Домашка на завтра ({tomorrow_label}) добавлена!\n\n📚 {message.text}"

    await message.answer(
        f"✅ Домашка сохранена и отправлена всем!",
        reply_markup=get_menu(message.from_user.id)
    )

    users = await get_all_users()
    from aiogram import Bot
    import os
    bot_instance = Bot(token=os.getenv("BOT_TOKEN"))
    for (user_id,) in users:
        if user_id != ADMIN_ID:
            try:
                await bot_instance.send_message(user_id, notification_text)
            except Exception:
                pass
    await bot_instance.session.close()

@router.callback_query(F.data == "delete")
async def cb_delete(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Нет доступа!", show_alert=True)
        return
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    await clear_homework(tomorrow)
    await call.message.edit_text(
        "🗑 Домашка на завтра очищена!",
        reply_markup=get_menu(call.from_user.id)
    )
