from fastapi import FastAPI, Query
import requests
import re

app = FastAPI(title="Telegram Fragment Username Check API")

# ================= CONFIG =================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://fragment.com/"
}

DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

# ================= TELEGRAM CHECK =================
def is_telegram_taken(username: str) -> bool:
    try:
        r = requests.get(
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
            return any(sig in html for sig in signals)

        return False
    except:
        return False


# ================= FRAGMENT PAGE CHECK =================
def fragment_lookup(username: str):
    url = f"https://fragment.com/username/{username}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return {"on_fragment": False}

        html = r.text.lower()

        # ---- SOLD ----
        if any(s in html for s in ["this username was sold", "sold for", "final price"]):
            return {
                "on_fragment": True,
                "status": "Sold",
                "price_ton": "Unknown",
                "fragment_url": url
            }

        # ---- PRICE ----
        price = None
        m = re.search(r'([\d,]{2,})\s*ton', html)
        if m:
            price = m.group(1).replace(",", "")

        # ---- LISTED ----
        if any(s in html for s in ["buy username", "place a bid", "fragment marketplace"]):
            return {
                "on_fragment": True,
                "status": "Available",
                "price_ton": price or "Unknown",
                "fragment_url": url
            }

        return {"on_fragment": False}

    except:
        return {"on_fragment": False}


# ================= ROOT =================
@app.get("/")
async def home():
    return {
        "api": "Telegram Username Claim Check API",
        "usage": "/check?user=username",
        "developer": DEVELOPER,
        "channel": CHANNEL,
        "status": "online"
    }


# ================= MAIN ENDPOINT =================
@app.get("/check")
async def check_username(user: str = Query(..., min_length=1)):
    username = user.replace("@", "").strip().lower()

    telegram_taken = is_telegram_taken(username)
    fragment = fragment_lookup(username)

    # 🔴 Telegram taken
    if telegram_taken:
        return {
            "username": f"@{username}",
            "status": "Taken (Telegram)",
            "on_fragment": True if fragment.get("on_fragment") else False,
            "price_ton": fragment.get("price_ton", "Unknown") if fragment.get("on_fragment") else "Unknown",
            "can_claim": False,
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🟡 Fragment listed / sold
    if fragment.get("on_fragment"):
        return {
            "username": f"@{username}",
            "status": fragment.get("status"),
            "on_fragment": True,
            "price_ton": fragment.get("price_ton"),
            "can_claim": False,
            "message": "Buy from Fragment" if fragment.get("status") == "Available" else "",
            "fragment_url": fragment.get("fragment_url"),
            "developer": DEVELOPER,
            "channel": CHANNEL
        }

    # 🟢 Free & claimable
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
