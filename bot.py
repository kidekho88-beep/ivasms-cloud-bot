import os, json, subprocess
import telebot
from telebot import types

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x.strip().isdigit()]

bot = telebot.TeleBot(BOT_TOKEN)
PROCESSES = {}

def load_json(p, d):
    if not os.path.exists(p):
        with open(p,"w") as f: json.dump(d,f)
        return d
    try:
        return json.load(open(p))
    except:
        return d

def save_json(p, d):
    json.dump(d, open(p,"w"), indent=2)

def is_admin(uid): return uid in ADMINS

@bot.message_handler(commands=["start"])
def start(m):
    if not is_admin(m.from_user.id): return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚀 Run", "⛔ Stop", "📊 Status")
    bot.send_message(m.chat.id, "IVASMS Control Panel", reply_markup=kb)

@bot.message_handler(func=lambda m: m.text=="🚀 Run")
def run(m):
    if not is_admin(m.from_user.id): return
    p = subprocess.Popen(["python","worker.py"])
    PROCESSES["main"] = p
    bot.reply_to(m, "🚀 Worker started")

@bot.message_handler(func=lambda m: m.text=="⛔ Stop")
def stop(m):
    for p in PROCESSES.values():
        try: p.terminate()
        except: pass
    PROCESSES.clear()
    bot.reply_to(m, "⛔ Worker stopped")

@bot.message_handler(func=lambda m: m.text=="📊 Status")
def status(m):
    bot.reply_to(m, f"Running: {list(PROCESSES.keys())}")

@bot.message_handler(commands=["setcookie"])
def setcookie(m):
    if not is_admin(m.from_user.id): return
    cookie = m.text.replace("/setcookie","").strip()
    save_json("session.json", {"cookie": cookie})
    bot.reply_to(m, "✅ Cookie updated")

print("Bot started")
bot.infinity_polling(skip_pending=True)
