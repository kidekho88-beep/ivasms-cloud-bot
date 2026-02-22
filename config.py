import os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Railway Variables থেকে আসবে
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in environment")

ADMINS = []
_admins = os.getenv("ADMINS", "")
if _admins:
    try:
        ADMINS = [int(x.strip()) for x in _admins.split(",") if x.strip().isdigit()]
    except:
        ADMINS = []
