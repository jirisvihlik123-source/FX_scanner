# fx_indikator.py
from PIL import Image, ImageDraw
import numpy as np

def annotate_chart_with_strategy(image, df=None, indicators=[], trend=None, sl=None, tp1=None, tp2=None):
    """
    Funkce na anotaci grafu:
    - Vykreslí SL/TP jako červené a zelené rámečky
    - Vykreslí indikátory z df
    - Vrátí anotovaný obrázek a popis
    """
    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # SL a TP jako rámečky
    if sl is not None and tp1 is not None and df is not None:
        min_price = df['close'].min()
        max_price = df['close'].max()

        sl_y = int(h * (1 - (sl - min_price) / (max_price - min_price)))
        tp1_y = int(h * (1 - (tp1 - min_price) / (max_price - min_price)))
        tp2_y = int(h * (1 - (tp2 - min_price) / (max_price - min_price)))

        draw.rectangle([(0, sl_y-3), (w, sl_y+3)], outline="red", width=3)
        draw.rectangle([(0, tp1_y-3), (w, tp1_y+3)], outline="green", width=3)
        draw.rectangle([(0, tp2_y-3), (w, tp2_y+3)], outline="green", width=3)

    # Indikátory do grafu
    if df is not None and indicators:
        for ind in indicators:
            if ind in df.columns:
                scaled = (df[ind] - df[ind].min()) / (df[ind].max() - df[ind].min())
                y = (1 - scaled.iloc[-1]) * h
                draw.line([(0, y), (w, y)], fill="blue", width=2)
                draw.text((w-60, y-10), ind, fill="blue")

    description = f"### Analýza grafu\nTrend: {trend}\nSL/TP zakresleno."
    return img, description

