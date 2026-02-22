import json, subprocess, os, time
import telebot
from telebot import types
from config import BOT_TOKEN, ADMINS

bot = telebot.TeleBot(BOT_TOKEN)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSES = {}

ACCOUNTS_FILE = "accounts.json"
GROUPS_FILE = "groups.json"

def load_json(p, default):
    if not os.path.exists(p):
        with open(p, "w") as f:
            json.dump(default, f)
        return default
    try:
        with open(p, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(p, data):
    with open(p, "w") as f:
        json.dump(data, f, indent=2)

def is_admin(uid):
    return uid in ADMINS

@bot.message_handler(commands=["start"])
def start(msg):
    if not is_admin(msg.from_user.id):
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚀 Run Bot", "⛔ Stop Bot", "📊 Status", "🍪 Update Cookies")
    bot.send_message(msg.chat.id,
        "⚙️ iVASMS Control Panel\n\n"
        "/addacc <email> <pass>\n"
        "/rmvacc <email>\n"
        "/addgroup  (গ্রুপে গিয়ে এই কমান্ড দাও)\n"
        "/rmvgroup <group_id>\n"
        "/myaccount\n",
        reply_markup=kb
    )

@bot.message_handler(commands=["addacc"])
def addacc(msg):
    if not is_admin(msg.from_user.id):
        return
    p = msg.text.split(maxsplit=2)
    if len(p) < 3:
        return bot.reply_to(msg, "Usage: /addacc email pass")
    acc = load_json(ACCOUNTS_FILE, [])
    if any(a["email"] == p[1] for a in acc):
        return bot.reply_to(msg, "⚠️ Already exists")
    acc.append({"email": p[1], "pass": p[2]})
    save_json(ACCOUNTS_FILE, acc)
    bot.reply_to(msg, "✅ Account added")

@bot.message_handler(commands=["rmvacc"])
def rmvacc(msg):
    if not is_admin(msg.from_user.id):
        return
    p = msg.text.split()
    acc = load_json(ACCOUNTS_FILE, [])
    acc = [a for a in acc if a["email"] != p[1]]
    save_json(ACCOUNTS_FILE, acc)
    bot.reply_to(msg, "🗑 Account removed")

@bot.message_handler(commands=["addgroup"])
def addgroup(msg):
    if not is_admin(msg.from_user.id):
        return
    if msg.chat.type == "private":
        return bot.reply_to(msg, "❌ এই কমান্ড গ্রুপে গিয়ে দাও")
    groups = load_json(GROUPS_FILE, [])
    gid = msg.chat.id
    if gid not in groups:
        groups.append(gid)
        save_json(GROUPS_FILE, groups)
    bot.reply_to(msg, f"✅ Group added:\n{gid}")

@bot.message_handler(commands=["rmvgroup"])
def rmvgroup(msg):
    if not is_admin(msg.from_user.id):
        return
    p = msg.text.split()
    groups = load_json(GROUPS_FILE, [])
    groups = [g for g in groups if str(g) != p[1]]
    save_json(GROUPS_FILE, groups)
    bot.reply_to(msg, "🗑 Group removed")

@bot.message_handler(commands=["myaccount"])
def myacc(msg):
    if not is_admin(msg.from_user.id):
        return
    acc = load_json(ACCOUNTS_FILE, [])
    groups = load_json(GROUPS_FILE, [])
    txt = "📂 Accounts:\n"
    if acc:
        txt += "\n".join(f"- {a['email']}" for a in acc)
    else:
        txt += "None"
    txt += "\n\n👥 Groups:\n"
    if groups:
        txt += "\n".join(str(g) for g in groups)
    else:
        txt += "None"
    bot.reply_to(msg, txt)

@bot.message_handler(func=lambda m: m.text == "🚀 Run Bot")
def run_all(msg):
    if not is_admin(msg.from_user.id):
        return
    acc = load_json(ACCOUNTS_FILE, [])
    if not acc:
        return bot.reply_to(msg, "⚠️ No accounts")
    for a in acc:
        if a["email"] not in PROCESSES:
            PROCESSES[a["email"]] = subprocess.Popen(["python", "scraper.py", a["email"]], cwd=BASE_DIR)
    bot.reply_to(msg, "🚀 All started")

@bot.message_handler(func=lambda m: m.text == "⛔ Stop Bot")
def stop_all(msg):
    if not is_admin(msg.from_user.id):
        return
    for p in PROCESSES.values():
        try:
            p.terminate()
        except:
            pass
    PROCESSES.clear()
    bot.reply_to(msg, "⛔ All stopped")

@bot.message_handler(func=lambda m: m.text == "📊 Status")
def status(msg):
    if not is_admin(msg.from_user.id):
        return
    running = list(PROCESSES.keys())
    if running:
        bot.reply_to(msg, "🟢 Running:\n" + "\n".join(running))
    else:
        bot.reply_to(msg, "🔴 No running bots")

@bot.message_handler(func=lambda m: m.text == "🍪 Update Cookies")
def cookies(msg):
    if not is_admin(msg.from_user.id):
        return
    bot.reply_to(msg, "🍪 Cookies will refresh automatically on next login.")

print("🤖 Bot started")
bot.infinity_polling(skip_pending=True)
