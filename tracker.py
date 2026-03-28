import json
import re
import time
import random
import string
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import threading

import requests

DATA_FILE  = "alerts.json"
USERS_FILE = "users.json"
DEALS_FILE = "deals.json"
TINYFISH_ENDPOINT = "https://agent.tinyfish.ai/v1/automation/run-sse"

# ─────────────────────────────────────────────────────────────────
# In-memory price + product cache (TTL = 5 min)
# ─────────────────────────────────────────────────────────────────

_CACHE: dict = {}
_CACHE_LOCK = threading.Lock()
CACHE_TTL = 300  # seconds


def _cache_get(key: str):
    with _CACHE_LOCK:
        entry = _CACHE.get(key)
        if entry and (time.time() - entry["ts"]) < CACHE_TTL:
            return entry["val"]
    return None


def _cache_set(key: str, val):
    with _CACHE_LOCK:
        _CACHE[key] = {"val": val, "ts": time.time()}


# ─────────────────────────────────────────────────────────────────
# JSON Storage Helpers  (file-level lock for write safety)
# ─────────────────────────────────────────────────────────────────

_FILE_LOCK = threading.Lock()


def _load(path):
    if not Path(path).exists():
        return []
    with open(path, "r") as f:
        return json.load(f)


def _save(path, data):
    with _FILE_LOCK:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


def load_alerts():  return _load(DATA_FILE)
def save_alerts(d): _save(DATA_FILE, d)
def load_users():   return _load(USERS_FILE)
def save_users(d):  _save(USERS_FILE, d)
def load_deals():   return _load(DEALS_FILE)
def save_deals(d):  _save(DEALS_FILE, d)


# ─────────────────────────────────────────────────────────────────
# User / Auth helpers
# ─────────────────────────────────────────────────────────────────

def get_user(phone: str):
    for u in load_users():
        if u["phone"] == phone:
            return u
    return None


def upsert_user(phone: str, **kwargs):
    users = load_users()
    for u in users:
        if u["phone"] == phone:
            u.update(kwargs)
            save_users(users)
            return u
    new_user = {"phone": phone, "created_at": datetime.now().isoformat(), **kwargs}
    users.append(new_user)
    save_users(users)
    return new_user


# ─────────────────────────────────────────────────────────────────
# Alert helpers
# ─────────────────────────────────────────────────────────────────

def load_alerts_for(phone: str):
    return [a for a in load_alerts() if a.get("phone") == phone]


def add_alert(phone, url, site, min_price, max_price):
    alerts = load_alerts()
    alert = {
        "id": str(int(time.time())),
        "phone": phone,
        "url": url,
        "site": site,
        "min_price": float(min_price),
        "max_price": float(max_price),
        "current_price": None,
        "in_cart": False,
        "cart_added_at": None,
        "price_history": [],
        "created_at": datetime.now().isoformat(),
    }
    alerts.append(alert)
    save_alerts(alerts)
    return alert


def remove_alert(alert_id):
    save_alerts([a for a in load_alerts() if a["id"] != alert_id])


def update_alert(alert_id, **kwargs):
    alerts = load_alerts()
    for a in alerts:
        if a["id"] == alert_id:
            a.update(kwargs)
    save_alerts(alerts)


def check_cart_expiry(alert):
    if not alert.get("in_cart") or not alert.get("cart_added_at"):
        return False
    added = datetime.fromisoformat(alert["cart_added_at"])
    return datetime.now() > added + timedelta(days=7)


def days_left_in_cart(alert):
    if not alert.get("in_cart") or not alert.get("cart_added_at"):
        return None
    added = datetime.fromisoformat(alert["cart_added_at"])
    delta = (added + timedelta(days=7)) - datetime.now()
    return max(0, delta.days)


# ─────────────────────────────────────────────────────────────────
# TinyFish core runner  – connect timeout 10s, read timeout 90s
# ─────────────────────────────────────────────────────────────────

