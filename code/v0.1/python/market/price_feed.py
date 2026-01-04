import requests
from datetime import datetime, timezone
from config import SYMBOL, VS_CURRENCY

def fetch_price_with_time():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": SYMBOL, "vs_currencies": VS_CURRENCY}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    price = float(data[SYMBOL][VS_CURRENCY])
    ts = datetime.now(timezone.utc)
    return price, ts
