import re
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query

app = FastAPI(title="Username Claim Checker")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://fragment.com/"
}

session = requests.Session()
session.headers.update(HEADERS)

DEVELOPER = "Paras Chourasiya"
CHANNEL = "@obitoapi / @obitostuffs"

# ================= FRAGMENT API ONLY =================
def fragment_api_lookup(username: str):
    try:
        r = session.get("https://fragment.com", timeout=6)
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

        payload = {
            "type": "usernames",
            "query": username,
            "method": "searchAuctions"
        }

        res = session.post(api_url, data=payload, timeout=6).json()
        html = res.get("html")
        if not html:
            return None

        soup2 = BeautifulSoup(html, "html.parser")
        vals = soup2.find_all("div", class_="tm-value")
        if len(vals) < 3:
            return None

        status = vals[2].get_text(strip=True)
        price = vals[1].get_text(strip=True)

        if status not in ["Available", "Sold"]:
            return None

        return {
            "status": status,
            "price_ton": price
        }

    except:
        return None


# ================= MAIN ENDPOINT =================
@app.get("/check")
async def check(user: str = Query(...)):
    username = user.replace("@", "").lower().strip()

    fragment = fragment_api_lookup(username)

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

    # 🟢 DEFAULT: CLAIMABLE
    return {
        "username": f"@{username}",
        "status": "Available",
        "on_fragment": False,
        "price_ton": None,
        "can_claim": True,
        "message": "Telegram availability cannot be verified publicly",
        "developer": DEVELOPER,
        "channel": CHANNEL
    }
