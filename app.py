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

# ================= FRAGMENT API URL =================
def get_fragment_api():
    try:
        r = session.get("https://fragment.com", timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for script in soup.find_all("script"):
            if script.string and "apiUrl" in script.string:
                m = re.search(r"hash=([a-fA-F0-9]+)", script.string)
                if m:
                    return f"https://fragment.com/api?hash={m.group(1)}"
        return None
    except:
        return None


# ================= FRAGMENT CHECK =================
def fragment_check(username: str, retries=2):
    api_url = get_fragment_api()
    if not api_url:
        return None

    payload = {
        "type": "usernames",
        "query": username,
        "method": "searchAuctions"
    }

    try:
        res = session.post(api_url, data=payload, timeout=10).json()
        html = res.get("html")

        if not html:
            return None

        soup = BeautifulSoup(html, "html.parser")
        values = soup.find_all("div", class_="tm-value")

        if len(values) < 3:
            return None

        return {
            "username": values[0].get_text(strip=True),
            "price_ton": values[1].get_text(strip=True),
            "status": values[2].get_text(strip=True)
        }

    except:
        if retries > 0:
            time.sleep(1)
            return fragment_check(username, retries - 1)
        return None


# ================= MAIN ENDPOINT =================
@app.get("/check")
async def check_username(username: str = Query(..., min_length=1)):
    username = username.strip().lower().replace("@", "")

    data = fragment_check(username)
    if not data:
        raise HTTPException(status_code=500, detail="Fragment API error")

    status = data["status"].lower()

    # 🟢 NOT LISTED = FREE
    if status == "unavailable":
        return {
            "username": f"@{username}",
            "status": "Available",
            "on_fragment": False,
            "price_ton": None,
            "can_claim": True,
            "message": "Can be claimed directly",
            "developer": DEVELOPER,
            "contact": CONTACT,
            "portfolio": PORTFOLIO,
            "channel": CHANNEL
        }

    # 🔴 LISTED OR SOLD ON FRAGMENT
    return {
        "username": data["username"],
        "status": data["status"],
        "on_fragment": True,
        "price_ton": data["price_ton"],
        "can_claim": False,
        "message": "Buy from Fragment" if data["status"] == "Available" else "Already sold",
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL
    }
