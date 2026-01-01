from fastapi import FastAPI, Query
import requests
import re

app = FastAPI(title="Telegram Fragment Username Checker")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}

DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

session = requests.Session()
session.headers.update(HEADERS)

# ---------------- TELEGRAM CHECK (CLAIM ONLY) ----------------
def is_telegram_taken(username: str) -> bool:
    try:
        r = session.get(f"https://t.me/{username}", timeout=10)
        if r.status_code == 404:
            return False

        if r.status_code == 200:
            html = r.text.lower()
            uname = username.lower()
            return (
                (f"@{uname}" in html or f"t.me/{uname}" in html)
                and any(x in html for x in ["send message", "join channel", "view in telegram"])
            )
        return False
    except:
        return False


# ---------------- FRAGMENT CHECK (STATUS AUTHORITY) ----------------
def fragment_lookup(username: str):
    url = f"https://fragment.com/username/{username}"
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return None

        html = r.text.lower()

        # SOLD
        if any(x in html for x in ["this username was sold", "sold for", "final price"]):
            return {
                "status": "Sold",
                "price_ton": "Unknown",
                "url": url
            }

        # AVAILABLE / LISTED
        if any(x in html for x in ["buy username", "place a bid", "fragment marketplace"]):
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


# ---------------- MAIN ENDPOINT ----------------
@app.get("/check")
async def check(user: str = Query(...)):
    username = user.replace("@", "").lower().strip()

    fragment = fragment_lookup(username)
    telegram_taken = is_telegram_taken(username)

    # 🟡 FRAGMENT DECIDES STATUS
    if fragment:
        return {
            "username": f"@{username}",
            "status": fragment["status"],
            "on_fragment": True,
            "price_ton": fragment["price_ton"],
            "can_claim": False,   # fragment listing/sold ⇒ cannot claim
            "fragment_url": fragment["url"],
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🔴 TELEGRAM TAKEN (NO FRAGMENT)
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
