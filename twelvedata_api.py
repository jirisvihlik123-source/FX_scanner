# twelvedata_api.py
import requests
import pandas as pd
import streamlit as st

# ============== API KEY (volitelně ze Streamlit secrets) ==============
# Pokud nemáš v secrets TD_API_KEY, API_KEY bude None — get_ohlc() to ošetří.
API_KEY = st.secrets.get("TD_API_KEY", None)

# ====================== HELPERS / KONSTANTY ===========================
DEFAULT_OUTPUTSIZE = 200
REQUEST_TIMEOUT = 10  # seconds

# ====================== GET OHLC (bez import-time crash) =================
def get_ohlc(pair: str, interval: str, outputsize: int = DEFAULT_OUTPUTSIZE):
    """
    Stáhne OHLC data z TwelveData.
    - pair: 'EURUSD' nebo 'EUR/USD' (automaticky se upraví)
    - interval: '1min','5min','15min','1h','4h', ...
    Vrátí pandas.DataFrame s indexem datetime a sloupci open, high, low, close, volume (volume může být NA).
    V případě chyby vyhodí ValueError s popisem (který hlavní app zobrazí).
    """
    if not API_KEY:
        raise ValueError("API key není nastaven. Přidej TD_API_KEY do Streamlit secrets.")

    if "/" in pair:
        symbol = pair.replace("/", "")
    else:
        symbol = pair

    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "apikey": API_KEY,
        "outputsize": outputsize,
        "format": "JSON"
    }

    try:
        resp = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Chyba při volání TwelveData: {e}")

    try:
        data = resp.json()
    except Exception:
        raise ValueError(f"Neplatná odpověď od TwelveData (není JSON). Status code: {resp.status_code}")

    # Ověření odpovědi
    if "values" not in data:
        # vracíme čitelnou chybu včetně payloadu
        raise ValueError(f"Chyba v API: {data}")

    df = pd.DataFrame(data["values"])[::-1].reset_index(drop=True)

    # bezpečný převod číselných sloupců
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            # nahradíme prázdné stringy None a převedeme na float
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = pd.NA

    # datum / index
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
        df = df.set_index("datetime")
    else:
        # fallback index kdyby náhodou chyběl
        df.index = pd.date_range(end=pd.Timestamp.now(), periods=len(df), freq="T")

    return df

# ====================== EMA ============================================
def calculate_ema(df: pd.DataFrame, period: int = 50) -> pd.Series:
    if df is None or "close" not in df.columns or df["close"].dropna().shape[0] == 0:
        return pd.Series(dtype=float, index=df.index if df is not None else [])
    return df["close"].ewm(span=period, adjust=False).mean()

# ====================== RSI ============================================
def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    if df is None or "close" not in df.columns or len(df["close"].dropna()) < period + 1:
        return pd.Series(dtype=float, index=df.index if df is not None else [])
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ====================== ADX ============================================
def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Vrací ADX sérii. Pokud nedostatek dat, vrací sérii NA.
    """
    if df is None or len(df.dropna(subset=["high", "low", "close"])) < period + 1:
        return pd.Series(dtype=float, index=df.index if df is not None else [])

    d = df.copy()
    # True range
    d["TR"] = d[["high", "low", "close"]].apply(
        lambda x: max(x["high"] - x["low"], abs(x["high"] - x["close"]), abs(x["low"] - x["close"])), axis=1
    )
    d["+DM"] = d["high"].diff()
    d["-DM"] = -d["low"].diff()
    d["+DM"] = d["+DM"].where((d["+DM"] > d["-DM"]) & (d["+DM"] > 0), 0.0)
    d["-DM"] = d["-DM"].where((d["-DM"] > d["+DM"]) & (d["-DM"] > 0), 0.0)

    atr = d["TR"].rolling(period).mean()
    plus_di = 100 * (d["+DM"].rolling(period).sum() / atr)
    minus_di = 100 * (d["-DM"].rolling(period).sum() / atr)
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
    adx = dx.rolling(period).mean()
    return adx

# ====================== TREND & INDIKÁTORY =============================
def determine_trend(df: pd.DataFrame):
    """
    Vrací: (trend:str, signal:str, indicators:dict)
    indicators obsahuje: EMA50, EMA200, RSI, ADX (poslední validní hodnoty) a '_series' -> celé série
    """
    # vypočítat série
    ema50_s = calculate_ema(df, 50)
    ema200_s = calculate_ema(df, 200)
    rsi_s = calculate_rsi(df, 14)
    adx_s = calculate_adx(df, 14)

    def last_value(series):
        try:
            v = series.dropna().iloc[-1]
            return float(v)
        except Exception:
            return None

    ema50 = last_value(ema50_s)
    ema200 = last_value(ema200_s)
    rsi = last_value(rsi_s)
    adx = last_value(adx_s)

    trend = "Neutrální"
    signal = "Neobchodovat"

    if ema50 is not None and ema200 is not None and rsi is not None and adx is not None:
        if ema50 > ema200 and rsi > 50 and adx > 20:
            trend = "Bullish"
            signal = "Long"
        elif ema50 < ema200 and rsi < 50 and adx > 20:
            trend = "Bearish"
            signal = "Short"

    indicators = {
        "EMA50": ema50,
        "EMA200": ema200,
        "RSI": rsi,
        "ADX": adx,
        "_series": {"EMA50": ema50_s, "EMA200": ema200_s, "RSI": rsi_s, "ADX": adx_s}
    }

    return trend, signal, indicators

# ====================== SL / TP =======================================
def calculate_sl_tp(df: pd.DataFrame, signal: str):
    """
    Vrací (sl, tp1, tp2) nebo (None, None, None).
    Používáme jednoduchý ATR proxy (rolling max high - rolling min low).
    """
    if df is None or len(df.dropna(subset=["high", "low", "close"])) < 3:
        return None, None, None

    last_close = df["close"].dropna().iloc[-1]

    try:
        atr = df["high"].rolling(14).max().iloc[-1] - df["low"].rolling(14).min().iloc[-1]
    except Exception:
        atr = None

    if atr is None or pd.isna(atr) or atr == 0:
        return None, None, None

    if signal == "Long":
        sl = last_close - atr
        tp1 = last_close + atr
        tp2 = last_close + 2 * atr
    elif signal == "Short":
        sl = last_close + atr
        tp1 = last_close - atr
        tp2 = last_close - 2 * atr
    else:
        return None, None, None

    return float(sl), float(tp1), float(tp2)
