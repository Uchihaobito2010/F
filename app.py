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

# ================= TELEGRAM CHECK (ULTRA STRICT) =================def telegram_taken(username: str) -> bool:
    """
    True ONLY if a real Telegram profile/channel exists.
    Uses real action buttons as proof.
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

        # must reference the exact username
        if f"@{u}" not in html and f"t.me/{u}" not in html:
            return False

        # REAL proof: Telegram action buttons
        real_buttons = [
            'send message',
            'join channel'
        ]

        if any(btn in html for btn in real_buttons):
            return True

        # no buttons = generic / free
        return False

    except:
        return False
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

