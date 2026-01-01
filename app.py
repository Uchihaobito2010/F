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

# ================= ROOT =================
@app.get("/")
async def root():
    return {
        "api": "Fragment Username Checker",
        "endpoint": "/check?user=username",
        "developer": DEVELOPER,
        "contact": CONTACT,
        "portfolio": PORTFOLIO,
        "channel": CHANNEL
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

def check_fgusername(username: str, retries=3):
    api_url = frag_api()
    if not api_url:
        return {"error": f"Could not get API URL for @{username}"}

    data = {
        "type": "usernames",
        "query": username,
        "method": "searchAuctions"
    }

    try:
        session = get_session()
        response = session.post(api_url, data=data, timeout=20).json()
    except Exception:
        if retries > 0:
            time.sleep(2)
            return check_fgusername(username, retries - 1)
        return {"error": "API request failed"}

    html_data = response.get("html")
    if not html_data and retries > 0:
        time.sleep(2)
        return check_fgusername(username, retries - 1)
    elif not html_data:
        return {"error": "No HTML returned from Fragment API"}

    soup = BeautifulSoup(html_data, "html.parser")
    elements = soup.find_all("div", class_="tm-value")

    if len(elements) < 3:
        return {"error": "Not enough info in response"}

    tag = elements[0].get_text(strip=True)
    price = elements[1].get_text(strip=True)
    status = elements[2].get_text(strip=True)

    available = status.lower() == "unavailable"
    message = "✅ This username might be free or not listed on Fragment" if available else ""

    return {
        "username": tag,
        "price": price,
        "status": status,
        "available": available,
        "message": message,
        "developer": DEVELOPER,
        "channel": CHANNEL
    }

# ================= MAIN ENDPOINT =================
@app.get("/check")
async def check(user: str = Query(..., min_length=1)):
    user = user.replace("@", "").strip().lower()

    result = check_fgusername(user)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])

    return result
