import re
import time
import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from fastapi import FastAPI, HTTPException, Query

app = FastAPI()

session = requests.Session()
session.headers.update({"User-Agent": generate_user_agent()})

DEVELOPER = "@Aotpy"
CHANNEL = "@obitoapi / @obitostuffs"

USD_TO_INR = 83.0

def frag_api():
    try:
        r = session.get("https://fragment.com", timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for script in soup.find_all("script"):
            if script.string and "apiUrl" in script.string:
                match = re.search(r'hash=([a-fA-F0-9]+)', script.string)
                if match:
                    return f"https://fragment.com/api?hash={match.group(1)}"
        return None
    except:
        return None

def get_ton_usd_inr(username: str):
    try:
        r = session.get(
            f"https://fragment.com/username/{username}",
            timeout=10
        )

        soup = BeautifulSoup(r.text, "html.parser")

        ton = None

        ton_tag = soup.find("div", class_="table-cell-value")
        if ton_tag:
            ton = ton_tag.text.replace(",", "").strip()

        bid_input = soup.find("input", {"name": "bid_value"})
        if not ton and bid_input:
            ton = bid_input.get("value")

        if not ton:
            return None, None, None

        ton = float(ton)

        rate_match = re.search(r'"tonRate":([0-9.]+)', r.text)
        if not rate_match:
            return ton, None, None

        ton_rate_usd = float(rate_match.group(1))

        usd = round(ton * ton_rate_usd, 2)
        inr = round(usd * USD_TO_INR, 2)

        return ton, usd, inr

    except:
        return None, None, None

def check_fgusername(username: str, retries=3):
    api_url = frag_api()
    if not api_url:
        return {"error": "Fragment API not found"}

    payload = {
        "type": "usernames",
        "query": username,
        "method": "searchAuctions"
    }

    try:
        res = session.post(api_url, data=payload, timeout=10).json()
    except:
        if retries > 0:
            time.sleep(2)
            return check_fgusername(username, retries - 1)
        return {"error": "Fragment API request failed"}

    html = res.get("html")
    if not html:
        return {"error": "No HTML returned from Fragment"}

    soup = BeautifulSoup(html, "html.parser")
    values = soup.find_all("div", class_="tm-value")

    if len(values) < 3:
        return {"error": "Invalid Fragment response"}

    tag = values[0].get_text(strip=True)
    price_ton = values[1].get_text(strip=True)
    status = values[2].get_text(strip=True)

    can_claim = status.lower() == "unavailable"
    message = "✅ Claim This Username it's free 💕🗿🥀. if u Can't able to Claim This Username so surely it's from Frozen account Try to claim it👍" if can_claim else ""

    ton, usd, inr = get_ton_usd_inr(username)

    return {
        "username": tag,
        "Price_TON": price_ton,
        "₹inr": f"₹ {inr}" if inr else "N/A",
        "$usd": f"$ {usd}" if usd else "N/A",
        "status": status,
        "Can Claim": can_claim,
        "message": message,
        "developer": DEVELOPER,
        "channel": CHANNEL
    }

@app.get("/check")
async def check_username(username: str = Query(..., min_length=1)):
    username = username.strip().lower().replace("@", "")
    result = check_fgusername(username)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result
