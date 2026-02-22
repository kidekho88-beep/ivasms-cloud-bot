import time, json, requests

BOT_TOKEN = os.getenv("BOT_TOKEN")

def load_session():
    try:
        return json.load(open("session.json"))
    except:
        return {}

def send(chat_id, text):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id":chat_id,"text":text})

while True:
    sess = load_session()
    cookie = sess.get("cookie")

    if not cookie:
        print("⛔ No cookie set")
        time.sleep(10)
        continue

    print("🔄 Connected with cookie:", cookie[:20])

    # এখানে তুমি পরে IVASMS API কল বসাবে
    # response = requests.get("IVASMS_API_URL", headers={...})

    time.sleep(15)
