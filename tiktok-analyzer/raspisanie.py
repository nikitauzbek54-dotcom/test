import asyncio
import json
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.client.default import DefaultBotProperties

# ============ НАСТРОЙКИ ============
BOT_TOKEN = "8713334159:AAGRlKlBhN7r6L4AsO9uWvd41lmEGwsSPAM"
ADMIN_ID = 8976601589

# ============ ПАПКА ДЛЯ ДАННЫХ ============
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
STORAGE_FILE = DATA_DIR / "storage.json"

# ============ ХРАНИЛИЩЕ ============
def load_storage():
    if STORAGE_FILE.exists():
        try:
            return json.loads(STORAGE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "users": [],
        "banner": None,
        "schedule": {},
        "homework": {},
        "sticker": None,
    }

def save_storage(data):
    STORAGE_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

storage = load_storage()

# ============ БОТ ============
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

admin_state = {}

DAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб"]

# ============ КЛАВИАТУРЫ ============
def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Расписание", callback_data="menu_schedule")],
        [InlineKeyboardButton(text="📚 Домашка", callback_data="menu_homework")],
        [InlineKeyboardButton(text="🤡 Матвей пидор", callback_data="menu_matvey")],
    ])

def schedule_menu():
    rows = [[InlineKeyboardButton(text=f"📅 {d}", callback_data=f"show_schedule_{d}")] for d in DAYS]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def homework_menu():
    subjects = list(storage["homework"].keys())
    if not subjects:
        rows = [[InlineKeyboardButton(text="Пока пусто", callback_data="noop")]]
    else:
        rows = [[InlineKeyboardButton(text=f"📚 {s}", callback_data=f"show_hw_{s}")] for s in subjects]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 Загрузить расписание", callback_data="admin_schedule")],
        [InlineKeyboardButton(text="📚 Загрузить домашку", callback_data="admin_homework")],
        [InlineKeyboardButton(text="🖼 Заменить баннер", callback_data="admin_banner")],
        [InlineKeyboardButton(text="🎨 Заменить стикер Матвея", callback_data="admin_sticker")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_broadcast")],
    ])

