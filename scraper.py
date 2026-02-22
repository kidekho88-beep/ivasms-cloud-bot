import time
import threading

RUNNING = {}
LOCK = threading.Lock()

def start_scraper_for_account(acc, bot, chat_id):
    email = acc["email"]

    with LOCK:
        if RUNNING.get(email):
            bot.send_message(chat_id, f"⚠️ Already running:\n<code>{email}</code>")
            return
        RUNNING[email] = True

    bot.send_message(chat_id, f"🚀 Started scraper for:\n<code>{email}</code>")

    try:
        while RUNNING.get(email):
            # এখানে পরে real OTP scraping logic বসানো যাবে
            print(f"[SCRAPER] Running for {email}")
            time.sleep(15)
    except Exception as e:
        print(f"[SCRAPER ERROR] {email} -> {e}")
    finally:
        with LOCK:
            RUNNING[email] = False
        bot.send_message(chat_id, f"❌ Scraper stopped:\n<code>{email}</code>")

def stop_all_scrapers():
    with LOCK:
        for k in RUNNING.keys():
            RUNNING[k] = False

def get_status():
    with LOCK:
        if not RUNNING:
            return "No scrapers running"
        txt = ""
        for k, v in RUNNING.items():
            txt += f"{k} → {'🟢 Running' if v else '🔴 Stopped'}\n"
        return txt
