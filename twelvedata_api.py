import requests
import pandas as pd

API_KEY = "TVŮJ_API_KLIC"

def get_ohlc(pair: str, interval: str, outputsize=100):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": pair,
        "interval": interval,
        "apikey": API_KEY,
        "outputsize": outputsize,
        "format": "JSON"
    }
    resp = requests.get(url, params=params)
    data = resp.json()
    
    if "values" not in data:
        raise ValueError(f"Chyba v API: {data}")
    
    df = pd.DataFrame(data["values"])[::-1]
    df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)
    df["datetime"] = pd.to_datetime(df["datetime"])
    df.set_index("datetime", inplace=True)
    return df

def calculate_ema(df, period=50):
    return df["close"].ewm(span=period, adjust=False).mean()

def calculate_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_adx(df, period=14):
    df = df.copy()
    df["TR"] = df[["high","low","close"]].apply(lambda x: max(x["high"]-x["low"], abs(x["high"]-x["close"]), abs(x["low"]-x["close"])), axis=1)
    df["+DM"] = df["high"].diff()
    df["-DM"] = df["low"].diff().abs()
    df["+DM"] = df["+DM"].where((df["+DM"]>df["-DM"]) & (df["+DM"]>0), 0)
    df["-DM"] = df["-DM"].where((df["-DM"]>df["+DM"]) & (df["-DM"]>0), 0)
    atr = df["TR"].rolling(period).mean()
    plus_di = 100 * (df["+DM"].rolling(period).sum() / atr)
    minus_di = 100 * (df["-DM"].rolling(period).sum() / atr)
    adx = abs(plus_di - minus_di) / (plus_di + mi_

