# twelvedata_api.py
import requests
import pandas as pd
import streamlit as st

# ======================================
# NAČTENÍ API KEY ZE SECRETS
# ======================================
API_KEY = st.secrets.get("TD_API_KEY", None)
if not API_KEY:
    raise ValueError("API key není načten ze Streamlit secrets! Přidej ho pod TD_API_KEY.")

# ======================================
# FUNKCE: Stáhne OHLC data
# ======================================
def get_ohlc(pair: str, interval: str, outputsize=200):
    """
    Vrací DataFrame s indexem datetime a sloupci open, high, low, close, (volume)
    pair musí být ve formátu jako 'EURUSD' nebo 'EUR/USD' (převod proveden zde).
    """
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

    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if "values" not in data:
        # Propagujeme čitelnou chybu dál
        raise ValueError(f"Chyba v API: {data}")

    df = pd.DataFrame(data["values"])[::-1].reset_index(drop=True)

    # bezpečně převeď sloupce, které existují
    for col in ["open", "high", "low", "close", "volume"]:
        if col in df.columns:
            df[col] = df[col].astype(float)
        else:
            df[col] = pd.NA

    # datetime a index
    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"])
        df.set_index("datetime", inplace=True)
    else:
        # pokud náhodou chybí, vytvoříme sekvenční index
        df.index = pd.date_range(end=pd.Timestamp.now(), periods=len(df), freq="T")

    return df

# ======================================
# FUNKCE: EMA
# ======================================
def calculate_ema(df, period=50):
    if len(df) < 2:
        return pd.Series([pd.NA] * len(df), index=df.index)
    return df["close"].ewm(span=period, adjust=False).mean()

# ======================================
# FUNKCE: RSI
# ======================================
def calculate_rsi(df, period=14):
    if len(df) < period + 1:
        return pd.Series([pd.NA] * len(df), index=df.index)
    delta = df["close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# ======================================
# FUNKCE: ADX
# ======================================
def calculate_adx(df, period=14):
    if len(df) < period + 1:
        return pd.Series([pd.NA] * len(df), index=df.index)

    df2 = df.copy()
    df2["TR"] = df2[["high", "low", "close"]].apply(
        lambda x: max(x["high"] - x["low"], abs(x["high"] - x["close"]), abs(x["low"] - x["close"])), axis=1
    )
    df2["+DM"] = df2["high"].diff()
    df2["-DM"] = -df2["low"].diff()
    df2["+DM"] = df2["+DM"].where((df2["+DM"] > df2["-DM"]) & (df2["+DM"] > 0), 0.0)
    df2["-DM"] = df2["-DM"].where((df2["-DM"] > df2["+DM"]) & (df2["-DM"] > 0), 0.0)

    atr = df2["TR"].rolling(period).mean()
    plus_di = 100 * (df2["+DM"].rolling(period).sum() / atr)
    minus_di = 100 * (df2["-DM"].rolling(period).sum() / atr)
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
    adx = dx.rolling(period).mean()
    return adx

# ======================================
# FUNKCE: Určení trendu a signálu
# ======================================
def determine_trend(df):
    """
    Vrátí (trend, signal, indicators_dict)
    indicators_dict obsahuje klíče: EMA50, EMA200, RSI, ADX (poslední hodnoty)
    """
    # počítej celé série (pro vizualizaci)
    ema50_s = calculate_ema(df, 50)
    ema200_s = calculate_ema(df, 200)
    rsi_s = calculate_rsi(df, 14)
    adx_s = calculate_adx(df, 14)

    # poslední hodnoty (bez chyb)
    def last_valid(series):
        try:
            return float(series.dropna().iloc[-1])
        except Exception:
            return None

    ema50 = last_valid(ema50_s)
    ema200 = last_valid(ema200_s)
    rsi = last_valid(rsi_s)
    adx = last_valid(adx_s)

    trend = "Neutrální"
    signal = "Neobchodovat"

    if ema50 is not None and ema200 is not None and rsi is not None and adx is not None:
        if ema50 > ema200 and rsi > 50 and adx > 20:
            trend = "Bullish"
            signal = "Long"
        elif ema50 < ema200 and rsi < 50 and adx > 20:
            trend = "Bearish"
            signal = "Short"

    indicators = {"EMA50": ema50, "EMA200": ema200, "RSI": rsi, "ADX": adx}
    # také přidáme série do dict pro případ, že je chceš vykreslit jinde
    indicators["_series"] = {"EMA50": ema50_s, "EMA200": ema200_s, "RSI": rsi_s, "ADX": adx_s}

    return trend, signal, indicators

# ======================================
# FUNKCE: SL a TP
# ======================================
def calculate_sl_tp(df, signal):
    """
    Vrátí (sl, tp1, tp2) nebo (None, None, None)
    SL/TP jsou počítány podle ATR-based pravidla.
    """
    if df is None or len(df) < 3:
        return None, None, None

    last_close = df["close"].iloc[-1]
    # ATR jako high rolling max - low rolling min (jednoduchý proxy)
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
        # pro neutrální vrací None -> hlavní aplikace může nabídnout doporučení
        return None, None, None

    return float(sl), float(tp1), float(tp2)

