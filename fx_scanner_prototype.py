import streamlit as st
from PIL import Image
import twelvedata_api as td
import easyocr
import re
import numpy as np
from fx_indikator import generate_indicator_chart

# ======================================
# ZÁKLADNÍ NASTAVENÍ
# ======================================
st.set_page_config(page_title="FX Chart Assistant", layout="wide")
st.title("FX Chart Assistant – Screenshot + Data analýza")

mode = st.radio("Vyber režim:", ["Screenshot analýza", "Data analýza"])

# ======================================
# OCR – DETEKCE MĚNOVÉHO PÁRU
# ======================================
def detect_currency_pair(image):
    reader = easyocr.Reader(['en'])
    img_array = np.array(image)
    results = reader.readtext(img_array)
    text = " ".join([r[1] for r in results])
    match = re.search(r'\b([A-Z]{3}/[A-Z]{3})\b', text)
    if match:
        return match.group(1).replace("/", "").upper()
    return None


# ======================================
# REŽIM 1 – SCREENSHOT ANALÝZA
# ======================================
if mode == "Screenshot analýza":
    st.header("Screenshot analýza")

    direction = st.sidebar.radio("Směr obchodu:", ["Long (buy)", "Short (sell)"])
    strategy = st.sidebar.selectbox("Strategie:", [
        "Swing - pullback", "Breakout - průraz", "Range - obchod v pásmu"
    ])
    rrr = st.sidebar.slider("RRR:", 1.0, 4.0, 2.0, 0.5)

    uploaded_file = st.file_uploader("Nahraj screenshot grafu:", type=["png","jpg","jpeg"])
    analyze_button = st.button("Vygenerovat analýzu")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Původní screenshot")
        if uploaded_file:
            st.image(Image.open(uploaded_file), use_column_width=True)

    with col2:
        st.subheader("Analýza screenshotu")
        if uploaded_file and analyze_button:
            st.info("Tato část bude později doplněna o strategické zóny (SL/TP).")
        else:
            st.info("Nahraj obrázek a klikni na tlačítko.")


# ======================================
# REŽIM 2 – DATA ANALÝZA
# ======================================
else:
    st.header("Data analýza (TwelveData API)")

    uploaded_file = st.file_uploader("Nahraj screenshot grafu (kvůli OCR):", type=["png","jpg","jpeg"])
    timeframe = st.selectbox("Timeframe:", ["1min", "5min", "15min", "1h", "4h"])

    indicators = st.multiselect(
        "Vyber indikátory do obrázku:",
        ["EMA50", "EMA200", "RSI", "ADX"],
        default=["EMA50", "EMA200", "RSI", "ADX"]
    )

    analyze_button = st.button("Analyzovat")

    if uploaded_file and analyze_button:

        # screenshot pro OCR
        image = Image.open(uploaded_file)
        detected_pair = detect_currency_pair(image)

        st.write("OCR detekce:", detected_pair)

        pair = st.text_input("Zadej měnový pár:", value=detected_pair if detected_pair else "")

        if not pair:
            st.error("Zadej měnový pár ručně.")
        else:
            try:
                # DEBUG
                st.write("DEBUG – symbol:", pair)
                st.write("DEBUG – timeframe:", timeframe)
                st.write("DEBUG – API key:", td.API_KEY)

                # STAŽENÍ DAT
                df = td.get_ohlc(pair, timeframe)
                trend, signal, ind_values = td.determine_trend(df)
                sl, tp1, tp2 = td.calculate_sl_tp(df, signal)

                # Pokud není vhodný trend na SL/TP
                if sl is None or trend == "Neutrální":
                    atr = df["high"].rolling(14).max().iloc[-1] - df["low"].rolling(14).min().iloc[-1]
                    st.warning(f"Není vhodná doba pro SL. Doporučený SL (ATR): {atr:.5f}")
                    sl = tp1 = tp2 = None

                # GENEROVÁNÍ GRAFU S INDIKÁTORY
                chart = generate_indicator_chart(
                    df=df,
                    indicators=indicators,
                    sl=sl,
                    tp1=tp1,
                    tp2=tp2,
                    trend=trend
                )

                # VÝSTUP
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Původní screenshot")
                    st.image(image, use_column_width=True)

                with col2:
                    st.subheader("Graf s indikátory a SL/TP")
                    st.image(chart, use_column_width=True)

                st.markdown(f"""
### Výsledek:
**Pár:** {pair}  
**Trend:** {trend}  
**Signál:** {signal}

**Indikátory:**  
{chr(10).join([f"- {k}: {v:.5f}" for k,v in ind_values.items()])}

**SL:** {sl if sl else "–"}  
**TP1:** {tp1 if tp1 else "–"}  
**TP2:** {tp2 if tp2 else "–"}  
""")

            except Exception as e:
                st.error(f"Chyba během zpracování: {e}")
