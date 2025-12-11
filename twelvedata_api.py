import requests
import pandas as pd

API_KEY = "cb61bbdf66f84ba4952d645daec6d807"  # nahraď svým klíčem

def get_ohlc(pair: str, interval: str, outputsize=100):
    print("DEBUG API pair =", repr(pair))
    print("DEBUG API interval =", repr(interval))
    print("DEBUG API KEY =", repr(API_KEY))

    """
    Stáhne OHLC data pro daný symbol a timeframe.
    """
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": pair.upper(),
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
    df["TR"] = df[["high","low","close"]].apply(
        lambda x: max(x["high"]-x["low"], abs(x["high"]-x["close"]), abs(x["low"]-x["close"])), axis=1
    )
    df["+DM"] = df["high"].diff()
    df["-DM"] = df["low"].diff().abs()
    df["+DM"] = df["+DM"].where((df["+DM"]>df["-DM"]) & (df["+DM"]>0), 0)
    df["-DM"] = df["-DM"].where((df["-DM"]>df["+DM"]) & (df["-DM"]>0), 0)
    atr = df["TR"].rolling(period).mean()
    plus_di = 100 * (df["+DM"].rolling(period).sum() / atr)
    minus_di = 100 * (df["-DM"].rolling(period).sum() / atr)
    adx = abs(plus_di - minus_di) / (plus_di + minus_di) * 100
    adx = adx.rolling(period).mean()
    return adx

def determine_trend(df):
    ema50 = calculate_ema(df, 50).iloc[-1]
    ema200 = calculate_ema(df, 200).iloc[-1]
    rsi = calculate_rsi(df).iloc[-1]
    adx = calculate_adx(df).iloc[-1]

    trend = "Neutrální"
    signal = "Neobchodovat"

    if ema50 > ema200 and rsi > 50 and adx > 20:
        trend = "Bullish"
        signal = "Long"
    elif ema50 < ema200 and rsi < 50 and adx > 20:
        trend = "Bearish"
        signal = "Short"

    return trend, signal, {"EMA50": ema50, "EMA200": ema200, "RSI": rsi, "ADX": adx}

def calculate_sl_tp(df, signal):
    last_close = df["close"].iloc[-1]
    atr = df["high"].rolling(14).max().iloc[-1] - df["low"].rolling(14).min().iloc[-1]

    if signal == "Long":
        sl = last_close - atr
        tp1 = last_close + atr
        tp2 = last_close + 2 * atr
    elif signal == "Short":
        sl = last_close + atr
        tp1 = last_close - atr
        tp2 = last_close - 2 * atr
    else:
        sl = tp1 = tp2 = None

    return sl, tp1, tp2