def _run_tinyfish(goal: str, url: str, api_key: str, timeout: int = 90) -> str:
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    payload = {"url": url, "goal": goal, "proxy_config": {"enabled": False}}
    result_text = ""
    try:
        with requests.post(
            TINYFISH_ENDPOINT, headers=headers, json=payload,
            stream=True, timeout=(10, timeout)   # (connect, read)
        ) as resp:
            resp.raise_for_status()
            for raw in resp.iter_lines(chunk_size=4096):
                if not raw:
                    continue
                line = raw.decode("utf-8") if isinstance(raw, bytes) else raw
                if line.startswith("data:"):
                    ds = line[5:].strip()
                    if ds in ("[DONE]", ""):
                        continue
                    try:
                        chunk = json.loads(ds)
                        for f in ("result", "message", "content", "text", "answer"):
                            if chunk.get(f):
                                result_text = str(chunk[f])
                    except json.JSONDecodeError:
                        result_text = ds
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"TinyFish API error: {e}")
    return result_text


def _extract_json(text: str) -> dict:
    m = re.search(r'\{.*?\}', text, re.DOTALL)
    if m:
        return json.loads(m.group())
    raise ValueError(f"No JSON in: {text!r}")


# ─────────────────────────────────────────────────────────────────
# TinyFish — Price scraping  (with TTL cache)
# ─────────────────────────────────────────────────────────────────

def get_price_with_tinyfish(url: str, api_key: str):
    cached = _cache_get(f"price:{url}")
    if cached is not None:
        return cached

    goal = (
        "Visit this product page and find the current selling price. "
        "Return ONLY JSON: {\"price\": 1234.00} "
        "Use a plain number, no currency symbols or commas. "
        "If price not found return {\"price\": null}"
    )
    try:
        result = _run_tinyfish(goal, url, api_key)
        data = _extract_json(result)
        p = data.get("price")
        price = float(p) if p is not None else None
        _cache_set(f"price:{url}", price)
        return price
    except Exception as e:
        print(f"[get_price] {e}")
        return None


# ─────────────────────────────────────────────────────────────────
# TinyFish — Product info scraping  (with TTL cache)
# ─────────────────────────────────────────────────────────────────

def get_product_info_with_tinyfish(url: str, api_key: str) -> dict:
    cached = _cache_get(f"info:{url}")
    if cached is not None:
        return cached

    goal = (
        "Visit this product page and extract: product name, current price, "
        "main product image URL, and the website/store name. "
        "Return ONLY JSON: "
        "{\"name\": \"...\", \"price\": 1234.00, \"image\": \"https://...\", \"store\": \"...\"} "
        "Price must be a plain number. If any field is unavailable use null."
    )
    try:
        result = _run_tinyfish(goal, url, api_key)
        info = _extract_json(result)
        _cache_set(f"info:{url}", info)
        return info
    except Exception as e:
        print(f"[get_product_info] {e}")
        return {}


# ─────────────────────────────────────────────────────────────────
# TinyFish — Login
# ─────────────────────────────────────────────────────────────────

SITE_LOGIN_URLS = {
    "Amazon":   "https://www.amazon.in/ap/signin",
    "Flipkart": "https://www.flipkart.com/account/login",
    "Myntra":   "https://www.myntra.com/login",
    "Meesho":   "https://www.meesho.com/login",
    "Nykaa":    "https://www.nykaa.com/login",
    "Snapdeal": "https://www.snapdeal.com/login",
    "Ajio":     "https://www.ajio.com/s/login-503012",
    "Other":    "",
}


def login_with_tinyfish(site: str, email: str, password: str, api_key: str, login_url: str = ""):
    url = login_url or SITE_LOGIN_URLS.get(site, "")
    if not url:
        return False, "", f"No login URL found for {site}"
    goal = (
        f"Go to the login page of {site}. "
        f"Log in using email or username '{email}' and password '{password}'. "
        "Wait until login is complete and the home/account page loads. "
        "Return ONLY JSON: {\"success\": true} or {\"success\": false, \"reason\": \"...\"}"
    )
    try:
        result = _run_tinyfish(goal, url, api_key, timeout=120)
        data = _extract_json(result)
        success = bool(data.get("success", False))
        token = str(data.get("session_id") or data.get("profile_id") or "active")
        return success, token, data.get("reason", "")
    except Exception as e:
        return False, "", str(e)


# ─────────────────────────────────────────────────────────────────
# TinyFish — Add to cart
# ─────────────────────────────────────────────────────────────────

def add_to_cart_with_tinyfish(url: str, site: str, api_key: str):
    goal = (
        f"I am already logged in to {site}. "
        "Go to this product page and click 'Add to Cart' or 'Buy Now'. "
        "Confirm whether the item was successfully added. "
        "Return ONLY JSON: {\"success\": true} or {\"success\": false, \"reason\": \"...\"}"
    )
    try:
        result = _run_tinyfish(goal, url, api_key, timeout=120)
        data = _extract_json(result)
        return bool(data.get("success", False)), data.get("reason", "")
    except Exception as e:
        return False, str(e)


