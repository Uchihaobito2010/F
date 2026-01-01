import re
import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query

app = FastAPI()

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://fragment.com/"
}

DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

session = requests.Session()
session.headers.update(HEADERS)

# ---------------- TELEGRAM CHECK ----------------
def is_telegram_taken(username: str) -> bool:
    try:
        r = session.get(f"https://t.me/{username}", timeout=10)
        return r.status_code == 200 and "tgme_page_title" in r.text.lower()
    except:
        return False

# ---------------- FRAGMENT API (PRICE) ----------------
def fragment_api_price(username: str, retries=2):
    try:
        r = session.get("https://fragment.com", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        for script in soup.find_all("script"):
            if script.string and "apiUrl" in script.string:
                m = re.search(r"hash=([a-fA-F0-9]+)", script.string)
                if m:
                    api = f"https://fragment.com/api?hash={m.group(1)}"
                    data = {
                        "type": "usernames",
                        "query": username,
                        "method": "searchAuctions"
                    }
                    res = session.post(api, data=data, timeout=20).json()
                    html = res.get("html")
                    if not html:
                        return None

                    s = BeautifulSoup(html, "html.parser")
                    vals = s.find_all("div", class_="tm-value")
                    if len(vals) >= 2:
                        return vals[1].get_text(strip=True)

        return None
    except:
        return None

# ---------------- FRAGMENT PAGE (STATUS) ----------------
def fragment_page_status(username: str):
    url = f"https://fragment.com/username/{username}"
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return None

        html = r.text.lower()

        if "this username was sold" in html:
            return {"status": "Sold", "url": url}

        if any(x in html for x in ["buy username", "place a bid"]):
            return {"status": "Available", "url": url}

        return None
    except:
        return None

# ---------------- MAIN ENDPOINT ----------------
@app.get("/check")
async def check(user: str = Query(...)):
    username = user.replace("@", "").lower().strip()

    # 1️⃣ Fragment page (status priority)
    fragment_status = fragment_page_status(username)

    # 2️⃣ Fragment API (price best-effort)
    price = fragment_api_price(username) if fragment_status else None

    # 3️⃣ Telegram (claim logic)
    telegram_taken = is_telegram_taken(username)

    if fragment_status:
        return {
            "username": f"@{username}",
            "status": fragment_status["status"],
            "on_fragment": True,
            "price_ton": price or "Unknown",
            "can_claim": False,
            "fragment_url": fragment_status["url"],
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    if telegram_taken:
        return {
            "username": f"@{username}",
            "status": "Taken (Telegram)",
            "on_fragment": False,
            "price_ton": "Unknown",
            "can_claim": False,
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    return {
        "username": f"@{username}",
        "status": "Available",
        "on_fragment": False,
        "price_ton": "Unknown",
        "can_claim": True,
        "message": "Can be claimed directly",
        "developer": DEVELOPER,
        "channel": CHANNEL
    }