def admin_schedule_menu():
    rows = [[InlineKeyboardButton(text=f"📅 {d}", callback_data=f"set_schedule_{d}")] for d in DAYS]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def admin_homework_menu():
    subjects = list(storage["homework"].keys())
    rows = [[InlineKeyboardButton(text=f"📚 {s}", callback_data=f"set_hw_{s}")] for s in subjects]
    rows.append([InlineKeyboardButton(text="➕ Добавить предмет", callback_data="add_subject")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

# ============ ХЕЛПЕР: БЕЗОПАСНЫЙ EDIT ============
async def safe_edit(call: CallbackQuery, text: str, reply_markup=None):
    """Пытается отредактировать сообщение, если не получается — отправляет новое."""
    try:
        await call.message.edit_text(text, reply_markup=reply_markup)
    except Exception:
        try:
            await call.message.answer(text, reply_markup=reply_markup)
        except Exception as e:
            print(f"safe_edit error: {e}")

# ============ СТАРТ ============
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    if user_id not in storage["users"]:
        storage["users"].append(user_id)
        save_storage(storage)

    text = "👋 <b>Привет!</b>\n\nВыбирай, что нужно:"
    banner = storage.get("banner")
    if banner:
        try:
            await message.answer_photo(banner, caption=text, reply_markup=main_menu())
            return
        except Exception as e:
            storage["banner"] = None
            save_storage(storage)
            if message.from_user.id == ADMIN_ID:
                await message.answer(f"⚠️ Баннер был битый, сброшен.\n<code>{e}</code>")
    await message.answer(text, reply_markup=main_menu())

# ============ АДМИНКА ============
@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("🔧 <b>Админ-панель</b>", reply_markup=admin_menu())

# ============ CALLBACK: ГЛАВНОЕ МЕНЮ ============
@dp.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery):
    await safe_edit(call, "Выбирай, что нужно:", main_menu())
    await call.answer()

@dp.callback_query(F.data == "menu_schedule")
async def menu_schedule(call: CallbackQuery):
    await safe_edit(call, "📅 <b>Выбери день:</b>", schedule_menu())
    await call.answer()

@dp.callback_query(F.data == "menu_homework")
async def menu_homework(call: CallbackQuery):
    await safe_edit(call, "📚 <b>Выбери предмет:</b>", homework_menu())
    await call.answer()

@dp.callback_query(F.data == "menu_matvey")
async def menu_matvey(call: CallbackQuery):
    if storage.get("sticker"):
        try:
            await call.message.answer_sticker(storage["sticker"])
        except Exception:
            storage["sticker"] = None
            save_storage(storage)
            await call.message.answer("⚠️ Стикер битый, загрузи заново через /admin")
    else:
        await call.message.answer("🤡 Матвей пидор (стикер ещё не загружен)")
    await call.answer()

@dp.callback_query(F.data == "noop")
async def noop(call: CallbackQuery):
    await call.answer()

# ============ ПОКАЗ РАСПИСАНИЯ / ДОМАШКИ ============
@dp.callback_query(F.data.startswith("show_schedule_"))
async def show_schedule(call: CallbackQuery):
    day = call.data.replace("show_schedule_", "")
    file_id = storage["schedule"].get(day)
    if file_id:
        try:
            await call.message.answer_photo(file_id, caption=f"📅 <b>{day}</b>")
        except Exception as e:
            storage["schedule"][day] = None
            save_storage(storage)
            await call.message.answer(f"⚠️ Фото на <b>{day}</b> битое, загрузи заново через /admin\n<code>{e}</code>")
    else:
        await call.message.answer(f"📅 На <b>{day}</b> расписание ещё не загружено")
    await call.answer()

@dp.callback_query(F.data.startswith("show_hw_"))
async def show_hw(call: CallbackQuery):
    subject = call.data.replace("show_hw_", "")
    file_id = storage["homework"].get(subject)
    if file_id:
        try:
            await call.message.answer_photo(file_id, caption=f"📚 <b>{subject}</b>")
        except Exception as e:
            storage["homework"][subject] = None
            save_storage(storage)
            await call.message.answer(f"⚠️ Фото по <b>{subject}</b> битое, загрузи заново через /admin\n<code>{e}</code>")
    else:
        await call.message.answer(f"📚 По <b>{subject}</b> домашка ещё не загружена")
    await call.answer()

# ============ CALLBACK: АДМИНКА ============
@dp.callback_query(F.data == "admin_back")
async def admin_back(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await safe_edit(call, "🔧 <b>Админ-панель</b>", admin_menu())
    await call.answer()

@dp.callback_query(F.data == "admin_schedule")
async def admin_schedule(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await safe_edit(call, "📅 <b>Какой день загружаем?</b>", admin_schedule_menu())
    await call.answer()

@dp.callback_query(F.data == "admin_homework")
async def admin_homework(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    await safe_edit(call, "📚 <b>Какой предмет загружаем?</b>", admin_homework_menu())
    await call.answer()

@dp.callback_query(F.data.startswith("set_schedule_"))
async def set_schedule(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    day = call.data.replace("set_schedule_", "")
    admin_state[call.from_user.id] = f"schedule_{day}"
    await safe_edit(call, f"📸 Отправь фото расписания на <b>{day}</b>")
    await call.answer()

@dp.callback_query(F.data.startswith("set_hw_"))
async def set_hw(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    subject = call.data.replace("set_hw_", "")
    admin_state[call.from_user.id] = f"homework_{subject}"
    await safe_edit(call, f"📸 Отправь фото домашки по <b>{subject}</b>")
    await call.answer()

@dp.callback_query(F.data == "add_subject")
async def add_subject(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    admin_state[call.from_user.id] = "new_subject"
    await safe_edit(call, "✏️ Напиши название нового предмета:")
    await call.answer()

@dp.callback_query(F.data == "admin_banner")
async def admin_banner(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    admin_state[call.from_user.id] = "banner"
    await safe_edit(call, "🖼 Отправь новую картинку-баннер:")
    await call.answer()

@dp.callback_query(F.data == "admin_sticker")
async def admin_sticker(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    admin_state[call.from_user.id] = "sticker"
    await safe_edit(call, "🎨 Отправь стикер для Матвея:")
    await call.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast(call: CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return
    admin_state[call.from_user.id] = "broadcast"
    await safe_edit(call, "📢 Напиши текст рассылки:")
    await call.answer()

# ============ ПРИЁМ ФОТО/СТИКЕРА ============
@dp.message(F.photo)
async def handle_photo(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    state = admin_state.get(message.from_user.id)
    if not state:
        return
    file_id = message.photo[-1].file_id

    if state.startswith("schedule_"):
        day = state.replace("schedule_", "")
        storage["schedule"][day] = file_id
        save_storage(storage)
        await message.answer(f"✅ Расписание на <b>{day}</b> обновлено!")
        await broadcast(f"📅 Расписание на <b>{day}</b> обновлено! Смотри в меню.")

    elif state.startswith("homework_"):
        subject = state.replace("homework_", "")
        storage["homework"][subject] = file_id
        save_storage(storage)
        await message.answer(f"✅ Домашка по <b>{subject}</b> обновлена!")
        await broadcast(f"📚 Домашка по <b>{subject}</b> обновлена! Смотри в меню.")

    elif state == "banner":
        storage["banner"] = file_id
        save_storage(storage)
        await message.answer("✅ Баннер обновлён!")

    admin_state.pop(message.from_user.id, None)

@dp.message(F.sticker)
async def handle_sticker(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    state = admin_state.get(message.from_user.id)
    if state == "sticker":
        storage["sticker"] = message.sticker.file_id
        save_storage(storage)
        await message.answer("✅ Стикер Матвея обновлён!")
        admin_state.pop(message.from_user.id, None)

# ============ ТЕКСТ ОТ АДМИНА ============
@dp.message(F.text)
async def handle_text(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    state = admin_state.get(message.from_user.id)
    if not state:
        return

    if state == "new_subject":
        subject = message.text.strip()
        if subject and subject not in storage["homework"]:
            storage["homework"][subject] = None
            save_storage(storage)
            await message.answer(f"✅ Предмет <b>{subject}</b> добавлен! Теперь загрузи фото.")
            await message.answer("📚 Выбери предмет:", reply_markup=admin_homework_menu())
        else:
            await message.answer("⚠️ Такой предмет уже есть или пустое название.")
        admin_state.pop(message.from_user.id, None)

    elif state == "broadcast":
        text = message.text
        admin_state.pop(message.from_user.id, None)
        count = await broadcast(text)
        await message.answer(f"✅ Рассылка отправлена {count} пользователям.")

# ============ РАССЫЛКА ============
async def broadcast(text: str) -> int:
    count = 0
    for user_id in storage["users"]:
        try:
            await bot.send_message(user_id, text)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            pass
    return count

# ============ ЗАПУСК ============
async def main():
    if "СЮДА_ВСТАВЬ" in BOT_TOKEN:
        print("❌ Ты не вставил токен! Открой файл и замени BOT_TOKEN.")
        return
    print(f"✅ Бот запущен! ADMIN_ID: {ADMIN_ID}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())