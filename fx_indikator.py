# fx_indikator.py
import pandas as pd
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from io import BytesIO

def generate_indicator_chart(df, indicators, sl=None, tp1=None, tp2=None):
    """
    Vytvoří kombinovaný graf:
    - svíčky
    - indikátory dle výběru uživatele
    - SL/TP zóny
    Vrací PIL Image.
    """

    if df is None or len(df) < 3:
        raise ValueError("Nedostatek dat pro vykreslení grafu.")

    # Připravíme obrázek
    fig, ax = plt.subplots(figsize=(12, 6))

    # -----------------------------
    # SVÍČKOVÝ GRAF (OHLC)
    # -----------------------------
    for i in range(len(df)):
        o = df["open"].iloc[i]
        h = df["high"].iloc[i]
        l = df["low"].iloc[i]
        c = df["close"].iloc[i]

        color = "green" if c >= o else "red"
        ax.plot([i, i], [l, h], color=color, linewidth=1)  # knot
        ax.add_patch(
            plt.Rectangle(
                (i - 0.3, min(o, c)), 0.6, abs(c - o),
                color=color, alpha=0.6
            )
        )

    # -----------------------------
    # INDIKÁTORY
    # -----------------------------
    ind_series = indicators.get("_series", {})

    if "EMA50" in ind_series:
        ax.plot(ind_series["EMA50"].values, label="EMA50", linewidth=1.5)

    if "EMA200" in ind_series:
        ax.plot(ind_series["EMA200"].values, label="EMA200", linewidth=1.5)

    if "RSI" in ind_series:
        rsi = ind_series["RSI"].values
        # Přepočet do stejného rozsahu jako cena (vizualizace)
        scaled_rsi = (
            (rsi - np.nanmin(rsi)) /
            (np.nanmax(rsi) - np.nanmin(rsi) + 1e-9)
        ) * (df["close"].max() - df["close"].min()) + df["close"].min()
        ax.plot(scaled_rsi, label="RSI (scaled)", linewidth=1)

    if "ADX" in ind_series:
        adx = ind_series["ADX"].values
        scaled_adx = (
            (adx - np.nanmin(adx)) /
            (np.nanmax(adx) - np.nanmin(adx) + 1e-9)
        ) * (df["close"].max() - df["close"].min()) + df["close"].min()
        ax.plot(scaled_adx, label="ADX (scaled)", linewidth=1)

    # -----------------------------
    # SL / TP LINKY
    # -----------------------------
    if sl is not None:
        ax.axhline(sl, color="red", linewidth=1.5, label="SL")

    if tp1 is not None:
        ax.axhline(tp1, color="green", linewidth=1.5, label="TP1")

    if tp2 is not None:
        ax.axhline(tp2, color="green", linestyle="--", linewidth=1.5, label="TP2")

    # Osa a legenda
    ax.set_title("Price Chart with Indicators")
    ax.set_xlim(0, len(df))
    ax.legend()

    # -----------------------------
    # Export jako PIL Image
    # -----------------------------
    buf = BytesIO()
    plt.tight_layout()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)

    return Image.open(buf).convert("RGBA")
