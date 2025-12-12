# fx_indikator.py
import numpy as np
from PIL import Image, ImageDraw

def annotate_chart_with_strategy(image, df=None, indicators=[], trend=None, sl=None, tp1=None, tp2=None):
    """
    Vykreslí na obrázek grafu indikátory a SL/TP zóny.
    - image: PIL.Image
    - df: DataFrame s hodnotami indikátorů
    - indicators: seznam indikátorů k vykreslení (např. ["EMA50","EMA200","RSI","ADX"])
    - trend: textový popis trendu
    - sl, tp1, tp2: hodnoty Stop Loss a Take Profit
    """
    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # SL a TP jako červené a zelené rámečky
    if sl is not None and tp1 is not None and df is not None:
        min_price = df['close'].min()
        max_price = df['close'].max()
        if max_price != min_price:  # zabránění dělení nulou
            sl_y = int(h * (1 - (sl - min_price) / (max_price - min_price)))
            tp1_y = int(h * (1 - (tp1 - min_price) / (max_price - min_price)))
            tp2_y = int(h * (1 - (tp2 - min_price) / (max_price - min_price)))

            draw.rectangle([(0, sl_y-5), (w, sl_y+5)], outline="red", width=3)
            draw.rectangle([(0, tp1_y-5), (w, tp1_y+5)], outline="green", width=3)
            draw.rectangle([(0, tp2_y-5), (w, tp2_y+5)], outline="green", width=3)

    # Indikátory
    if df is not None and indicators:
        for ind in indicators:
            if ind in df.columns:
                scaled = (df[ind] - df[ind].min()) / (df[ind].max() - df[ind].min() + 1e-8)
                y = (1 - scaled.iloc[-1]) * h
                draw.line([(0, y), (w, y)], fill="blue", width=2)
                draw.text((w-60, y-10), ind, fill="blue")

    description = f"### Analýza grafu\nTrend: {trend}\nSL/TP zakresleno, indikátory: {', '.join(indicators)}"
    return img, description
