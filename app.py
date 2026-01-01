import re
import time
import requests
from bs4 import BeautifulSoup
from user_agent import generate_user_agent
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="Fragment Username Checker API")

# ================= CREDITS =================
DEVELOPER = "Paras Chourasiya"
CONTACT = "https://t.me/Aotpy"
PORTFOLIO = "https://aotpy.vercel.app"
CHANNEL = "@obitoapi / @obitostuffs"

# ================= SESSION =================
def get_session():
    s = requests.Session()
    s.headers.update({"User-Agent": generate_user_agent()})
    return s

# ================= ROOT ( / ) =================
@app.get("/")
async def root():
    return {
        "name": "Fragment Username Checker API",
        "usage": "/check?user=username",
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL,
        "status": "running"
    }

# ================= FRAGMENT API =================
def frag_api():
    try:
        session = get_session()
        r = session.get("https://fragment.com", timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")

        for script in soup.find_all("script"):
            if script.string and "apiUrl" in script.string:
                match = re.search(r"hash=([a-fA-F0-9]+)", script.string)
                if match:
                    return f"https://fragment.com/api?hash={match.group(1)}"
        return None
    except:
        return None

def check_fgusername(username: str, retries=2):
    api_url = frag_api()
    if not api_url:
        return {"error": "Fragment API not found"}

    payload = {
        "type": "usernames",
        "query": username,
        "method": "searchAuctions"
    }

    try:
        session = get_session()
        res = session.post(api_url, data=payload, timeout=20).json()
    except:
        if retries > 0:
            time.sleep(2)
            return check_fgusername(username, retries - 1)
        return {"error": "Fragment request failed"}

    html_data = res.get("html")
    if not html_data:
        return {
            "username": f"@{username}",
            "on_fragment": False,
            "price": None,
            "status": "Not Listed",
            "can_claim": True
        }

    soup = BeautifulSoup(html_data, "html.parser")
    values = soup.find_all("div", class_="tm-value")

    if len(values) < 3:
        return {"error": "Invalid Fragment response"}

    tag = values[0].get_text(strip=True)
    price = values[1].get_text(strip=True)
    status = values[2].get_text(strip=True)

    return {
        "username": tag,
        "on_fragment": True,
        "price": price,
        "status": status,
        "can_claim": False
    }

# ================= MAIN ENDPOINT =================
@app.get("/check")
async def check(user: str = Query(..., min_length=1)):
    user = user.replace("@", "").strip().lower()
    result = check_fgusername(user)

    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    result.update({
        "developer": DEVELOPER,
        "channel": CHANNEL
    })

    return result
