import streamlit as st
from PIL import Image, ImageDraw
import twelvedata_api as td
import pytesseract
import re

# ======================================
# ZAKLADNI NASTAVENI STRANKY
# ======================================
st.set_page_config(
    page_title="FX Chart Assistant",
    layout="wide"
)

st.title("FX Chart Assistant – screenshot + data rezim")
st.write("Vyber rezim analyzy.")

# ======================================
# REZIMY
# ======================================
mode = st.radio(
    "Vyber rezim:",
    ["Screenshot analyza", "Data analyza"]
)

# ======================================
# REZIM 1 – SCREENSHOT ANALYZA
# ======================================
def annotate_chart_with_strategy(image, direction, strategy, rrr):
    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # zakladni pozice zon
    sl_y = int(h * 0.78)
    entry_y = int(h * 0.60)
    tp1_y = int(h * 0.40)
    tp2_y = int(h * 0.25)

    # mirror pro short
    if direction.startswith("Short"):
        sl_y = int(h * 0.22)
        entry_y = int(h * 0.40)
        tp1_y = int(h * 0.60)
        tp2_y = int(h * 0.75)

    # preset: breakout
    if strategy == "Breakout - pruraz":
        if direction.startswith("Long"):
            entry_y = int(h * 0.50)
            sl_y = int(h * 0.65)
            tp1_y = int(h * 0.35)
        else:
            entry_y = int(h * 0.50)
            sl_y = int(h * 0.35)
            tp1_y = int(h * 0.62)

    # preset: range
    if strategy == "Range - obchod v pasmu":
        sl_y = int(h * 0.70)
        entry_y = int(h * 0.60)
        tp1_y = int(h * 0.50)
        tp2_y = int(h * 0.42)

    def draw_level(y, label, color):
        draw.line([(0, y), (w, y)], fill=color, width=3)
        draw.rectangle([(10, y - 24), (180, y)], fill=(0, 0, 0, 180))
        draw.text((15, y - 20), label, fill="white")

    draw_level(sl_y, "SL zona", "#ff4d4d")
    draw_level(entry_y, "ENTRY", "#facc15")












