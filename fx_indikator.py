import streamlit as st
from PIL import Image, ImageDraw
import twelvedata_api as td
import easyocr
import re
import numpy as np

st.set_page_config(page_title="FX Chart Assistant – screenshot + data", layout="wide")
st.title("FX Chart Assistant – screenshot + data")
st.write("Vyber režim analýzy:")

mode = st.radio("Režim:", ["Screenshot analýza", "Data analýza"])

# ======================================
# FUNKCE PRO ANOTACI GRAFU
# ======================================
def annotate_chart_with_strategy(image, df=None, indicators=[], trend=None, sl=None, tp1=None, tp2=None):
    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    # SL a TP jako rámečky
    if sl and tp1:
        sl_y = int(h * (1 - (sl - df['close'].min()) / (df['close'].max() - df['close'].min())))
        tp1_y = int(h * (1 - (tp1 - df['close'].min()) / (df['close'].max() - df['close'].min())))
        tp2_y = int(h * (1 - (tp2 - df['close'].min()) / (df['close'].max() - df['close'].min())))

        draw.rectangle([(0, sl_y-5), (w, sl_y+5)], outline="red", width=3)
        draw.rectangle([(0, tp1_y-5), (w, tp1_y+5)], outline="green", width=3)
        draw.rectangle([(0, tp2_y-5), (w, tp2_y+5)], outline="green", width=3)

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

# ======================================
# FUNKCE OCR
# ======================================
def detect_currency_pair(image):
    reader = easyocr.Reader(['en'])
    img_array = np.array(image)
    results = reader.readtext(img_array)
    text = " ".join([res[1] for res in results])
    match = re.search(r'\b([A-Z]{3}/[A-Z]{3})\b', text)
    if match:
        return match.group(1).replace("/", "").upper()
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

    uploaded_file = st.file_uploader("Nahraj screenshot grafu:", type=["png","jpg","jpeg"])
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
            annotated, desc = annotate_chart_with_strategy(original)
            st.image(annotated, use_column_width=True)
            st.markdown(desc)
        else:
            st.info("Nahraj screenshot a klikni na tlačítko.")

else:
    st.header("Data analýza (TwelveData)")
    uploaded_file = st.file_uploader("Nahraj screenshot grafu:", type=["png","jpg","jpeg"])
    timeframe = st.selectbox("Timeframe:", ["1min","5min","15min","1h","4h"])
    indicators = st.multiselect("Vyber indikátory k vykreslení:", ["EMA50","EMA200","RSI","ADX"], default=["EMA50","EMA200","RSI","ADX"])
    pair_input = st.text_input("Měnový pár (volitelně, OCR):")

    analyze_button = st.button("Analyzovat")

    if uploaded_file and analyze_button:
        image = Image.open(uploaded_file)
        pair = detect_currency_pair(image) if not pair_input else pair_input.upper()

        if not pair:
            st.error("Nepodařilo se rozpoznat měnový pár z obrázku. Zadej ho ručně.")
        else:
            try:
                df = td.get_ohlc(pair, timeframe)
                trend, signal, ind_values = td.determine_trend(df)
                sl, tp1, tp2 = td.calculate_sl_tp(df, signal)

                # Pokud trend není vhodný, SL se nezobrazuje a vypíše doporučení
                if sl is None or trend == "Neutrální":
                    atr = df['high'].rolling(14).max().iloc[-1] - df['low'].rolling(14).min().iloc[-1]
                    sl = None
                    tp1 = None
                    tp2 = None
                    st.warning(f"Není vhodná doba pro SL. Doporučená velikost SL: {atr:.5f}")

                annotated, desc = annotate_chart_with_strategy(image, df=df, indicators=indicators,
                                                               trend=trend, sl=sl, tp1=tp1, tp2=tp2)
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Původní graf")
                    st.image(image, use_column_width=True)
                with col2:
                    st.subheader("Analýza s indikátory")
                    st.image(annotated, use_column_width=True)
                    st.markdown(desc)

                st.markdown(f"""
### Výsledek Data analýzy

**Použitý pár:** {pair}  
**Trend:** {trend}  
**Signal:** {signal}  

**Indikátory:**  
{chr(10).join([f"- {k}: {v:.5f}" for k,v in ind_values.items() if k in indicators])}

**SL:** {sl if sl else '–'}  
**TP1:** {tp1 if tp1 else '–'}  
**TP2:** {tp2 if tp2 else '–'}
""")
            except Exception as e:
                st.error(f"Chyba při načítání nebo výpočtu: {e}")
