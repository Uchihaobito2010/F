from fastapi import FastAPI, Query
import requests
import re

app = FastAPI(title="Telegram Fragment Claim Check API")

# ================= CONFIG =================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://fragment.com/"
}

OWNER = "Paras Chourasiya"
CONTACT = "https://t.me/Aotpy"
CHANNEL = "@obitoapi / @obitostuffs"

# ================= TELEGRAM CHECK =================
def is_telegram_taken(username: str) -> bool:
    try:
        r = requests.get(f"https://t.me/{username}", headers=HEADERS, timeout=10)
        return r.status_code == 200 and "tgme_page_title" in r.text
    except:
        return False


# ================= FRAGMENT CHECK =================
def fragment_lookup(username: str):
    url = f"https://fragment.com/username/{username}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return {"on_fragment": False}

        html = r.text.lower()

        # ---------- SOLD ----------
        sold_signals = [
            "this username was sold",
            "sold for",
            "final price"
        ]
        if any(sig in html for sig in sold_signals):
            return {
                "on_fragment": True,
                "status": "Sold",
                "price_ton": "Unknown",
                "fragment_url": url
            }

        # ---------- PRICE (BEST EFFORT) ----------
        price = None
        price_patterns = [
            r'([\d,]{2,})\s*ton',
            r'price[^0-9]{0,10}([\d,]{2,})',
            r'([\d,]{2,})\s*tons'
        ]

        for pattern in price_patterns:
            m = re.search(pattern, html)
            if m:
                price = m.group(1).replace(",", "")
                break

        # ---------- LISTED ----------
        fragment_signals = [
            "buy username",
            "place a bid",
            "fragment marketplace"
        ]
        if any(sig in html for sig in fragment_signals):
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
        "owner": OWNER,
        "contact": CONTACT,
        "channel": CHANNEL,
        "status": "online"
    }


# ================= MAIN ENDPOINT =================
@app.get("/check")
async def check_username(user: str = Query(..., min_length=1)):
    username = user.replace("@", "").strip().lower()

    # 1️⃣ Telegram taken
    if is_telegram_taken(username):
        return {
            "username": f"@{username}",
            "on_fragment": False,
            "status": "Taken (Telegram)",
            "price_ton": "Unknown",
            "can_claim": False,
            "owner": OWNER
        }

    # 2️⃣ Fragment check
    fragment = fragment_lookup(username)

    if fragment.get("on_fragment"):
        return {
            "username": f"@{username}",
            "on_fragment": True,
            "status": fragment.get("status"),
            "price_ton": fragment.get("price_ton"),
            "can_claim": False,
            "message": "Buy from Fragment" if fragment.get("status") == "Available" else "",
            "fragment_url": fragment.get("fragment_url"),
            "owner": OWNER
        }

    # 3️⃣ Claimable
    return {
        "username": f"@{username}",
        "on_fragment": False,
        "status": "Available",
        "price_ton": "Unknown",
        "can_claim": True,
        "message": "Can be claimed directly",
        "owner": OWNER
    }
