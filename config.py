import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(',') if id.strip()]
DB_NAME = os.getenv("DB_NAME", "xxxxxx").strip()
DB_USER = os.getenv("DB_USER", "xxxxx").strip()
DB_PASSWORD = os.getenv("DB_PASSWORD", "xxxx").strip()
DB_HOST = os.getenv("DB_HOST", "xxxxx").strip()
DB_PORT = int(os.getenv("DB_PORT", xxxxx))

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
