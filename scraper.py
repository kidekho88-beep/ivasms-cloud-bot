import sys, time, json, os, re, requests, traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import BOT_TOKEN

# ---------- CONFIG ----------
RUN_EMAIL = sys.argv[1] if len(sys.argv) > 1 else None

CHROME_BIN = os.getenv("CHROME_BIN", "/usr/bin/chromium-browser")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

LOGIN_URL = "https://www.ivasms.com/login"
DASHBOARD_URL = "https://www.ivasms.com/portal/live/my_sms"

SESSION_FILE = "sessions.json"
POLL_INTERVAL = 10
RETRY_BACKOFF = 30

seen_otps = set()

# ---------- JSON SAFE ----------
def load_json(p, default):
    try:
        if not os.path.exists(p):
            with open(p, "w") as f:
                json.dump(default, f)
            return default
        with open(p, "r") as f:
            data = f.read().strip()
            return json.loads(data) if data else default
    except Exception as e:
        print("⚠ JSON error:", p, e)
        with open(p, "w") as f:
            json.dump(default, f)
        return default

def save_json(p, data):
    with open(p, "w") as f:
        json.dump(data, f, indent=2)

# ---------- TELEGRAM ----------
def send(chat_id, txt):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, data={"chat_id": chat_id, "text": txt}, timeout=20)
    except Exception as e:
        print("Telegram send error:", e)

# ---------- UTILS ----------
def extract_otp(t):
    m = re.findall(r"\b\d{4,8}\b", t)
    return m[0] if m else None

def detect_tags(number):
    if number.startswith("+977"): return "🇳🇵", "NP"
    if number.startswith("+880"): return "🇧🇩", "BD"
    if number.startswith("+91"):  return "🇮🇳", "IN"
    if number.startswith("+84"):  return "🇻🇳", "VN"
    if number.startswith("+62"):  return "🇮🇩", "ID"
    return "🌍", "XX"

def detect_service(msg):
    m = msg.lower()
    if "whatsapp" in m: return "WS"
    if "telegram" in m: return "TG"
    if "google" in m:   return "GG"
    if "facebook" in m:return "FB"
    if "tiktok" in m:  return "TT"
    return "OTP"

# ---------- DRIVER ----------
def build_driver():
    o = Options()
    o.add_argument("--headless=new")
    o.add_argument("--no-sandbox")
    o.add_argument("--disable-dev-shm-usage")
    o.add_argument("--disable-gpu")
    o.add_argument("--window-size=1280,720")
    o.add_argument("--disable-blink-features=AutomationControlled")
    if CHROME_BIN:
        o.binary_location = CHROME_BIN

    s = Service(CHROMEDRIVER_PATH)
    d = webdriver.Chrome(service=s, options=o)
    d.set_page_load_timeout(120)
    return d

# ---------- SESSION ----------
def login_and_cache_session(driver, email, password):
    print("🔐 Login:", email)
    driver.get(LOGIN_URL)

    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.NAME, "email"))
    )

    driver.find_element(By.NAME, "email").clear()
    driver.find_element(By.NAME, "email").send_keys(email)

    driver.find_element(By.NAME, "password").clear()
    driver.find_element(By.NAME, "password").send_keys(password)

    driver.find_element(By.XPATH, "//button[@type='submit']").click()

    time.sleep(20)  # wait for redirect

    cookies = driver.get_cookies()
    sess = load_json(SESSION_FILE, {})
    sess[email] = cookies
    save_json(SESSION_FILE, sess)
    print("💾 Session cached for:", email)

def restore_session(driver, email):
    sess = load_json(SESSION_FILE, {})
    cookies = sess.get(email)
    if not cookies:
        return False

    driver.get("https://www.ivasms.com/")
    for c in cookies:
        try:
            driver.add_cookie(c)
        except:
            pass

    driver.get(DASHBOARD_URL)
    time.sleep(10)

    if "login" in (driver.current_url or "").lower():
        print("♻️ Session expired for:", email)
        return False

    print("♻️ Session restored for:", email)
    return True

# ---------- SCRAPE ----------
def scrape_realtime(driver, groups):
    driver.get(DASHBOARD_URL)
    WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    print("✅ Live SMS page loaded")

    while True:
        rows = driver.find_elements(By.XPATH, "//table//tbody//tr")
        for r in rows:
            try:
                tds = r.find_elements(By.TAG_NAME, "td")
                if len(tds) < 3:
                    continue

                number = tds[1].text.strip()
                msg = tds[-1].text.strip()
                otp = extract_otp(msg)

                if otp and otp not in seen_otps:
                    seen_otps.add(otp)
                    flag, cc = detect_tags(number)
                    svc = detect_service(msg)

                    txt = f"{flag} #{svc} #{cc}\n{number}\n\n{otp}"

                    for g in groups:
                        send(g, txt)

                    print("📩 OTP:", otp)

            except Exception as e:
                print("Row parse error:", e)

        time.sleep(POLL_INTERVAL)
        driver.refresh()

# ---------- MAIN ----------
def main():
    print("🚀 Realtime Scraper started for:", RUN_EMAIL or "ALL")

    while True:
        driver = None
        try:
            accounts = load_json("accounts.json", [])
            groups = load_json("groups.json", [])

            if RUN_EMAIL:
                accounts = [a for a in accounts if a.get("email") == RUN_EMAIL]

            if not accounts:
                print("⚠ No accounts found, waiting...")
                time.sleep(20)
                continue

            for acc in accounts:
                driver = build_driver()

                ok = restore_session(driver, acc["email"])
                if not ok:
                    login_and_cache_session(driver, acc["email"], acc["pass"])

                scrape_realtime(driver, groups)

        except Exception as e:
            print("❌ Fatal error:", e)
            traceback.print_exc()
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            time.sleep(RETRY_BACKOFF)

if __name__ == "__main__":
    main()
