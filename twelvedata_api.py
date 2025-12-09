import requests
import pandas as pd
import numpy as np
from typing import Tuple, Dict

API_KEY = "TVŮJ_API_KLIC"  # nahraď svým klíčem

# Helper: normalizace symbolu
def normalize_symbol(pair: str) -> str:
    return pair.replace("/", "").replace(" ", "").upper()

def get_ohlc(pair: str, interval: str, outputsize: int = 200) -> pd.DataFrame:
    """
    Vraci df s indexem datetime a sloupci open, high, low, close, volume.
    Vyhazuje ValueError pokud API vrati chybu.
    """
    symbol = normalize_symbol(pair)
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "apikey": API_KEY,
        "outputsize": outputsize,
        "format": "JSON"
    }
    resp = requests.get(url, params=params, timeout=15)
    try:
        data = resp.json()
    except Exception as e:
        raise ValueError(f"Neplatná odpověď z API: {e}")

    # osetreni chyb z API
    if resp.status_code != 200:
        # dalsi info v odpovedi
        raise ValueError(f"HTTP {resp.status_code} - {data}")

    if "status" in data and data.get("status") == "error":
        raise ValueError(f"Chyba v API: {data}")

    if "values" not in data:
        raise ValueError(f"Neplatna data (values missing): {data}")

    df = pd.DataFrame(data["values"])[::-1].reset_index(drop=True)
    # prepsani typu
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
    df = df.dropna(subset=["datetime"]).set_index("datetime")
    return df

def calculate_ema(df: pd.DataFrame, period: int = 50) -> pd.Series:
    return df["close"].ewm(span=period, adjust=False).mean()

def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Implementace ADX (priblizna, robustni).
    """
    high = df["high"]
    low = df["low"]
    close = df["close"]

    up = high.diff()
    down = low.diff().abs()

    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)

    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    # smooth DM as sum over period (approx)
    plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(period).sum() / atr)
    minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(period).sum() / atr)

    dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
    adx = dx.rolling(period).mean()
    return adx

def determine_trend(df: pd.DataFrame) -> Tuple[str, str, Dict[str, float]]:
    """
    Vraci (trend, signal, indikatory), kde signal je 'Long'/'Short'/'Neobchodovat'
    """
    # zajistime minimalni delku
    if len(df) < 50:
        raise ValueError("Nedostatecny pocet radku dat pro vypocet indikatoru.")

    ema50 = calculate_ema(df, 50).iloc[-1]
    ema200 = calculate_ema(df, 200).iloc[-1] if len(df) >= 200 else calculate_ema(df, 200).iloc[-1]
    rsi = calculate_rsi(df, 14).iloc[-1]
    adx = calculate_adx(df, 14).iloc[-1]

    trend = "Neutrální"
    signal = "Neobchodovat"

    # logika rozhodovani
    if (ema50 > ema200) and (rsi > 50) and (adx > 20):
        trend = "Bullish"
        signal = "Long"
    elif (ema50 < ema200) and (rsi < 50) and (adx > 20):
        trend = "Bearish"
        signal = "Short"

    indik = {
        "EMA50": ema50,
        "EMA200": ema200,
        "RSI14": rsi,
        "ADX": adx
    }
    return trend, signal, indik

def calculate_sl_tp(df: pd.DataFrame, signal: str, aggressive: bool = False) -> Tuple[float, float, float]:
    """
    Agresivni (B) varianta: vetsi TP (2x ATR) a uzsi SL
    conservative: mensi TP, sirsi SL
    """
    last_close = float(df["close"].iloc[-1])
    # ATR aproximace: high-low range over rolling window
    atr = (df["high"].rolling(14).max() - df["low"].rolling(14).min()).iloc[-1]
    if np.isnan(atr) or atr == 0:
        # fallback - pouzij procento close
        atr = last_close * 0.0015  # 0.15% fallback

    if signal == "Long":
        if aggressive:
            sl = last_close - 0.5 * atr
            tp1 = last_close + 1.5 * atr
            tp2 = last_close + 3.0 * atr
        else:
            sl = last_close - 1.0 * atr
            tp1 = last_close + 1.0 * atr
            tp2 = last_close + 2.0 * atr
    elif signal == "Short":
        if aggressive:
            sl = last_close + 0.5 * atr
            tp1 = last_close - 1.5 * atr
            tp2 = last_close - 3.0 * atr
        else:
            sl = last_close + 1.0 * atr
            tp1 = last_close - 1.0 * atr
            tp2 = last_close - 2.0 * atr
    else:
        sl = tp1 = tp2 = None

    return sl, tp1, tp2
