import re
import time
import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from fastapi import FastAPI, HTTPException, Query

app = FastAPI()

# ================= SESSION =================
session = requests.Session()
session.headers.update({"User-Agent": generate_user_agent()})

# ================= CREDITS =================
DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

HEADERS = {
    "User-Agent": generate_user_agent(),
    "Referer": "https://fragment.com/"
}

# ================= TELEGRAM CHECK =================
def is_telegram_taken(username: str) -> bool:
    try:
        r = session.get(
            f"https://t.me/{username}",
            headers=HEADERS,
            timeout=10,
            allow_redirects=True
        )

        if r.status_code == 404:
            return False

        if r.status_code == 200:
            html = r.text.lower()
            signals = [
                "tgme_page_title",
                "view in telegram",
                "send message",
                "join channel",
                "og:title"
            ]
            if any(sig in html for sig in signals):
                return True

        return False
    except:
        return False

# ================= FRAGMENT API =================
def frag_api():
    try:
        r = session.get("https://fragment.com", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        for script in soup.find_all("script"):
            if script.string and "apiurl" in script.string.lower():
                match = re.search(r"hash=([a-fA-F0-9]+)", script.string)
                if match:
                    return f"https://fragment.com/api?hash={match.group(1)}"
        return None
    except:
        return None

def fragment_api_lookup(username: str, retries=3):
    api_url = frag_api()
    if not api_url:
        return {"on_fragment": False}

    data = {
        "type": "usernames",
        "query": username,
        "method": "searchAuctions"
    }

    try:
        res = session.post(api_url, data=data, timeout=20).json()
    except:
        if retries > 0:
            time.sleep(2)
            return fragment_api_lookup(username, retries - 1)
        return {"on_fragment": False}

    html_data = res.get("html")
    if not html_data:
        return {"on_fragment": False}

    soup = BeautifulSoup(html_data, "html.parser")
    values = soup.find_all("div", class_="tm-value")

    if len(values) < 3:
        return {"on_fragment": False}

    tag = values[0].get_text(strip=True)
    price_raw = values[1].get_text(strip=True)
    status_raw = values[2].get_text(strip=True)

    # normalize
    status = status_raw.capitalize()
    price = price_raw if price_raw else "Unknown"

    return {
        "on_fragment": True,
        "username": tag,
        "price_ton": price,
        "status": status
    }

# ================= MAIN ENDPOINT =================
@app.get("/check")
async def check_username(user: str = Query(..., min_length=1)):
    username = user.replace("@", "").lower().strip()

    # 1️⃣ Telegram check
    telegram_taken = is_telegram_taken(username)

    # 2️⃣ Fragment API check
    fragment = fragment_api_lookup(username)

    # ---------- CASE A: Telegram already taken ----------
    if telegram_taken:
        return {
            "username": f"@{username}",
            "status": "Taken (Telegram)",
            "price_ton": fragment.get("price_ton", "Unknown"),
            "on_fragment": fragment.get("on_fragment", False),
            "can_claim": False,
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # ---------- CASE B: On Fragment ----------
    if fragment.get("on_fragment"):
        return {
            "username": fragment.get("username", f"@{username}"),
            "status": fragment.get("status"),
            "price_ton": fragment.get("price_ton"),
            "on_fragment": True,
            "can_claim": False,
            "message": "Buy from Fragment",
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # ---------- CASE C: Free & Claimable ----------
    return {
        "username": f"@{username}",
        "status": "Available",
        "price_ton": "Unknown",
        "on_fragment": False,
        "can_claim": True,
        "message": "Can be claimed directly",
        "developer": DEVELOPER,
        "channel": CHANNEL
    }
