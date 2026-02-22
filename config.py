import os

# Telegram Bot Token (Railway/Termux env থেকে নিবে)
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin user IDs (comma separated: "123456789,987654321")
_raw_admins = os.getenv("ADMINS", "")
ADMINS = [int(x.strip()) for x in _raw_admins.split(",") if x.strip().isdigit()]

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN not set! Railway Variables এ BOT_TOKEN বসাও।")

if not ADMINS:
    raise RuntimeError("❌ ADMINS not set! Railway Variables এ ADMINS বসাও (comma separated IDs)।")
