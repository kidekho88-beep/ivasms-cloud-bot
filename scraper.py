import sys, time, json, os, re, requests, traceback
from config import BOT_TOKEN

RUN_EMAIL = sys.argv[1] if len(sys.argv) > 1 else None

IVASMS_API_URL = "https://www.ivasms.com/api/live_sms"  # example (তুমি আসল endpoint বসাবে)
SESSION_FILE = "session.json"
POLL_INTERVAL = 10
seen_otps = set()

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

def save_json(p, data):
    with open(p, "w") as f:
        json.dump(data, f, indent=2)

def send(chat_id, txt):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": chat_id, "text": txt}, timeout=20)

def extract_otp(t):
    m = re.findall(r"\b\d{4,8}\b", t)
    return m[0] if m else None

def detect_tags(number):
    if number.startswith("+977"): return "🇳🇵", "NP"
    if number.startswith("+880"): return "🇧🇩", "BD"
    if number.startswith("+91"):  return "🇮🇳", "IN"
    return "🌍", "XX"

def detect_service(msg):
    m = msg.lower()
    if "whatsapp" in m: return "WS"
    if "telegram" in m: return "TG"
    if "google" in m:   return "GG"
    return "OTP"

def main():
    print("🚀 OTP Worker started for:", RUN_EMAIL)
    while True:
        try:
            groups = load_json("groups.json", [])
            session = load_json(SESSION_FILE, {})
            cookie = session.get(RUN_EMAIL)

            if not cookie:
                print("⛔ No cookie for:", RUN_EMAIL)
                time.sleep(10)
                continue

            headers = {"Cookie": cookie, "User-Agent": "Mozilla/5.0"}
            r = requests.get(IVASMS_API_URL, headers=headers, timeout=30)

            if r.status_code != 200:
                print("❌ API Error:", r.status_code)
                time.sleep(10)
                continue

            data = r.json()  # এখানে IVASMS API অনুযায়ী পার্স করবে

            for item in data.get("messages", []):
                number = item.get("number","")
                msg = item.get("message","")
                otp = extract_otp(msg)
                if otp and otp not in seen_otps:
                    seen_otps.add(otp)
                    flag, cc = detect_tags(number)
                    svc = detect_service(msg)
                    txt = f"{flag} #{svc} #{cc}\n{number}\n\n{otp}"
                    for g in groups:
                        send(g, txt)
                    print("📩 OTP sent:", otp)

            time.sleep(POLL_INTERVAL)

        except Exception as e:
            print("❌ Worker error:", e)
            traceback.print_exc()
            time.sleep(15)

if __name__ == "__main__":
    main()
