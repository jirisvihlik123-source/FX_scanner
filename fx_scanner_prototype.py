import streamlit as st
from PIL import Image, ImageDraw
import twelvedata_api as td
import easyocr
import re
import numpy as np

# ======================================
# ZAKLADNI NASTAVENI STRANKY
# ======================================
st.set_page_config(
    page_title="FX Chart Assistant",
    layout="wide"
)

st.title("FX Chart Assistant – screenshot + data režim")
st.write("Vyber režim analýzy.")

# ======================================
# REŽIMY
# ======================================
mode = st.radio(
    "Vyber režim:",
    ["Screenshot analýza", "Data analýza"]
)

# ======================================
# REŽIM 1 – SCREENSHOT ANALÝZA
# ======================================
def annotate_chart_with_strategy(image, direction, strategy, rrr):
    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # základní pozice zón
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
    if strategy == "Breakout - průraz":
        if direction.startswith("Long"):
            entry_y = int(h * 0.50)
            sl_y = int(h * 0.65)
            tp1_y = int(h * 0.35)
        else:
            entry_y = int(h * 0.50)
            sl_y = int(h * 0.35)
            tp1_y = int(h * 0.62)

    # preset: range
    if strategy == "Range - obchod v pásmu":
        sl_y = int(h * 0.70)
        entry_y = int(h * 0.60)
        tp1_y = int(h * 0.50)
        tp2_y = int(h * 0.42)

    def draw_level(y, label, color):
        draw.line([(0, y), (w, y)], fill=color, width=3)
        draw.rectangle([(10, y - 24), (180, y)], fill=(0, 0, 0, 180))
        draw.text((15, y - 20), label, fill="white")

    draw_level(sl_y, "SL zóna", "#ff4d4d")
    draw_level(entry_y, "ENTRY", "#facc15")
    draw_level(tp1_y, "TP1", "#22c55e")
    draw_level(tp2_y, f"TP2 (RRR ~ {rrr:.1f})", "#16a34a")

    description = f"""
### Screenshot analýza

**Směr:** {direction}  
**Strategie:** {strategy}  
**RRR:** 1:{rrr:.1f}

**SL zóna** – místo pro ochranu obchodu.  
**ENTRY** – logická zóna vstupu.  
**TP1 + TP2** – cílový profit.
"""
    return img, description

# ======================================
# REŽIM 2 – DATA ANALÝZA (EasyOCR + TwelveData)
# ======================================
def detect_currency_pair(image):
    """
    OCR detekce měnového páru z obrázku pomocí EasyOCR.
    """
    reader = easyocr.Reader(['en'])
    img_array = np.array(image)
    results = reader.readtext(img_array)
    text = " ".join([res[1] for res in results])
    match = re.search(r'\b([A-Z]{3}/[A-Z]{3})\b', text)
    if match:
        return match.group(1).replace("/", "").upper()  # převede na formát EURUSD
    return None

# ======================================
# STREAMLIT LAYOUT
# ======================================
if mode == "Screenshot analýza":
    st.header("Screenshot analýza")
    st.sidebar.header("Nastavení strategie")

    direction = st.sidebar.radio("Směr obchodu:", ["Long (buy)", "Short (sell)"])
    strategy = st.sidebar.selectbox("Strategie:", ["Swing - pullback", "Breakout - průraz", "Range - obchod v pásmu"])
    rrr = st.sidebar.slider("RRR (Risk Reward):", 1.0, 4.0, 2.0, 0.5)

    uploaded_file = st.file_uploader("Nahraj screenshot grafu:", type=["png", "jpg", "jpeg"])
    analyze_button = st.button("Vygenerovat analýzu")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Původní graf")
        if uploaded_file:
            original = Image.open(uploaded_file)
            st.image(original, use_column_width=True)
    with col2:
        st.subheader("Analýza")
        if uploaded_file and analyze_button:
            original = Image.open(uploaded_file)
            annotated, desc = annotate_chart_with_strategy(original, direction, strategy, rrr)
            st.image(annotated, use_column_width=True)
            st.markdown(desc)
        else:
            st.info("Nahraj screenshot a klikni na tlačítko.")

else:
    st.header("Data analýza (TwelveData)")
    uploaded_file = st.file_uploader("Nahraj screenshot grafu:", type=["png", "jpg", "jpeg"])
    timeframe = st.selectbox("Timeframe:", ["1min", "5min", "15min", "1h", "4h"])
    indicators = st.multiselect("Vyber indikátory:", ["EMA50", "EMA200", "RSI14", "ADX"], default=["EMA50","EMA200","RSI14","ADX"])
    manual_pair = st.text_input("Ruční zadání měnového páru (EURUSD):", "")

    analyze_button = st.button("Analyzovat")

    if uploaded_file and analyze_button:
        image = Image.open(uploaded_file)
        pair = detect_currency_pair(image)

        if manual_pair:
            pair = manual_pair.replace("/", "").upper()

        if not pair:
            st.error("Nepodařilo se rozpoznat měnový pár z obrázku. Zadej ho ručně.")
        else:
            try:
                df = td.get_ohlc(pair, timeframe)
                trend, signal, ind_values = td.determine_trend(df)
                sl, tp1, tp2 = td.calculate_sl_tp(df, signal)
                st.success(f"Použitý pár: {pair}")
                st.markdown(f"""
### Výsledek Data analýza

**Trend:** {trend}  
**Signal:** {signal}  

**Indikátory:**  
{chr(10).join([f"- {k}: {v:.5f}" for k,v in ind_values.items() if k in indicators])}

**SL:** {sl:.5f if sl else '–'}  
**TP1:** {tp1:.5f if tp1 else '–'}  
**TP2:** {tp2:.5f if tp2 else '–'}
                """)
            except Exception as e:
                st.error(f"Chyba při načítání dat z API: {e}")

