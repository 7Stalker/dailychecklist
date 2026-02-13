import aiosqlite
from config import DB_NAME
from datetime import datetime, timedelta

async def create_tables():
    async with aiosqlite.connect(DB_NAME) as db:
        # YANGI JADVAL: Foydalanuvchilar
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # 1. Odatlar ro'yxati (Oldingidek)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                is_done BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. YANGI: Tarix jurnali (Logs)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()

async def add_habit(user_id: int, name: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO habits (user_id, name) VALUES (?, ?)", (user_id, name))
        await db.commit()

async def get_habits(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM habits WHERE user_id = ?", (user_id,)) as cursor:
            return await cursor.fetchall()

async def toggle_habit_status(habit_id: int, user_id: int):
    """Odat bajarilganda Log yozamiz, bekor qilinsa Logni o'chiramiz"""
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_done FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id)) as cursor:
            row = await cursor.fetchone()
            if row:
                current_status = row[0]
                new_status = 0 if current_status else 1
                
                # 1. Statusni o'zgartiramiz
                await db.execute("UPDATE habits SET is_done = ? WHERE id = ?", (new_status, habit_id))
                
                # 2. LOG yozamiz yoki o'chiramiz
                if new_status == 1:
                    # Bajarildi -> Tarixga yozamiz
                    await db.execute("INSERT INTO habit_logs (habit_id, user_id) VALUES (?, ?)", (habit_id, user_id))
                else:
                    # Bekor qilindi -> Bugungi logni o'chiramiz (tasodifan bosib qo'yilgan bo'lsa)
                    # "date('now')" funksiyasi bugungi sanadagi logni topadi
                    await db.execute("""
                        DELETE FROM habit_logs 
                        WHERE habit_id = ? AND date(completed_at) = date('now')
                    """, (habit_id,))
                
                await db.commit()
                return True
    return False

async def delete_habit(habit_id: int, user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM habits WHERE id = ? AND user_id = ?", (habit_id, user_id))
        # Loglarni ham o'chiramiz (ixtiyoriy, tarix qolsin desangiz bu qatorni o'chiring)
        await db.execute("DELETE FROM habit_logs WHERE habit_id = ?", (habit_id,))
        await db.commit()

async def reset_daily_habits():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE habits SET is_done = 0")
        await db.commit()

async def get_users_with_pending_habits():
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT DISTINCT user_id FROM habits WHERE is_done = 0") as cursor:
            return [row[0] for row in await cursor.fetchall()]

# --- YANGI: Statistika funksiyalari ---

async def get_monthly_stats(user_id: int):
    """Oxirgi 30 kunlik statistika"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        # Qaysi odat necha marta bajarilgan?
        sql = """
            SELECT h.name, COUNT(l.id) as count
            FROM habits h
            LEFT JOIN habit_logs l ON h.id = l.habit_id
            WHERE h.user_id = ? AND l.completed_at >= date('now', '-30 days')
            GROUP BY h.name
            ORDER BY count DESC
        """
        async with db.execute(sql, (user_id,)) as cursor:
            return await cursor.fetchall()

async def get_time_stats(user_id: int):
    """Odatlar qaysi soatda bajarilayapti?"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        # Soatlarni guruhlaymiz (masalan: 08:00 da 5 ta, 09:00 da 2 ta)
        sql = """
            SELECT strftime('%H', completed_at) as hour, COUNT(*) as count
            FROM habit_logs
            WHERE user_id = ?
            GROUP BY hour
            ORDER BY count DESC
            LIMIT 1
        """
        async with db.execute(sql, (user_id,)) as cursor:
            return await cursor.fetchone()
            
async def add_user(user_id: int, full_name: str, username: str):
    """Yangi foydalanuvchini bazaga saqlash"""
    async with aiosqlite.connect(DB_NAME) as db:
        # INSERT OR IGNORE - agar foydalanuvchi oldin kirgan bo'lsa, xato bermaydi
        await db.execute("""
            INSERT OR IGNORE INTO users (user_id, full_name, username) 
            VALUES (?, ?, ?)
        """, (user_id, full_name, username))
        await db.commit()

async def get_all_users():
    """Admin uchun barcha foydalanuvchilar ro'yxatini olish"""
    async with aiosqlite.connect(DB_NAME) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users ORDER BY joined_at DESC") as cursor:
            return await cursor.fetchall()