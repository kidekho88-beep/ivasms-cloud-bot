import json, subprocess, os, signal
import telebot
from telebot import types
from config import BOT_TOKEN, ADMINS

bot = telebot.TeleBot(BOT_TOKEN)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROCESSES = {}

ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
GROUPS_FILE = os.path.join(BASE_DIR, "groups.json")

# ---------- Utils ----------
def load_json(p, default):
    if not os.path.exists(p):
        with open(p, "w") as f:
            json.dump(default, f)
        return default
    try:
        with open(p, "r") as f:
            d = f.read().strip()
            return json.loads(d) if d else default
    except:
        with open(p, "w") as f:
            json.dump(default, f)
        return default

def save_json(p, data):
    with open(p, "w") as f:
        json.dump(data, f, indent=2)

def is_admin(uid):
    return uid in ADMINS

# ---------- Handlers ----------
@bot.message_handler(commands=["start"])
def start(msg):
    if not is_admin(msg.from_user.id):
        return

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("🚀 Run Bot", "⛔ Stop Bot", "📊 Status")
    bot.send_message(
        msg.chat.id,
        "⚙️ iVASMS Control Panel\n\n"
        "/addacc <email> <pass>\n"
        "/rmvacc <email>\n"
        "/addgroup  (এই কমান্ড গ্রুপের ভিতরে দিতে হবে)\n"
        "/rmvgroup <group_id>\n"
        "/myaccount\n",
        reply_markup=kb
    )

# ---------- Run Menu ----------
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
    kb.add(types.InlineKeyboardButton("🚀 Run All Available Bots", callback_data="run_all"))
    bot.send_message(msg.chat.id, "👇 Choose account to run:", reply_markup=kb)

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
        bot.edit_message_text(f"▶️ Bot started for:\n{email}", call.message.chat.id, call.message.message_id)

def start_scraper(email):
    global PROCESSES
    if email in PROCESSES:
        return
    PROCESSES[email] = subprocess.Popen(
        ["python", "scraper.py", email],
        cwd=BASE_DIR
    )

# ---------- Stop / Status ----------
@bot.message_handler(func=lambda m: m.text == "⛔ Stop Bot")
def stop_all(msg):
    global PROCESSES
    if not is_admin(msg.from_user.id):
        return

    for p in PROCESSES.values():
        try:
            p.terminate()
        except:
            pass

    PROCESSES = {}
    bot.reply_to(msg, "⛔ All bots stopped")

@bot.message_handler(func=lambda m: m.text == "📊 Status")
def status(msg):
    if not is_admin(msg.from_user.id):
        return
    running = list(PROCESSES.keys())
    bot.reply_to(msg, "🟢 Running bots:\n" + ("\n".join(running) if running else "None"))

# ---------- Accounts ----------
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
    if len(p) < 2:
        return bot.reply_to(msg, "Usage: /rmvacc email")

    acc = load_json(ACCOUNTS_FILE, [])
    acc = [a for a in acc if a["email"] != p[1]]
    save_json(ACCOUNTS_FILE, acc)
    bot.reply_to(msg, "🗑 Account removed")

# ---------- Groups ----------
@bot.message_handler(commands=["addgroup"])
def addgroup(msg):
    if not is_admin(msg.from_user.id):
        return

    # Must be used inside group/supergroup
    if msg.chat.type not in ["group", "supergroup"]:
        return bot.reply_to(msg, "❌ এই কমান্ডটা গ্রুপের ভিতরে দিয়ে দাও")

    groups = load_json(GROUPS_FILE, [])
    gid = msg.chat.id

    if gid not in groups:
        groups.append(gid)
        save_json(GROUPS_FILE, groups)

    bot.reply_to(msg, f"✅ Group added\nID: {gid}")

@bot.message_handler(commands=["rmvgroup"])
def rmvgroup(msg):
    if not is_admin(msg.from_user.id):
        return

    p = msg.text.split()
    if len(p) < 2:
        return bot.reply_to(msg, "Usage: /rmvgroup <group_id>")

    groups = load_json(GROUPS_FILE, [])
    groups = [g for g in groups if str(g) != str(p[1])]
    save_json(GROUPS_FILE, groups)
    bot.reply_to(msg, "🗑 Group removed")

# ---------- My Account ----------
@bot.message_handler(commands=["myaccount"])
def myacc(msg):
    if not is_admin(msg.from_user.id):
        return

    acc = load_json(ACCOUNTS_FILE, [])
    groups = load_json(GROUPS_FILE, [])

    text = "Accounts:\n"
    if acc:
        for a in acc:
            text += f"- {a['email']}\n"
    else:
        text += "None\n"

    text += "\nGroups:\n"
    if groups:
        for g in groups:
            text += f"- {g}\n"
    else:
        text += "None\n"

    bot.reply_to(msg, text)

# ---------- Start Bot ----------
print("🤖 Control Panel Bot Started")
bot.infinity_polling(skip_pending=True)
