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
    draw_level(tp1_y, "TP1", "#22c55e")
    draw_level(tp2_y, f"TP2 (RRR ~ {rrr:.1f})", "#16a34a")

    description = f"""
### Screenshot analyza

**Smer:** {direction}  
**Strategie:** {strategy}  
**RRR:** 1:{rrr:.1f}

**SL zona** – misto pro ochranu obchodu.  
**ENTRY** – logicka zona vstupu.  
**TP1 + TP2** – cilovy profit.
"""

    return img, description

def detect_currency_pair(image):
    text = pytesseract.image_to_string(image)
    match = re.search(r'\b([A-Z]{3}/[A-Z]{3})\b', text)
    if match:
        return match.group(1).replace("/", "").upper()
    return None

if mode == "Screenshot analyza":
    st.header("Screenshot analyza")
    st.sidebar.header("Nastaveni strategie")

    direction = st.sidebar.radio("Smer obchodu:", ["Long (buy)", "Short (sell)"])
    strategy = st.sidebar.selectbox("Strategie:", ["Swing - pullback", "Breakout - pruraz", "Range - obchod v pasmu"])
    rrr = st.sidebar.slider("RRR (Risk Reward):", 1.0, 4.0, 2.0, 0.5)

    uploaded_file = st.file_uploader("Nahraj screenshot grafu:", type=["png", "jpg", "jpeg"])
    analyze_button = st.button("Vygenerovat analyzu")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Puvodni graf")
        if uploaded_file:
            original = Image.open(uploaded_file)
            st.image(original, use_column_width=True)
    with col2:
        st.subheader("Analyza")
        if uploaded_file and analyze_button:
            original = Image.open(uploaded_file)
            annotated, desc = annotate_chart_with_strategy(original, direction, strategy, rrr)
            st.image(annotated, use_column_width=True)
            st.markdown(desc)
        else:
            st.info("Nahraj screenshot a klikni na tlacitko.")

# ======================================
# REZIM 2 – DATA ANALYZA
# ======================================
else:
    st.header("Data analyza (TwelveData)")
    uploaded_file = st.file_uploader("Nahraj screenshot grafu:", type=["png", "jpg", "jpeg"])
    timeframe = st.selectbox("Timeframe:", ["1min", "5min", "15min", "1h", "4h"])
    indicators = st.multiselect("Vyber indikátory:", ["EMA50", "EMA200", "RSI14", "ADX"], default=["EMA50","EMA200","RSI14","ADX"])
    analyze_button = st.button("Analyzovat")

    if uploaded_file and analyze_button:
        image = Image.open(uploaded_file)
        pair = detect_currency_pair(image)
        if not pair:
            st.error("Nepodařilo se rozpoznat měnový pár z obrázku.")
        else:
            try:
                df = td.get_ohlc(pair, timeframe)
                trend, signal, ind_values = td.determine_trend(df)
                sl, tp1, tp2 = td.calculate_sl_tp(df, signal)
                st.success(f"Rozpoznaný pár: {pair}")
                st.markdown(f"""
### Výsledek Data analyza

**Trend:** {trend}  
**Signal:** {signal}  

**Indikátory:**  
{chr(10).join([f"- {k}: {v:.5f}" for k,v in ind_values.items() if k in indicators])}

**SL:** {sl:.5f if sl else '–'}  
**TP1:** {tp1:.5f if tp1 else '–'}  
**TP2:** {tp2:.5f if tp2 else '–'}
                """)
            except Exception as e:
                st.error(f"Chyba při načítání nebo výpočtu: {e}")
