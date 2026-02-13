import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# YANGI: O'zingizning Telegram ID raqamingizni shu yerga yozing (masalan: 123456789)
ADMIN_ID = 643932110 

DB_NAME = "checklist.db"