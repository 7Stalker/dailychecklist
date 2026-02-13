from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters.callback_data import CallbackData

class HabitCallback(CallbackData, prefix="habit"):
    action: str
    id: int

def get_habit_keyboard(habits):
    builder = InlineKeyboardBuilder()
    
    for habit in habits:
        status_icon = "✅" if habit['is_done'] else "❌"
        text = f"{status_icon} {habit['name']}"
        
        builder.button(text=text, callback_data=HabitCallback(action="toggle", id=habit['id']))
        builder.button(text="🗑", callback_data=HabitCallback(action="delete", id=habit['id']))
    
    builder.adjust(2)
    
    # Qo'shimcha funksiyalar
    builder.row(InlineKeyboardButton(text="➕ Yangi odat", callback_data="add_new"))
    # YANGI TUGMA:
    builder.row(InlineKeyboardButton(text="📊 Oylik hisobot va Tahlil", callback_data="stats"))
    
    return builder.as_markup()