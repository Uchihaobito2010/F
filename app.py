import re
import time
import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from fastapi import FastAPI, Query

app = FastAPI(title="Telegram Fragment Username Checker")

# ================= CONFIG =================
session = requests.Session()
session.headers.update({"User-Agent": generate_user_agent()})

DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

# ================= TELEGRAM (CLAIM ONLY) =================
def telegram_taken(username: str) -> bool:
    """
    True only if a real Telegram profile exists.
    Avoids placeholder false-positives.
    """
    try:
        r = session.get(f"https://t.me/{username}", timeout=10, allow_redirects=True)
        if r.status_code != 200:
            return False
        html = r.text.lower()
        u = username.lower()
        return (
            (f"@{u}" in html or f"t.me/{u}" in html) and
            any(x in html for x in ["send message", "join channel", "view in telegram"])
        )
    except:
        return False

# ================= FRAGMENT PAGE (STATUS) =================
def fragment_page_status(username: str):
    """
    Returns dict if Fragment clearly lists/sold the username.
    """
    url = f"https://fragment.com/username/{username}"
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return None
        html = r.text.lower()

        if any(x in html for x in ["this username was sold", "sold for", "final price"]):
            return {"status": "Sold", "url": url}

        if any(x in html for x in ["buy username", "place a bid", "fragment marketplace"]):
            return {"status": "Available", "url": url}

        return None
    except:
        return None

# ================= FRAGMENT API (PRICE – BEST EFFORT) =================
def fragment_api_price(username: str, retries=2):
    """
    Tries Fragment internal API to fetch price if exposed.
    May return None (normal).
    """
    try:
        r = session.get("https://fragment.com", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        api = None
        for s in soup.find_all("script"):
            if s.string and "apiUrl" in s.string:
                m = re.search(r"hash=([a-fA-F0-9]+)", s.string)
                if m:
                    api = f"https://fragment.com/api?hash={m.group(1)}"
                    break
        if not api:
            return None

        data = {"type": "usernames", "query": username, "method": "searchAuctions"}
        res = session.post(api, data=data, timeout=20).json()
        html = res.get("html")
        if not html:
            return None

        s2 = BeautifulSoup(html, "html.parser")
        vals = s2.find_all("div", class_="tm-value")
        if len(vals) >= 2:
            return vals[1].get_text(strip=True)
        return None
    except:
        if retries > 0:
            time.sleep(1)
            return fragment_api_price(username, retries - 1)
        return None

# ================= ENDPOINT =================
@app.get("/check")
async def check(user: str = Query(..., min_length=1)):
    username = user.replace("@", "").lower().strip()

    frag = fragment_page_status(username)
    tg_taken = telegram_taken(username)

    # 🔵 FRAGMENT DECIDES STATUS
    if frag:
        price = fragment_api_price(username)
        return {
            "username": f"@{username}",
            "status": frag["status"],
            "on_fragment": True,
            "price_ton": price,   # may be null (normal)
            "can_claim": False,   # fragment listing/sold → cannot claim
            "fragment_url": frag["url"],
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🔴 TELEGRAM DECIDES CLAIM
    if tg_taken:
        return {
            "username": f"@{username}",
            "status": "Taken (Telegram)",
            "on_fragment": False,
            "price_ton": None,
            "can_claim": False,
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🟢 FREE
    return {
        "username": f"@{username}",
        "status": "Available",
        "on_fragment": False,
        "price_ton": None,
        "can_claim": True,
        "message": "Can be claimed directly",
        "developer": DEVELOPER,
        "channel": CHANNEL
    }
