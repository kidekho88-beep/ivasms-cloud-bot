import os
import time
import threading
import telebot
from telebot import types

from scraper import start_scraper_for_account, stop_all_scrapers, get_status

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in environment variables")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

ACCOUNTS = []  # [{"email": "...", "pass": "..."}]

# ====== Commands ======

@bot.message_handler(commands=["start"])
def start_cmd(message):
    bot.reply_to(
        message,
        "🤖 <b>IVASMS Control Panel Bot Started</b>\n\n"
        "/addacc <email> <pass>\n"
        "/rmvacc <email>\n"
        "/myaccount\n"
        "/run\n"
        "/stop\n"
        "/status"
    )

@bot.message_handler(commands=["addacc"])
def add_account(message):
    try:
        _, email, password = message.text.split(maxsplit=2)
        ACCOUNTS.append({"email": email, "pass": password})
        bot.reply_to(message, f"✅ Account added:\n<code>{email}</code>")
    except:
        bot.reply_to(message, "❌ Usage:\n/addacc email password")

@bot.message_handler(commands=["rmvacc"])
def remove_account(message):
    try:
        _, email = message.text.split(maxsplit=1)
        global ACCOUNTS
        ACCOUNTS = [a for a in ACCOUNTS if a["email"] != email]
        bot.reply_to(message, f"🗑️ Removed:\n<code>{email}</code>")
    except:
        bot.reply_to(message, "❌ Usage:\n/rmvacc email")

@bot.message_handler(commands=["myaccount"])
def my_accounts(message):
    if not ACCOUNTS:
        bot.reply_to(message, "❌ No accounts added")
        return

    txt = "📦 <b>Your Accounts:</b>\n\n"
    for acc in ACCOUNTS:
        txt += f"• <code>{acc['email']}</code>\n"
    bot.reply_to(message, txt)

@bot.message_handler(commands=["run"])
def run_all(message):
    if not ACCOUNTS:
        bot.reply_to(message, "❌ No accounts to run")
        return

    for acc in ACCOUNTS:
        threading.Thread(target=start_scraper_for_account, args=(acc, bot, message.chat.id)).start()

    bot.reply_to(message, "🚀 Scraper started for all accounts")

@bot.message_handler(commands=["stop"])
def stop_all(message):
    stop_all_scrapers()
    bot.reply_to(message, "🛑 All scrapers stopped")

@bot.message_handler(commands=["status"])
def status_cmd(message):
    s = get_status()
    bot.reply_to(message, f"📊 <b>Status:</b>\n{s}")

# ====== Safe polling loop ======

def start_bot():
    while True:
        try:
            print("🤖 Bot polling started...")
            bot.infinity_polling(skip_pending=True, timeout=30)
        except Exception as e:
            print("⚠️ Bot crashed, restarting in 10s:", e)
            time.sleep(10)

if __name__ == "__main__":
    start_bot()
