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

# ================= TELEGRAM CHECK (CLAIM ONLY) =================
def telegram_taken(username: str) -> bool:
    """
    True only if a real Telegram profile/channel exists.
    """
    try:
        r = session.get(f"https://t.me/{username}", timeout=10, allow_redirects=True)
        if r.status_code != 200:
            return False

        html = r.text.lower()
        u = username.lower()

        return (
            (f"@{u}" in html or f"t.me/{u}" in html)
            and any(x in html for x in ["send message", "join channel", "view in telegram"])
        )
    except:
        return False


# ================= FRAGMENT API (ONLY SOURCE OF TRUTH) =================
def fragment_api_lookup(username: str, retries=2):
    """
    Uses Fragment internal API.
    Returns None if username is NOT on Fragment.
    """
    try:
        # get API hash
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

        data = {
            "type": "usernames",
            "query": username,
            "method": "searchAuctions"
        }

        res = session.post(api_url, data=data, timeout=20).json()
        html = res.get("html")

        if not html:
            return None

        soup2 = BeautifulSoup(html, "html.parser")
        vals = soup2.find_all("div", class_="tm-value")

        # Expect: username | price | status
        if len(vals) < 3:
            return None

        return {
            "status": vals[2].get_text(strip=True),
            "price_ton": vals[1].get_text(strip=True)
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

    # 🔵 FRAGMENT LISTED / SOLD (HIGHEST PRIORITY)
    if fragment:
        return {
            "username": f"@{username}",
            "status": fragment["status"],
            "on_fragment": True,
            "price_ton": fragment["price_ton"] or None,
            "can_claim": False,
            "fragment_url": f"https://fragment.com/username/{username}",
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🔴 TELEGRAM OWNED
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
