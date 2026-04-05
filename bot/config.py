import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS") or os.getenv("DB_PASSWORD")

raw_port = os.getenv("DB_PORT")
if not raw_port or raw_port.lower() == "none":
    DB_PORT = "5432"
else:
    DB_PORT = raw_port

def _build_database_url():
    url = os.getenv("DATABASE_URL")
    if url:
        # Railway gives postgresql:// or postgres:// — asyncpg needs postgresql+asyncpg://
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url
    return f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

DATABASE_URL = _build_database_url()

MAX_OLYMPIADS = 10
MAX_COURSES = 10
MAX_PROJECTS = 10

ESSAY_MIN_WORDS = 70
ESSAY_MAX_WORDS = 150

SCENARIO_TIMER_SECONDS = 20
MAX_TIMER_VIOLATIONS = 3