import os
import time
import threading
from telebot import TeleBot, types
from dotenv import load_dotenv

# Load env (Railway will provide env vars automatically)
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = os.getenv("ADMINS", "")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in environment")

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

# Parse admin IDs
ADMIN_IDS = []
if ADMINS:
    try:
        ADMIN_IDS = [int(x.strip()) for x in ADMINS.split(",") if x.strip().isdigit()]
    except Exception:
        ADMIN_IDS = []

# ---------- Helpers ----------
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ---------- Commands ----------
@bot.message_handler(commands=['start'])
def start_cmd(message):
    text = (
        "<b>🤖 IVASMS Cloud Bot</b>\n\n"
        "Welcome! This bot is running on Railway.\n\n"
        "Available commands:\n"
        "• /start - Show this message\n"
        "• /status - Bot status\n\n"
        "If you face any issue, contact admin."
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['status'])
def status_cmd(message):
    uptime = int(time.time() - START_TIME)
    text = (
        "✅ <b>Bot Status: Online</b>\n\n"
        f"⏱ Uptime: <code>{uptime}</code> seconds\n"
        f"👤 Your ID: <code>{message.from_user.id}</code>\n"
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ You are not authorized.")
        return

    text = (
        "🔐 <b>Admin Panel</b>\n\n"
        "Commands:\n"
        "• /status - Check bot status\n"
    )
    bot.reply_to(message, text)

# ---------- Fallback ----------
@bot.message_handler(func=lambda m: True)
def all_messages(message):
    bot.reply_to(message, "❓ Unknown command. Use /start to see options.")

# ---------- Runner ----------
def run_bot():
    while True:
        try:
            print("Bot started polling...")
            bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
        except Exception as e:
            print("Bot crashed, restarting in 5 seconds:", e)
            time.sleep(5)

if __name__ == "__main__":
    START_TIME = time.time()
    run_bot()
