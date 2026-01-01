import re
import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
from user_agent import generate_user_agent

app = FastAPI(title="Telegram Fragment Username Checker")

# ================= CONFIG =================
session = requests.Session()
session.headers.update({
    "User-Agent": generate_user_agent(),
    "Referer": "https://fragment.com/"
})

DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

# ================= TELEGRAM CHECK (ULTRA STRICT) =================
def telegram_taken(username: str) -> bool:
    """
    True ONLY if Telegram profile/channel REALLY exists.
    Uses og:title meta tag as final proof.
    """
    try:
        r = session.get(
            f"https://t.me/{username}",
            timeout=10,
            allow_redirects=True
        )

        if r.status_code != 200:
            return False

        html = r.text.lower()
        u = username.lower()

        # must contain username reference
        if f"@{u}" not in html and f"t.me/{u}" not in html:
            return False

        # strong proof: og:title exists
        if 'property="og:title"' in html:
            return True

        return False

    except:
        return False


# ================= FRAGMENT API CHECK =================
def fragment_api_lookup(username: str, retries=2):
    """
    Uses Fragment INTERNAL API.
    Returns dict only if username is LISTED or SOLD.
    """
    try:
        r = session.get("https://fragment.com", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        api_url = None
        for s in soup.find_all("script"):
            if s.string and "apiUrl" in s.string:
                m = re.search(r"hash=([a-fA-F0-9]+)", s.string)
                if m:
                    api_url = f"https://fragment.com/api?hash={m.group(1)}"
                    break

        if not api_url:
            return None

        payload = {
            "type": "usernames",
            "query": username,
            "method": "searchAuctions"
        }

        res = session.post(api_url, data=payload, timeout=20).json()
        html = res.get("html")
        if not html:
            return None

        soup2 = BeautifulSoup(html, "html.parser")
        values = soup2.find_all("div", class_="tm-value")

        if len(values) < 3:
            return None

        status = values[2].get_text(strip=True)
        price = values[1].get_text(strip=True)

        # ONLY valid Fragment states
        if status not in ["Available", "Sold"]:
            return None

        return {
            "status": status,
            "price_ton": price
        }

    except:
        if retries > 0:
            time.sleep(1)
            return fragment_api_lookup(username, retries - 1)
        return None


# ================= MAIN ENDPOINT =================
@app.get("/check")
async def check(user: str = Query(..., min_length=1)):
    username = user.replace("@", "").lower().strip()

    fragment = fragment_api_lookup(username)
    tg_taken = telegram_taken(username)

    # 🔵 FRAGMENT LISTED / SOLD
    if fragment:
        return {
            "username": f"@{username}",
            "status": fragment["status"],
            "on_fragment": True,
            "price_ton": fragment["price_ton"],
            "can_claim": False,
            "fragment_url": f"https://fragment.com/username/{username}",
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🔴 TELEGRAM REAL PROFILE
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

    # 🟢 FREE & CLAIMABLE
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
