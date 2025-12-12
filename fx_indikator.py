# chart_generator.py
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import pandas as pd
import numpy as np

def draw_chart(df,
               ema50=None,
               ema200=None,
               rsi=None,
               adx=None,
               signal=None,
               sl=None,
               tp1=None,
               tp2=None,
               show_ema50=True,
               show_ema200=True,
               show_rsi=True,
               show_adx=True):
    """
    Vrací matplotlib.figure.Figure s vykresleným close, EMA50/200, SL/TP jako pásy,
    a mini grafy RSI/ADX pokud jsou zapnuté.
    df: DataFrame s index datetime a sloupci open, high, low, close
    show_*: boolean, jestli indikátor vykreslit
    """

    # bezpečnostní fallback
    if df is None or df.empty:
        fig = plt.figure(figsize=(8, 4))
        plt.text(0.5, 0.5, "No data", ha="center", va="center")
        plt.axis("off")
        return fig

    # připravíme serie indikátorů v df (pokud ještě nejsou)
    df = df.copy()
    if "EMA50" not in df.columns:
        df["EMA50"] = df["close"].ewm(span=50, adjust=False).mean()
    if "EMA200" not in df.columns:
        df["EMA200"] = df["close"].ewm(span=200, adjust=False).mean()
    if "RSI" not in df.columns:
        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))
    if "ADX" not in df.columns:
        # jednoduchá ADX přepočítaná pouze pro zobrazení (může být pomalejší)
        df2 = df.copy()
        df2["TR"] = df2[["high", "low", "close"]].apply(
            lambda x: max(x["high"] - x["low"], abs(x["high"] - x["close"]), abs(x["low"] - x["close"])), axis=1
        )
        df2["+DM"] = df2["high"].diff().where(df2["high"].diff() > df2["low"].diff().abs(), 0.0)
        df2["-DM"] = df2["low"].diff().abs().where(df2["low"].diff().abs() > df2["high"].diff(), 0.0)
        atr = df2["TR"].rolling(14).mean()
        plus = 100 * (df2["+DM"].rolling(14).sum() / atr)
        minus = 100 * (df2["-DM"].rolling(14).sum() / atr)
        dx = (plus - minus).abs() / (plus + minus) * 100
        df["ADX"] = dx.rolling(14).mean()

    # grafické rozložení
    n_sub = 1 + (1 if show_rsi else 0) + (1 if show_adx else 0)
    height_ratios = [3] + [1] * (n_sub - 1)
    fig = plt.figure(figsize=(12, 6))
    gs = gridspec.GridSpec(n_sub, 1, height_ratios=height_ratios, hspace=0.15)

    ax_main = plt.subplot(gs[0])

    # Hlavní graf - close
    ax_main.plot(df.index, df["close"], label="Close", linewidth=1.2)
    if show_ema50 and "EMA50" in df.columns:
        ax_main.plot(df.index, df["EMA50"], label="EMA50", linewidth=1)
    if show_ema200 and "EMA200" in df.columns:
        ax_main.plot(df.index, df["EMA200"], label="EMA200", linewidth=1)

    ax_main.set_ylabel("Price")
    ax_main.legend(loc="upper left", fontsize=8)
    ax_main.grid(True)

    # SL/TP jako pásy (pokud jsou)
    try:
        price_min = df["close"].min()
        price_max = df["close"].max()
        price_range = price_max - price_min if price_max > price_min else price_max * 0.01
    except Exception:
        price_range = 1.0

    band = price_range * 0.02  # tloušťka rámečku (2% rozsahu) - vizuální

    if sl is not None:
        ax_main.axhspan(sl - band, sl + band, color="red", alpha=0.25, label="SL")
        ax_main.text(df.index[-1], sl, " SL", va="center", ha="left", color="red", fontsize=9)
    if tp1 is not None:
        ax_main.axhspan(tp1 - band, tp1 + band, color="green", alpha=0.2, label="TP1")
        ax_main.text(df.index[-1], tp1, " TP1", va="center", ha="left", color="green", fontsize=9)
    if tp2 is not None:
        ax_main.axhspan(tp2 - band, tp2 + band, color="green", alpha=0.15, label="TP2")
        ax_main.text(df.index[-1], tp2, " TP2", va="center", ha="left", color="green", fontsize=9)

    # dolní podgrafy
    idx = 1
    if show_rsi:
        ax_rsi = plt.subplot(gs[idx], sharex=ax_main)
        ax_rsi.plot(df.index, df["RSI"], label="RSI", linewidth=1)
        ax_rsi.axhline(70, color="gray", linewidth=0.5, linestyle="--")
        ax_rsi.axhline(30, color="gray", linewidth=0.5, linestyle="--")
        ax_rsi.set_ylabel("RSI")
        ax_rsi.grid(True)
        idx += 1

    if show_adx:
        ax_adx = plt.subplot(gs[idx], sharex=ax_main)
        ax_adx.plot(df.index, df["ADX"], label="ADX", linewidth=1)
        ax_adx.axhline(20, color="gray", linewidth=0.5, linestyle="--")
        ax_adx.set_ylabel("ADX")
        ax_adx.grid(True)

    # estetika
    for ax in fig.axes:
        for label in ax.get_xticklabels():
            label.set_rotation(25)
            label.set_ha("right")

    fig.tight_layout()
    return fig
