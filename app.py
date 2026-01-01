from fastapi import FastAPI, Query
import requests
import re

app = FastAPI(title="Telegram Username Claim Checker")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}

DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

session = requests.Session()
session.headers.update(HEADERS)

# ================= TELEGRAM CHECK (STRICT & SAFE) =================
def is_telegram_taken(username: str) -> bool:
    """
    Returns True ONLY if a real Telegram profile/channel exists.
    Avoids generic placeholder false-positives.
    """
    try:
        r = session.get(
            f"https://t.me/{username}",
            timeout=10,
            allow_redirects=True
        )

        if r.status_code == 404:
            return False  # definitely free

        if r.status_code != 200:
            return False

        html = r.text.lower()
        uname = username.lower()

        # real ownership proof
        real_signals = [
            f"@{uname}",
            f"t.me/{uname}"
        ]

        page_actions = [
            "send message",
            "join channel",
            "view in telegram"
        ]

        if any(rs in html for rs in real_signals) and any(pa in html for pa in page_actions):
            return True

        return False  # generic page → treat as free

    except:
        return False


# ================= FRAGMENT CHECK (STRICT) =================
def fragment_lookup(username: str):
    """
    Fragment trusted ONLY when explicit SOLD or LISTED signals exist.
    """
    url = f"https://fragment.com/username/{username}"

    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return None

        html = r.text.lower()

        # SOLD
        if any(x in html for x in [
            "this username was sold",
            "sold for",
            "final price"
        ]):
            return {
                "status": "Sold",
                "price_ton": "Unknown",
                "url": url
            }

        # LISTED / AVAILABLE
        if any(x in html for x in [
            "buy username",
            "place a bid",
            "fragment marketplace"
        ]):
            price = None
            m = re.search(r'([\d,]{2,})\s*ton', html)
            if m:
                price = m.group(1).replace(",", "")
            return {
                "status": "Available",
                "price_ton": price or "Unknown",
                "url": url
            }

        return None

    except:
        return None


# ================= ROOT =================
@app.get("/")
async def home():
    return {
        "api": "Telegram Username Claim Checker",
        "usage": "/check?user=username",
        "developer": DEVELOPER,
        "channel": CHANNEL,
        "status": "online"
    }


# ================= MAIN ENDPOINT =================
@app.get("/check")
async def check(user: str = Query(..., min_length=1)):
    username = user.replace("@", "").lower().strip()

    telegram_taken = is_telegram_taken(username)
    fragment = fragment_lookup(username)

    # 🔴 TELEGRAM OWNED (FINAL AUTHORITY)
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

    # 🟡 FRAGMENT LISTED / SOLD
    if fragment:
        return {
            "username": f"@{username}",
            "status": fragment["status"],
            "on_fragment": True,
            "price_ton": fragment["price_ton"],
            "can_claim": False,
            "fragment_url": fragment["url"],
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🟢 FREE & CLAIMABLE
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
