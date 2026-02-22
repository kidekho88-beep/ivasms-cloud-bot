import json, subprocess, os
import telebot
from telebot import types
from config import BOT_TOKEN, ADMINS

bot = telebot.TeleBot(BOT_TOKEN)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSES = {}

def load_json(p, default):
    if not os.path.exists(p):
        with open(p, "w") as f: json.dump(default, f)
        return default
    try:
        with open(p, "r") as f:
            d = f.read().strip()
            return json.loads(d) if d else default
    except:
        with open(p, "w") as f: json.dump(default, f)
        return default

def save_json(p, data):
    with open(p, "w") as f:
        json.dump(data, f, indent=2)

def is_admin(uid):
    return uid in ADMINS

@bot.message_handler(commands=["start"])
def start(msg):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚀 Run Bot", "⛔ Stop Bot", "📊 Status")
    bot.send_message(msg.chat.id,
        "⚙️ iVASMS Control Panel\n\n"
        "/addacc <email> <pass>\n"
        "/rmvacc <email>\n"
        "/addgroup\n"
        "/rmvgroup <id>\n"
        "/myaccount\n",
        reply_markup=kb
    )

@bot.message_handler(func=lambda m: m.text == "🚀 Run Bot")
def run_menu(msg):
    if not is_admin(msg.from_user.id):
        return
    acc = load_json("accounts.json", [])
    if not acc:
        return bot.reply_to(msg, "⚠️ No accounts added")

    kb = types.InlineKeyboardMarkup()
    for a in acc:
        kb.add(types.InlineKeyboardButton(
            f"▶️ Run: {a['email']}",
            callback_data=f"run_one|{a['email']}"
        ))
    kb.add(types.InlineKeyboardButton("🚀 Run All", callback_data="run_all"))
    bot.send_message(msg.chat.id, "👇 Choose account:", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("run_"))
def run_callback(call):
    if not is_admin(call.from_user.id):
        return

    acc = load_json("accounts.json", [])
    if call.data == "run_all":
        for a in acc:
            start_scraper(a["email"])
        bot.edit_message_text("🚀 All bots started!", call.message.chat.id, call.message.message_id)
    else:
        email = call.data.split("|")[1]
        start_scraper(email)
        bot.edit_message_text(f"▶️ Bot started for:\n{email}", call.message.chat.id, call.message.message_id)

def start_scraper(email):
    global PROCESSES
    if email in PROCESSES:
        return
    PROCESSES[email] = subprocess.Popen(["python", "scraper.py", email], cwd=BASE_DIR)

@bot.message_handler(func=lambda m: m.text == "⛔ Stop Bot")
def stop_all(msg):
    global PROCESSES
    if not is_admin(msg.from_user.id):
        return
    for p in PROCESSES.values():
        try: p.terminate()
        except: pass
    PROCESSES = {}
    bot.reply_to(msg, "⛔ All bots stopped")

@bot.message_handler(func=lambda m: m.text == "📊 Status")
def status(msg):
    if not is_admin(msg.from_user.id):
        return
    running = list(PROCESSES.keys())
    bot.reply_to(msg, "🟢 Running bots:\n" + ("\n".join(running) if running else "None"))

@bot.message_handler(commands=["addacc"])
def addacc(msg):
    if not is_admin(msg.from_user.id): return
    p = msg.text.split(maxsplit=2)
    if len(p) < 3:
        return bot.reply_to(msg, "Usage: /addacc email pass")
    acc = load_json("accounts.json", [])
    if any(a["email"] == p[1] for a in acc):
        return bot.reply_to(msg, "⚠️ Already added")
    acc.append({"email": p[1], "pass": p[2]})
    save_json("accounts.json", acc)
    bot.reply_to(msg, "✅ Account added")

@bot.message_handler(commands=["rmvacc"])
def rmvacc(msg):
    if not is_admin(msg.from_user.id): return
    p = msg.text.split()
    acc = load_json("accounts.json", [])
    acc = [a for a in acc if a["email"] != p[1]]
    save_json("accounts.json", acc)
    bot.reply_to(msg, "🗑 Account removed")

@bot.message_handler(commands=["addgroup"])
def addgroup(msg):
    if not is_admin(msg.from_user.id): return
    groups = load_json("groups.json", [])
    if msg.chat.id not in groups:
        groups.append(msg.chat.id)
    save_json("groups.json", groups)
    bot.reply_to(msg, "✅ Group added")

@bot.message_handler(commands=["rmvgroup"])
def rmvgroup(msg):
    if not is_admin(msg.from_user.id): return
    p = msg.text.split()
    groups = load_json("groups.json", [])
    groups = [g for g in groups if str(g) != p[1]]
    save_json("groups.json", groups)
    bot.reply_to(msg, "🗑 Group removed")

@bot.message_handler(commands=["myaccount"])
def myacc(msg):
    if not is_admin(msg.from_user.id): return
    acc = load_json("accounts.json", [])
    groups = load_json("groups.json", [])
    bot.reply_to(msg, f"Accounts:\n{acc}\n\nGroups:\n{groups}")

print("🤖 Control Panel Bot Started")
bot.infinity_polling(skip_pending=True)
