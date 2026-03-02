from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from datetime import date, timedelta
from database import add_homework, get_homework, delete_homework

router = Router()
ADMIN_ID = 5081890387

SUBJECTS = [
    "Математика", "Русский язык", "Чтение", "Окружающий мир",
    "Английский язык", "Музыка", "ИЗО", "Физкультура", "Технология"
]

class AddHomework(StatesGroup):
    subject = State()
    task = State()
    date_choice = State()

def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def main_menu(user_id: int) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="📅 На сегодня", callback_data="today"),
         InlineKeyboardButton(text="📆 На завтра", callback_data="tomorrow")]
    ]
    if is_admin(user_id):
        buttons.append([InlineKeyboardButton(text="➕ Добавить домашку", callback_data="add")])
        buttons.append([InlineKeyboardButton(text="🗑 Удалить домашку", callback_data="delete")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def subjects_keyboard(action: str) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, subject in enumerate(SUBJECTS):
        row.append(InlineKeyboardButton(text=subject, callback_data=f"{action}:{subject}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def date_keyboard() -> InlineKeyboardMarkup:
    today = date.today()
    buttons = []
    for i in range(1, 8):
        d = today + timedelta(days=i)
        weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        label = f"{weekdays[d.weekday()]} {d.strftime('%d.%m')}"
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"date:{d.isoformat()}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def format_homework(date_str: str, label: str) -> str:
    rows = await get_homework(date_str)
    if not rows:
        return f"📭 Домашки на {label} нет!"
    text = f"📚 Домашка на {label}:\n\n"
    for subject, task in rows:
        text += f"📌 <b>{subject}</b>\n{task}\n\n"
    return text.strip()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет, 4Б!\n\nЯ бот для домашних заданий. Выбирай что хочешь:",
        reply_markup=main_menu(message.from_user.id),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "back")
async def cb_back(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "Выбирай что хочешь:",
        reply_markup=main_menu(call.from_user.id)
    )

@router.callback_query(F.data == "today")
async def cb_today(call: CallbackQuery):
    today = date.today().isoformat()
    text = await format_homework(today, "сегодня")
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ]))

@router.callback_query(F.data == "tomorrow")
async def cb_tomorrow(call: CallbackQuery):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    text = await format_homework(tomorrow, "завтра")
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back")]
    ]))

@router.callback_query(F.data == "add")
async def cb_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Только администратор может добавлять домашку!", show_alert=True)
        return
    await state.set_state(AddHomework.subject)
    await call.message.edit_text("Выбери предмет:", reply_markup=subjects_keyboard("addsubj"))

@router.callback_query(F.data.startswith("addsubj:"))
async def cb_add_subject(call: CallbackQuery, state: FSMContext):
    subject = call.data.split(":")[1]
    await state.update_data(subject=subject)
    await state.set_state(AddHomework.date_choice)
    await call.message.edit_text(f"📌 Предмет: <b>{subject}</b>\n\nНа какое число задание?",
                                  reply_markup=date_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("date:"))
async def cb_add_date(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа!", show_alert=True)
        return
    chosen_date = call.data.split(":")[1]
    await state.update_data(date=chosen_date)
    await state.set_state(AddHomework.task)
    data = await state.get_data()
    await call.message.edit_text(
        f"📌 Предмет: <b>{data['subject']}</b>\n📅 Дата: <b>{chosen_date}</b>\n\nНапиши задание текстом:",
        parse_mode="HTML"
    )

@router.message(AddHomework.task)
async def process_task(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    data = await state.get_data()
    await add_homework(data["subject"], message.text, data["date"])
    await state.clear()
    await message.answer(
        f"✅ Добавлено!\n\n📌 <b>{data['subject']}</b>\n📅 {data['date']}\n📝 {message.text}",
        parse_mode="HTML",
        reply_markup=main_menu(message.from_user.id)
    )

@router.callback_query(F.data == "delete")
async def cb_delete(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("❌ Нет доступа!", show_alert=True)
        return
    await call.message.edit_text("Выбери предмет для удаления:", reply_markup=subjects_keyboard("delsubj"))

@router.callback_query(F.data.startswith("delsubj:"))
async def cb_delete_subject(call: CallbackQuery, state: FSMContext):
    subject = call.data.split(":")[1]
    await state.update_data(subject=subject)
    await call.message.edit_text(f"📌 Предмет: <b>{subject}</b>\n\nНа какую дату удалить?",
                                  reply_markup=date_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("deldate:"))
async def cb_delete_date(call: CallbackQuery, state: FSMContext):
    chosen_date = call.data.split(":")[1]
    data = await state.get_data()
    await delete_homework(data["subject"], chosen_date)
    await state.clear()
    await call.message.edit_text(
        f"🗑 Удалено!\n\n📌 <b>{data['subject']}</b> на {chosen_date}",
        parse_mode="HTML",
        reply_markup=main_menu(call.from_user.id)
    )
