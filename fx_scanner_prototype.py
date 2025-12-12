import streamlit as st
from PIL import Image
import twelvedata_api as td
import easyocr
import re
import numpy as np
from fx_indikator import annotate_chart_with_strategy  # nový modul

# ======================================
# ZÁKLADNÍ NASTAVENÍ STRÁNKY
# ======================================
st.set_page_config(
    page_title="FX Chart Assistant – screenshot + data",
    layout="wide"
)
st.title("FX Chart Assistant – screenshot + data")
st.write("Vyber režim analýzy:")

mode = st.radio("Režim:", ["Screenshot analýza", "Data analýza"])

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
# REŽIM 1 – SCREENSHOT ANALÝZA
# ======================================
if mode == "Screenshot analýza":
    st.header("Screenshot analýza")
    st.sidebar.header("Nastavení strategie")

    direction = st.sidebar.radio("Směr obchodu:", ["Long (buy)", "Short (sell)"])
    strategy = st.sidebar.selectbox("Strategie:", [
        "Swing - pullback",
        "Breakout - průraz",
        "Range - obchod v pásmu"
    ])
    rrr = st.sidebar.slider("RRR:", 1.0, 4.0, 2.0, 0.5)

    uploaded_file = st.file_uploader("Nahraj screenshot grafu:", type=["png", "jpg", "jpeg"])
    analyze_button = st.button("Vygenerovat analýzu")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Původní graf")
        if uploaded_file:
            st.image(Image.open(uploaded_file), use_column_width=True)

    with col2:
        st.subheader("Analýza")
        if uploaded_file and analyze_button:
            original = Image.open(uploaded_file)
            annotated, desc = annotate_chart_with_strategy(original, trend=None)
            st.image(annotated, use_column_width=True)
            st.markdown(desc)
        else:
            st.info("Nahraj screenshot a klikni na tlačítko.")

# ======================================
# REŽIM 2 – DATA ANALÝZA
# ======================================
else:
    st.header("Data analýza (TwelveData)")
    uploaded_file = st.file_uploader("Nahraj screenshot grafu:", type=["png","jpg","jpeg"])
    timeframe = st.selectbox("Timeframe:", ["1min","5min","15min","1h","4h"])
    indicators = st.multiselect("Vyber indikátory k vykreslení:", ["EMA50","EMA200","RSI","ADX"], 
                                default=["EMA50","EMA200","RSI","ADX"])
    pair_input = st.text_input("Měnový pár (volitelně, OCR):")
    analyze_button = st.button("Analyzovat")

    if uploaded_file and analyze_button:
        image = Image.open(uploaded_file)

        # OCR detekce měnového páru
        pair = detect_currency_pair(image) if not pair_input else pair_input.upper()
        st.write("OCR výstup:", pair)

        # Pokud OCR selže, uživatel musí zadat pár ručně
        pair = st.text_input("Zadej měnový pár ručně:", value=pair if pair else "")

        if not pair:
            st.error("Nepodařilo se rozpoznat měnový pár. Zadej ho ručně.")
        else:
            try:
                # DEBUG
                st.write("DEBUG – symbol odeslaný do API:", pair)
                st.write("DEBUG – timeframe:", timeframe)
                st.write("DEBUG – API key:", td.API_KEY)

                # Získání dat OHLC
                df = td.get_ohlc(pair, timeframe)

                # Určení trendu a signálu
                trend, signal, ind_values = td.determine_trend(df)
                sl, tp1, tp2 = td.calculate_sl_tp(df, signal)

                # Pokud trend není vhodný, SL/TP se nezobrazí
                if sl is None or trend == "Neutrální":
                    atr = df['high'].rolling(14).max().iloc[-1] - df['low'].rolling(14).min().iloc[-1]
                    sl = tp1 = tp2 = None
                    st.warning(f"Není vhodná doba pro SL. Doporučená velikost SL: {atr:.5f}")

                # Generování obrázku s indikátory
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

                # Textový výstup
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
