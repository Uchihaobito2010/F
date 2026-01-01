from fastapi import FastAPI, Query
import requests
import re

app = FastAPI(title="Telegram Fragment Username Check API")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://fragment.com/"
}

DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

session = requests.Session()
session.headers.update(HEADERS)

# ---------------- TELEGRAM CHECK (AUTHORITATIVE) ----------------
def is_telegram_taken(username: str) -> bool:
    try:
        r = session.get(f"https://t.me/{username}", timeout=10)
        if r.status_code == 404:
            return False
        if r.status_code == 200:
            html = r.text.lower()
            return any(x in html for x in [
                "tgme_page_title",
                "view in telegram",
                "send message",
                "join channel",
                "og:title"
            ])
        return False
    except:
        return False


# ---------------- FRAGMENT CHECK (STRICT) ----------------
def fragment_lookup(username: str):
    """
    ONLY trust Fragment when SOLD is clearly stated.
    Ignore 'Available' listings if Telegram is taken.
    """
    url = f"https://fragment.com/username/{username}"
    try:
        r = session.get(url, timeout=15)
        if r.status_code != 200:
            return None

        html = r.text.lower()

        # TRUST ONLY SOLD SIGNALS
        if any(x in html for x in [
            "this username was sold",
            "sold for",
            "final price"
        ]):
            return {
                "status": "Sold",
                "on_fragment": True,
                "price_ton": "Unknown",
                "fragment_url": url
            }

        # AVAILABLE listing is WEAK → return but mark as listing
        if any(x in html for x in [
            "buy username",
            "place a bid",
            "fragment marketplace"
        ]):
            return {
                "status": "Available",
                "on_fragment": True,
                "price_ton": "Unknown",
                "fragment_url": url,
                "listing_only": True
            }

        return None
    except:
        return None


# ---------------- MAIN ENDPOINT ----------------
@app.get("/check")
async def check(user: str = Query(...)):
    username = user.replace("@", "").lower().strip()

    telegram_taken = is_telegram_taken(username)
    fragment = fragment_lookup(username)

    # 🔴 TELEGRAM TAKEN → AUTHORITATIVE
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

    # 🟡 FRAGMENT SOLD / LISTED
    if fragment:
        return {
            "username": f"@{username}",
            "status": fragment["status"],
            "on_fragment": True,
            "price_ton": fragment.get("price_ton", "Unknown"),
            "can_claim": False,
            "fragment_url": fragment.get("fragment_url"),
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🟢 FREE
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
