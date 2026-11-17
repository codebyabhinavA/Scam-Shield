import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in .env")

ACCESS_TOKEN_MINUTES = 60
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL")
if not GEMINI_API_KEY or not GEMINI_MODEL:
    raise RuntimeError("GEMINI_API_KEY and GEMINI_MODEL must be set in .env")
FRONTEND_ORIGINS = [
    o.strip()
    for o in (os.getenv("FRONTEND_ORIGINS") or "http://127.0.0.1:5500,http://localhost:5500").split(",")
    if o.strip()
]