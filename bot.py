import json, subprocess, os, signal
import telebot
from telebot import types
from config import BOT_TOKEN, ADMINS

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSES = {}

ACCOUNTS_FILE = "accounts.json"
GROUPS_FILE = "groups.json"

# ---------- SAFE JSON ----------
def load_json(path, default):
    try:
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump(default, f)
            return default

        with open(path, "r") as f:
            data = f.read().strip()
            if not data:
                with open(path, "w") as fw:
                    json.dump(default, fw)
                return default
            return json.loads(data)
    except Exception as e:
        print("⚠ JSON error:", path, e)
        with open(path, "w") as f:
            json.dump(default, f)
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def is_admin(uid):
    return uid in ADMINS

# ---------- START ----------
@bot.message_handler(commands=["start"])
def start(msg):
    if not is_admin(msg.from_user.id):
        return bot.reply_to(msg, "❌ Admin only")

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚀 Run Bot", "⛔ Stop Bot")
    kb.add("📊 Status")

    bot.send_message(
        msg.chat.id,
        "⚙️ <b>iVASMS Control Panel</b>\n\n"
        "/addacc <email> <pass>\n"
        "/rmvacc <email>\n"
        "/addgroup  (এই গ্রুপে OTP যাবে)\n"
        "/rmvgroup <group_id>\n"
        "/myaccount\n",
        reply_markup=kb
    )

# ---------- RUN MENU ----------
@bot.message_handler(func=lambda m: m.text == "🚀 Run Bot")
def run_menu(msg):
    if not is_admin(msg.from_user.id):
        return

    acc = load_json(ACCOUNTS_FILE, [])
    if not acc:
        return bot.reply_to(msg, "⚠️ No accounts added")

    kb = types.InlineKeyboardMarkup()
    for a in acc:
        kb.add(types.InlineKeyboardButton(
            f"▶️ Run: {a['email']}",
            callback_data=f"run_one|{a['email']}"
        ))
    kb.add(types.InlineKeyboardButton("🚀 Run ALL", callback_data="run_all"))

    bot.send_message(msg.chat.id, "👇 Choose account to run:", reply_markup=kb)

# ---------- RUN CALLBACK ----------
@bot.callback_query_handler(func=lambda c: c.data.startswith("run_"))
def run_callback(call):
    if not is_admin(call.from_user.id):
        return

    acc = load_json(ACCOUNTS_FILE, [])

    if call.data == "run_all":
        for a in acc:
            start_scraper(a["email"])
        bot.edit_message_text("🚀 All bots started!", call.message.chat.id, call.message.message_id)
    else:
        email = call.data.split("|", 1)[1]
        start_scraper(email)
        bot.edit_message_text(f"▶️ Bot started for:\n<b>{email}</b>", call.message.chat.id, call.message.message_id)

# ---------- START SCRAPER ----------
def start_scraper(email):
    global PROCESSES
    if email in PROCESSES:
        print("Already running:", email)
        return

    p = subprocess.Popen(["python", "scraper.py", email], cwd=BASE_DIR)
    PROCESSES[email] = p
    print("🚀 Scraper started:", email)

# ---------- STOP ALL ----------
@bot.message_handler(func=lambda m: m.text == "⛔ Stop Bot")
def stop_all(msg):
    global PROCESSES
    if not is_admin(msg.from_user.id):
        return

    for email, proc in PROCESSES.items():
        try:
            proc.send_signal(signal.SIGTERM)
        except:
            pass

    PROCESSES = {}
    bot.reply_to(msg, "⛔ All bots stopped")

# ---------- STATUS ----------
@bot.message_handler(func=lambda m: m.text == "📊 Status")
def status(msg):
    if not is_admin(msg.from_user.id):
        return

    running = list(PROCESSES.keys())
    txt = "🟢 Running bots:\n" + ("\n".join(running) if running else "None")
    bot.reply_to(msg, txt)

# ---------- ADD ACCOUNT ----------
@bot.message_handler(commands=["addacc"])
def addacc(msg):
    if not is_admin(msg.from_user.id):
        return

    p = msg.text.split(maxsplit=2)
    if len(p) < 3:
        return bot.reply_to(msg, "❌ Usage: /addacc email password")

    acc = load_json(ACCOUNTS_FILE, [])
    if any(a["email"] == p[1] for a in acc):
        return bot.reply_to(msg, "⚠️ This account already exists")

    acc.append({"email": p[1], "pass": p[2]})
    save_json(ACCOUNTS_FILE, acc)
    bot.reply_to(msg, f"✅ Account added:\n<b>{p[1]}</b>")

# ---------- REMOVE ACCOUNT ----------
@bot.message_handler(commands=["rmvacc"])
def rmvacc(msg):
    if not is_admin(msg.from_user.id):
        return

    p = msg.text.split()
    if len(p) < 2:
        return bot.reply_to(msg, "❌ Usage: /rmvacc email")

    acc = load_json(ACCOUNTS_FILE, [])
    new_acc = [a for a in acc if a["email"] != p[1]]

    if len(new_acc) == len(acc):
        return bot.reply_to(msg, "⚠️ Account not found")

    save_json(ACCOUNTS_FILE, new_acc)
    bot.reply_to(msg, f"🗑 Account removed:\n<b>{p[1]}</b>")

# ---------- ADD GROUP ----------
@bot.message_handler(commands=["addgroup"])
def addgroup(msg):
    if not is_admin(msg.from_user.id):
        return

    groups = load_json(GROUPS_FILE, [])
    if msg.chat.id in groups:
        return bot.reply_to(msg, "⚠️ This group already added")

    groups.append(msg.chat.id)
    save_json(GROUPS_FILE, groups)
    bot.reply_to(msg, f"✅ Group added:\n<b>{msg.chat.id}</b>")

# ---------- REMOVE GROUP ----------
@bot.message_handler(commands=["rmvgroup"])
def rmvgroup(msg):
    if not is_admin(msg.from_user.id):
        return

    p = msg.text.split()
    if len(p) < 2:
        return bot.reply_to(msg, "❌ Usage: /rmvgroup group_id")

    groups = load_json(GROUPS_FILE, [])
    new_groups = [g for g in groups if str(g) != p[1]]

    if len(new_groups) == len(groups):
        return bot.reply_to(msg, "⚠️ Group not found")

    save_json(GROUPS_FILE, new_groups)
    bot.reply_to(msg, f"🗑 Group removed:\n<b>{p[1]}</b>")

# ---------- SHOW DATA ----------
@bot.message_handler(commands=["myaccount"])
def myacc(msg):
    if not is_admin(msg.from_user.id):
        return

    acc = load_json(ACCOUNTS_FILE, [])
    groups = load_json(GROUPS_FILE, [])

    bot.reply_to(
        msg,
        f"📦 <b>Accounts:</b>\n{acc}\n\n👥 <b>Groups:</b>\n{groups}"
    )

print("🤖 Control Panel Bot Started")
bot.infinity_polling(skip_pending=True)
