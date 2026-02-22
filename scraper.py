import sys, time, json, os, re, requests
from playwright.sync_api import sync_playwright

RUN_EMAIL = sys.argv[1] if len(sys.argv) > 1 else None
from config import BOT_TOKEN

LOGIN_URL = "https://www.ivasms.com/login"
DASHBOARD_URL = "https://www.ivasms.com/portal/live/my_sms"

def load_json(p, default):
    if not os.path.exists(p):
        with open(p, "w") as f: json.dump(default, f)
        return default
    try:
        with open(p, "r") as f:
            d = f.read().strip()
            return json.loads(d) if d else default
    except:
        return default

def send_telegram(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=20)
    except Exception as e:
        print("Telegram error:", e)

def extract_otp(text):
    m = re.findall(r"\b\d{4,8}\b", text)
    return m[0] if m else None

seen = set()

def main():
    accounts = load_json("accounts.json", [])
    groups = load_json("groups.json", [])
    if RUN_EMAIL:
        accounts = [a for a in accounts if a["email"] == RUN_EMAIL]

    if not accounts:
        print("No accounts.")
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context()
        page = context.new_page()

        for acc in accounts:
            print("🔐 Login:", acc["email"])
            page.goto(LOGIN_URL, timeout=120000)
            page.wait_for_timeout(30000)  # Cloudflare human-like wait

            page.fill('input[name="email"]', acc["email"])
            page.fill('input[name="password"]', acc["pass"])
            page.click('button[type="submit"]')
            page.wait_for_timeout(30000)

            page.goto(DASHBOARD_URL, timeout=120000)
            page.wait_for_timeout(15000)

            print("📄 Title:", page.title())

            while True:
                rows = page.query_selector_all("table tbody tr")
                for r in rows:
                    tds = r.query_selector_all("td")
                    if not tds:
                        continue
                    msg = tds[-1].inner_text().strip()
                    num = tds[1].inner_text().strip() if len(tds) > 1 else "N/A"
                    otp = extract_otp(msg)
                    if otp and otp not in seen:
                        seen.add(otp)
                        out = f"🔔 New OTP\n\n📞 {num}\n💬 {msg}\n🔑 OTP: {otp}"
                        print(out)
                        for gid in groups:
                            send_telegram(gid, out)
                time.sleep(10)

if __name__ == "__main__":
    main()
