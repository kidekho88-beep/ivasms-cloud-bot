import sys, os, json, time, re, traceback
from playwright.sync_api import sync_playwright
import requests
from config import BOT_TOKEN

RUN_EMAIL = sys.argv[1] if len(sys.argv) > 1 else None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_FILE = os.path.join(BASE_DIR, "accounts.json")
GROUPS_FILE = os.path.join(BASE_DIR, "groups.json")
SESSIONS_FILE = os.path.join(BASE_DIR, "sessions.json")

LOGIN_URL = "https://www.ivasms.com/login"
DASHBOARD_URL = "https://www.ivasms.com/portal/live/my_sms"

POLL_INTERVAL = 8

def load_json(p, default):
    if not os.path.exists(p):
        with open(p, "w") as f: json.dump(default, f)
        return default
    try:
        with open(p, "r") as f: return json.load(f)
    except: return default

def save_json(p, data):
    with open(p, "w") as f: json.dump(data, f, indent=2)

def send(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=20)

def extract_otp(msg):
    m = re.findall(r"\b\d{4,8}\b", msg)
    return m[0] if m else None

def detect_service(msg):
    m = msg.lower()
    if "whatsapp" in m: return "WS"
    if "telegram" in m: return "TG"
    if "google" in m: return "GG"
    if "facebook" in m: return "FB"
    return "OTP"

def detect_country(num):
    if num.startswith("+880"): return "🇧🇩", "BD"
    if num.startswith("+91"): return "🇮🇳", "IN"
    if num.startswith("+84"): return "🇻🇳", "VN"
    return "🌍", "XX"

def login_and_save(context, email, password):
    page = context.new_page()
    page.goto(LOGIN_URL, timeout=120000)
    page.fill("input[name=email]", email)
    page.fill("input[name=password]", password)
    page.click("button[type=submit]")
    page.wait_for_url("**/portal/**", timeout=120000)
    storage = context.storage_state()
    sess = load_json(SESSIONS_FILE, {})
    sess[email] = storage
    save_json(SESSIONS_FILE, sess)
    page.close()

def restore_context(browser, email):
    sess = load_json(SESSIONS_FILE, {})
    state = sess.get(email)
    if not state: return None
    return browser.new_context(storage_state=state)

def main():
    accounts = load_json(ACCOUNTS_FILE, [])
    groups = load_json(GROUPS_FILE, [])
    if RUN_EMAIL:
        accounts = [a for a in accounts if a["email"] == RUN_EMAIL]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for acc in accounts:
            ctx = restore_context(browser, acc["email"])
            if not ctx:
                ctx = browser.new_context()
                login_and_save(ctx, acc["email"], acc["pass"])
            page = ctx.new_page()
            page.goto(DASHBOARD_URL, timeout=120000)

            seen = set()
            while True:
                rows = page.query_selector_all("table tbody tr")
                for r in rows:
                    tds = r.query_selector_all("td")
                    if len(tds) < 3: continue
                    number = tds[1].inner_text().strip()
                    msg = tds[-1].inner_text().strip()
                    otp = extract_otp(msg)
                    if otp and otp not in seen:
                        seen.add(otp)
                        flag, cc = detect_country(number)
                        svc = detect_service(msg)
                        text = f"{flag} #{svc} #{cc}\n{number}\n\n{otp}"
                        for g in groups:
                            send(g, text)
                time.sleep(POLL_INTERVAL)
                page.reload()

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print("❌ Error:", e)
            traceback.print_exc()
            time.sleep(20)
