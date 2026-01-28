import re
import time
import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from fastapi import FastAPI, HTTPException, Query

app = FastAPI()

session = requests.Session()
session.headers.update({"User-Agent": generate_user_agent()})

DEVELOPER = "Paras"
CHANNEL = "@obitoapi / @obitostuffs"


# 🔹 Fragment internal API finder
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


# 🔹 TON + USD + INR extractor (friend logic adapted)
def ton_usd_inr(username: str):
    try:
        r = session.get(
            f"https://fragment.com/username/{username}",
            timeout=10
        )
        soup = BeautifulSoup(r.text, "html.parser")

        ton = None
        usd = None

        ton_tag = soup.find("div", class_="table-cell-value")
        if ton_tag:
            ton = ton_tag.text.replace(",", "").strip()

        bid_input = soup.find("input", {"name": "bid_value"})
        if not ton and bid_input:
            ton = bid_input.get("value")

        usd_tag = soup.find("div", class_="table-cell-desc")
        if usd_tag:
            usd = usd_tag.text.replace("~", "").replace("$", "").replace(",", "").strip()

        if ton and not usd:
            rate = re.search(r'"tonRate":([0-9.]+)', r.text)
            if rate:
                usd = round(float(ton) * float(rate.group(1)), 2)

        inr = None
        if usd:
            fx = session.get("https://api.exchangerate-api.com/v4/latest/USD").json()
            inr = round(float(usd) * fx["rates"]["INR"], 2)

        return ton, usd, inr

    except:
        return None, None, None


# 🔹 MAIN CHECK FUNCTION
def check_fgusername(username: str, retries=3):
    api_url = frag_api()
    if not api_url:
        return {"error": "Fragment API not found"}

    data = {"type": "usernames", "query": username, "method": "searchAuctions"}

    try:
        response = session.post(api_url, data=data, timeout=10).json()
    except:
        if retries > 0:
            time.sleep(2)
            return check_fgusername(username, retries - 1)
        return {"error": "API request failed"}

    html_data = response.get("html")
    if not html_data:
        return {"error": "No HTML returned"}

    soup = BeautifulSoup(html_data, "html.parser")
    elements = soup.find_all("div", class_="tm-value")

    if len(elements) < 3:
        return {"error": "Invalid response"}

    tag = elements[0].get_text(strip=True)
    price = elements[1].get_text(strip=True)
    status = elements[2].get_text(strip=True)

    available = status.lower() == "unavailable"
    message = "✅ This username might be free or not listed on Fragment" if available else ""

    ton, usd, inr = ton_usd_inr(username)

    return {
        "username": tag,
        "Price_TON": price,
        "₹inr": f"₹ {inr}" if inr else "N/A",
        "$usd": f"$ {usd}" if usd else "N/A",
        "status": status,
        "Can Claim": available,
        "message": message,
        "developer": DEVELOPER,
        "channel": CHANNEL
    }


# 🔹 FASTAPI ENDPOINT
@app.get("/check")
async def check_username(username: str = Query(..., min_length=1)):
    username = username.strip().lower().replace("@", "")
    result = check_fgusername(username)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result


