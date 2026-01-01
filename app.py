import re
import time
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Fragment Username Checker API")

# ================= CONFIG =================
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://fragment.com/"
})

DEVELOPER = "Paras Chourasiya"
CONTACT = "t.me/Aotpy"
PORTFOLIO = "https://aotpy.vercel.app"
CHANNEL = "@obitoapi / @obitostuffs"

# ================= INPUT VALIDATION =================
def validate_username(username: str):
    blocked = {
        "telegram_username",
        "username",
        "example",
        "test",
        "yourname"
    }

    if not username:
        raise HTTPException(status_code=400, detail="Username required")

    username = username.lower().strip().replace("@", "")

    if username in blocked:
        raise HTTPException(status_code=400, detail="Invalid placeholder username")

    if not re.fullmatch(r"[a-z0-9_]{5,32}", username):
        raise HTTPException(
            status_code=400,
            detail="Invalid username format"
        )

    return username

# ================= FRAGMENT API =================
def get_fragment_api():
    try:
        r = session.get("https://fragment.com", timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for s in soup.find_all("script"):
            if s.string and "apiUrl" in s.string:
                m = re.search(r"hash=([a-fA-F0-9]+)", s.string)
                if m:
                    return f"https://fragment.com/api?hash={m.group(1)}"
        return None
    except:
        return None

def fragment_check(username: str, retries=2):
    api = get_fragment_api()
    if not api:
        return None

    payload = {
        "type": "usernames",
        "query": username,
        "method": "searchAuctions"
    }

    try:
        res = session.post(api, data=payload, timeout=10).json()
        html = res.get("html")
        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        vals = soup.find_all("div", class_="tm-value")
        if len(vals) < 3:
            return None

        return {
            "username": vals[0].get_text(strip=True),
            "price_ton": vals[1].get_text(strip=True),
            "status": vals[2].get_text(strip=True)
        }

    except:
        if retries > 0:
            time.sleep(1)
            return fragment_check(username, retries - 1)
        return None

# ================= ROOT =================
@app.get("/")
async def home():
    return {
        "api": "Fragment Username Checker",
        "usage": "/check?username=tobi",
        "note": "Telegram availability is not publicly reliable",
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL
    }

# ================= MAIN ENDPOINT =================
@app.get("/check")
async def check(username: str = Query(...)):
    username = validate_username(username)

    data = fragment_check(username)
    if not data:
        raise HTTPException(status_code=500, detail="Fragment API error")

    status = data["status"].lower()

    # 🟢 NOT LISTED ON FRAGMENT
    if status == "unavailable":
        return {
            "username": f"@{username}",
            "status": "Available",
            "on_fragment": False,
            "price_ton": None,
            "can_claim": True,
            "message": "Not listed on Fragment",
            "developer": DEVELOPER,
            "contact": CONTACT,
            "portfolio": PORTFOLIO,
            "channel": CHANNEL
        }

    # 🔴 LISTED / SOLD
    return {
        "username": data["username"],
        "status": data["status"],
        "on_fragment": True,
        "price_ton": data["price_ton"],
        "can_claim": False,
        "message": "Listed on Fragment",
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL
    }
