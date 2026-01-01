from fastapi import FastAPI, Query
import requests
import re

app = FastAPI(title="Telegram Fragment Username Check API")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://fragment.com/"
}

DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

# ---------------- TELEGRAM CHECK ----------------
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


# ---------------- FRAGMENT CHECK ----------------
def fragment_lookup(username: str):
    url = f"https://fragment.com/username/{username}"

    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
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

    # 🟡 FRAGMENT HAS PRIORITY FOR STATUS
    if fragment:
        return {
            "username": f"@{username}",
            "status": fragment.get("status"),
            "on_fragment": True,
            "price_ton": fragment.get("price_ton"),
            "can_claim": False,
            "fragment_url": fragment.get("url"),
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
