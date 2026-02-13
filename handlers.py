from config import ADMIN_ID
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


import database as db
from keyboards import get_habit_keyboard, HabitCallback

router = Router()

class HabitForm(StatesGroup):
    waiting_for_name = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    # YANGI: Foydalanuvchini ro'yxatga olamiz
    full_name = message.from_user.full_name
    username = message.from_user.username or "yo'q"
    await db.add_user(user_id, full_name, username)
    habits = await db.get_habits(user_id)
    
    
    total = len(habits)
    done = sum(1 for h in habits if h['is_done'])
    percent = int((done / total) * 100) if total > 0 else 0
    
    text = (
        f"👋 Assalomu alaykum, {message.from_user.full_name}!\n"
        f"Bugungi natijangiz: <b>{percent}%</b>\n\n"
        "📋 <b>Sizning odatlaringiz:</b>"
    )
    await message.answer(text, reply_markup=get_habit_keyboard(habits))

# --- Statistika (YANGI) ---
@router.callback_query(F.data == "stats")
async def show_stats(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    
    # 1. Oylik hisobotni olamiz
    monthly_stats = await db.get_monthly_stats(user_id)
    # 2. Vaqt tahlilini olamiz
    best_time = await db.get_time_stats(user_id)
    
    text = "📊 <b>Sizning Oylik Hisobotingiz (30 kun):</b>\n\n"
    
    if not monthly_stats:
        text += "<i>Hozircha ma'lumot yetarli emas. Odatlarni bajarishda davom eting!</i>"
    else:
        for row in monthly_stats:
            text += f"🔹 <b>{row['name']}:</b> {row['count']} marta bajarildi\n"
            
    text += "\n🕰 <b>Vaqt tahlili:</b>\n"
    if best_time:
        hour = best_time['hour']
        text += f"Siz odatlarni ko'pincha soat <b>{hour}:00 - {int(hour)+1}:00</b> oralig'ida bajarasiz. 🔥"
    else:
        text += "Ma'lumot yo'q."
        
    # Orqaga qaytish tugmasi
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    back_btn = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_home")]])
    
    await callback.message.edit_text(text, reply_markup=back_btn)

@router.callback_query(F.data == "back_home")
async def go_home(callback: types.CallbackQuery):
    await cmd_start(callback.message)

# ... (Qolgan kodlar o'zgarishsiz qoladi: add_new, save_habit, toggle, delete) ...

@router.callback_query(F.data == "add_new")
async def ask_habit_name(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ Yangi odat nomini yozing:")
    await state.set_state(HabitForm.waiting_for_name)
    await callback.answer()

@router.message(HabitForm.waiting_for_name)
async def save_habit(message: types.Message, state: FSMContext):
    await db.add_habit(message.from_user.id, message.text)
    await message.answer(f"✅ '{message.text}' ro'yxatga qo'shildi!")
    await state.clear()
    await cmd_start(message)

@router.callback_query(HabitCallback.filter())
async def handle_habit_action(callback: types.CallbackQuery, callback_data: HabitCallback):
    user_id = callback.from_user.id
    if callback_data.action == "toggle":
        await db.toggle_habit_status(callback_data.id, user_id)
    elif callback_data.action == "delete":
        await db.delete_habit(callback_data.id, user_id)
        await callback.answer("O'chirildi!", show_alert=True)
    
    # Ro'yxatni yangilash
    habits = await db.get_habits(user_id)
    total = len(habits)
    done = sum(1 for h in habits if h['is_done'])
    percent = int((done / total) * 100) if total > 0 else 0
    
    text = (
        f"👋 Assalomu alaykum, {callback.from_user.full_name}!\n"
        f"Bugungi natijangiz: <b>{percent}%</b>\n\n"
        "📋 <b>Sizning odatlaringiz:</b>"
    )
    
# --- ADMIN PANEL ---
@router.message(Command("admin"))
async def cmd_admin(message: types.Message):
    # Xavfsizlik: Faqat ADMIN ishlata oladi
    if message.from_user.id != ADMIN_ID:
        return # Boshqa odam yozsa bot indamaydi
        
    users = await db.get_all_users()
    total_users = len(users)
    
    text = f"👑 <b>Admin Panel</b>\n\n"
    text += f"📊 <b>Umumiy foydalanuvchilar soni:</b> {total_users} ta\n\n"
    text += "👥 <b>Foydalanuvchilar ro'yxati (oxirgi qo'shilganlar):</b>\n"
    
    # Ro'yxat juda uzun bo'lib ketmasligi uchun oxirgi 20 ta odamni ko'rsatamiz
    for u in users[:20]:
        uname = f"@{u['username']}" if u['username'] != "yo'q" else "Username yashirin"
        text += f"🔹 {u['full_name']} ({uname}) - ID: <code>{u['user_id']}</code>\n"
        
    await message.answer(text)
    
    try:
        await callback.message.edit_text(text, reply_markup=get_habit_keyboard(habits))
    except Exception:
        pass