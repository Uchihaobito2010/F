from fastapi import FastAPI, Query
import requests
import re

app = FastAPI(title="Telegram Username Checker")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

session = requests.Session()
session.headers.update(HEADERS)

# ---------- TELEGRAM CHECK (REAL PROFILE ONLY) ----------
def telegram_taken(username: str) -> bool:
    try:
        r = session.get(f"https://t.me/{username}", timeout=10)
        if r.status_code != 200:
            return False

        html = r.text.lower()
        uname = username.lower()

        return (
            (f"@{uname}" in html or f"t.me/{uname}" in html)
            and any(x in html for x in ["send message", "join channel", "view in telegram"])
        )
    except:
        return False


# ---------- FRAGMENT CHECK (STATUS ONLY, NO PRICE) ----------
def fragment_status(username: str):
    url = f"https://fragment.com/username/{username}"
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return None

        html = r.text.lower()

        if any(x in html for x in [
            "this username was sold",
            "buy username",
            "place a bid",
            "fragment marketplace"
        ]):
            return url

        return None
    except:
        return None


# ---------- MAIN ENDPOINT ----------
@app.get("/check")
async def check(user: str = Query(...)):
    username = user.replace("@", "").lower().strip()

    tg_taken = telegram_taken(username)
    frag_url = fragment_status(username)

    # 🔴 Telegram owned
    if tg_taken:
        return {
            "username": f"@{username}",
            "status": "Taken (Telegram)",
            "on_fragment": False,
            "can_claim": False,
            "price_ton": None,
            "note": "Telegram ownership confirmed",
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🟡 Fragment listed
    if frag_url:
        return {
            "username": f"@{username}",
            "status": "Available",
            "on_fragment": True,
            "can_claim": False,
            "price_ton": None,
            "fragment_url": frag_url,
            "note": "Fragment does not expose price publicly",
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🟢 Free
    return {
        "username": f"@{username}",
        "status": "Available",
        "on_fragment": False,
        "can_claim": True,
        "price_ton": None,
        "note": "Free and claimable",
        "developer": DEVELOPER,
        "channel": CHANNEL
    }
