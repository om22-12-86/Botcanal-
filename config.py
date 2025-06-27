import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(',') if id.strip()]
DB_NAME = os.getenv("DB_NAME", "botcanal").strip()
DB_USER = os.getenv("DB_USER", "botcanal").strip()
DB_PASSWORD = os.getenv("DB_PASSWORD", "botcanal").strip()
DB_HOST = os.getenv("DB_HOST", "localhost").strip()
DB_PORT = int(os.getenv("DB_PORT", 5432))

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"