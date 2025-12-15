# fx_indikator.py
from PIL import Image, ImageDraw, ImageFont
import pandas as pd


# ==============================
# PŘEPIS CENY → Y SOUŘADNICE
# ==============================
def price_to_y(price, min_price, max_price, height):
    if max_price == min_price:
        return height // 2
    return int((1 - (price - min_price) / (max_price - min_price)) * height)


# ==============================
# HLAVNÍ FUNKCE – ANOTACE GRAFU
# ==============================
def annotate_chart_with_strategy(
    image: Image.Image,
    df: pd.DataFrame,
    indicators: list,
    trend: str,
    sl=None,
    tp1=None,
    tp2=None
):
    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)
    width, height = img.size

    min_price = df["low"].min()
    max_price = df["high"].max()

    notes = []

    # ==============================
    # SL / TP RÁMEČKY
    # ==============================
    if sl and tp1 and tp2 and trend != "Neutrální":
        sl_y = price_to_y(sl, min_price, max_price, height)
        tp1_y = price_to_y(tp1, min_price, max_price, height)
        tp2_y = price_to_y(tp2, min_price, max_price, height)

        draw.rectangle([(0, sl_y - 6), (width, sl_y + 6)], outline="red", width=3)
        draw.rectangle([(0, tp1_y - 6), (width, tp1_y + 6)], outline="green", width=3)
        draw.rectangle([(0, tp2_y - 6), (width, tp2_y + 6)], outline="green", width=3)

        notes.append("SL / TP zakresleno do grafu.")
    else:
        notes.append("Nevhodná situace pro zakreslení SL/TP – nízká kvalita signálu.")

    # ==============================
    # INDIKÁTORY (HORIZONTÁLNÍ ÚROVNĚ)
    # ==============================
    color_map = {
        "EMA50": "blue",
        "EMA200": "purple",
        "RSI": "orange",
        "ADX": "brown"
    }

    for ind in indicators:
        if ind not in df.columns:
            continue

        value = df[ind].iloc[0]
        y = price_to_y(value, min_price, max_price, height)

        draw.line([(0, y), (width, y)], fill=color_map.get(ind, "gray"), width=2)
        draw.text((10, y - 12), f"{ind}: {value:.2f}", fill=color_map.get(ind, "gray"))

    # ==============================
    # TEXTOVÝ POPIS
    # ==============================
    description = f"""
### Výsledek analýzy grafu

**Trend:** {trend}

""" + "\n".join(f"- {n}" for n in notes)

    return img, description.strip()
