# twelvedata_api.py
import requests
import pandas as pd
import numpy as np

# ==============================
# KONFIGURACE
# ==============================
API_KEY = "TVEJ_API_KLIC_TADY"   # NEBO použij st.secrets
BASE_URL = "https://api.twelvedata.com/time_series"


# ==============================
# NAČTENÍ DAT (SAFE)
# ==============================
def get_ohlc(symbol: str, interval: str, outputsize: int = 200) -> pd.DataFrame:
    params = {
        "symbol": symbol.replace("/", ""),
        "interval": interval,
        "apikey": API_KEY,
        "outputsize": outputsize,
        "format": "JSON"
    }

    r = requests.get(BASE_URL, params=params, timeout=15)
    data = r.json()

    if "status" in data and data["status"] == "error":
        raise ValueError(f"Chyba v API: {data}")

    df = pd.DataFrame(data["values"])
    df = df.astype({
        "open": float,
        "high": float,
        "low": float,
        "close": float
    })

    df = df.sort_index(ascending=False).reset_index(drop=True)
    return df


# ==============================
# INDIKÁTORY
# ==============================
def ema(series, period):
    return series.ewm(span=period, adjust=False).mean()


def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = -delta.clip(upper=0).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def adx(df, period=14):
    high, low, close = df["high"], df["low"], df["close"]

    plus_dm = high.diff()
    minus_dm = low.diff().abs()

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs()
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    return dx.rolling(period).mean()


# ==============================
# TREND & SIGNÁL
# ==============================
def determine_trend(df: pd.DataFrame):
    df["EMA50"] = ema(df["close"], 50)
    df["EMA200"] = ema(df["close"], 200)
    df["RSI"] = rsi(df["close"])
    df["ADX"] = adx(df)

    last = df.iloc[0]
    trend = "Neutrální"
    signal = "Neobchodovat"

    if last["EMA50"] > last["EMA200"] and last["RSI"] > 55:
        trend = "Bullish"
        signal = "Buy"
    elif last["EMA50"] < last["EMA200"] and last["RSI"] < 45:
        trend = "Bearish"
        signal = "Sell"

    indicators = {
        "EMA50": last["EMA50"],
        "EMA200": last["EMA200"],
        "RSI": last["RSI"],
        "ADX": last["ADX"]
    }

    return trend, signal, indicators


# ==============================
# SL / TP (SAFE)
# ==============================
def calculate_sl_tp(df: pd.DataFrame, signal: str):
    if signal not in ["Buy", "Sell"]:
        return None, None, None

    atr = (df["high"] - df["low"]).rolling(14).mean().iloc[0]
    price = df["close"].iloc[0]

    if signal == "Buy":
        sl = price - atr * 1.5
        tp1 = price + atr * 1.5
        tp2 = price + atr * 3
    else:
        sl = price + atr * 1.5
        tp1 = price - atr * 1.5
        tp2 = price - atr * 3

    return round(sl, 5), round(tp1, 5), round(tp2, 5)