# ─────────────────────────────────────────────────────────────────
# TinyFish — Scrape top deals  (PARALLEL across sites)
# ─────────────────────────────────────────────────────────────────

def _scrape_one_site(site_url: str, api_key: str, max_deals: int) -> list:
    goal = (
        f"Visit this shopping site and find the top {max_deals} products "
        "with the biggest discounts or price drops shown on the page. "
        "For each product return: name, current price (number), original price (number), "
        "discount percentage (number), product URL, image URL, store name. "
        "Return ONLY a JSON array: "
        "[{\"name\":\"...\",\"price\":999,\"original_price\":1999,"
        "\"discount_pct\":50,\"url\":\"https://...\",\"image\":\"https://...\",\"store\":\"...\"}]"
        " If a field is unavailable use null."
    )
    try:
        result = _run_tinyfish(goal, site_url, api_key, timeout=150)
        m = re.search(r'\[.*?\]', result, re.DOTALL)
        if m:
            deals = json.loads(m.group())
            return deals[:max_deals]
    except Exception as e:
        print(f"[scrape_deals] {site_url}: {e}")
    return []


def scrape_deals_with_tinyfish(site_url: str, api_key: str, max_deals: int = 4) -> list:
    """Single-site scrape (kept for backward compat)."""
    return _scrape_one_site(site_url, api_key, max_deals)


def scrape_deals_parallel(site_map: dict, api_key: str, max_deals: int = 3) -> list:
    """
    Scrape multiple sites IN PARALLEL.
    site_map = {"Amazon.in": "https://...", "Flipkart": "https://..."}
    Returns combined list sorted by discount.
    """
    all_deals = []

    def _fetch(name, url):
        deals = _scrape_one_site(url, api_key, max_deals)
        for d in deals:
            d["store"] = d.get("store") or name
        return deals

    with ThreadPoolExecutor(max_workers=min(len(site_map), 5)) as ex:
        futures = {ex.submit(_fetch, name, url): name for name, url in site_map.items()}
        for future in as_completed(futures):
            try:
                all_deals.extend(future.result())
            except Exception as e:
                print(f"[parallel_deals] {futures[future]}: {e}")

    # Sort by discount descending
    all_deals.sort(key=lambda d: d.get("discount_pct") or 0, reverse=True)
    return all_deals


# ─────────────────────────────────────────────────────────────────
# OTP helpers
# ─────────────────────────────────────────────────────────────────

_OTP_STORE: dict = {}


def generate_otp(phone: str) -> str:
    otp = "".join(random.choices(string.digits, k=6))
    _OTP_STORE[phone] = {"otp": otp, "expires": datetime.now() + timedelta(minutes=5)}
    return otp


def verify_otp(phone: str, otp: str) -> bool:
    record = _OTP_STORE.get(phone)
    if not record:
        return False
    if datetime.now() > record["expires"]:
        return False
    return record["otp"] == otp.strip()


# ─────────────────────────────────────────────────────────────────
# Twilio SMS helpers
# ─────────────────────────────────────────────────────────────────

def send_sms_otp(phone, otp, twilio_sid, twilio_token, twilio_phone) -> bool:
    try:
        from twilio.rest import Client
        Client(twilio_sid, twilio_token).messages.create(
            from_=twilio_phone, to=phone,
            body=f"Your CARTSYNCZ code: {otp}\nValid 5 min. Don't share."
        )
        return True
    except Exception as e:
        print(f"[sms_otp] {e}")
        return False


def send_sms_cart_alert(phone, product_name, price, site,
                         twilio_sid, twilio_token, twilio_phone) -> bool:
    try:
        from twilio.rest import Client
        Client(twilio_sid, twilio_token).messages.create(
            from_=twilio_phone, to=phone,
            body=(
                f"CARTSYNCZ ALERT!\n"
                f"{product_name} added to cart on {site}!\n"
                f"Price: ₹{price:,.0f}\n"
                "Reserved for 7 days. Happy shopping!"
            )
        )
        return True
    except Exception as e:
        print(f"[sms_cart] {e}")
        return False
