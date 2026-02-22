import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = list(map(int, os.getenv("ADMINS", "").split(","))) if os.getenv("ADMINS") else []

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")
if not ADMINS:
    raise ValueError("ADMINS not set")
