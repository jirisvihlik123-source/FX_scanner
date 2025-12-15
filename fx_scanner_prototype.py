# fx_scanner_prototype.py
import streamlit as st
from PIL import Image
import numpy as np
import easyocr

import twelvedata_api as td
from fx_indikator import draw_analysis_on_image


# ======================================
# ZÁKLADNÍ NASTAVENÍ
# ======================================
st.set_page_config(page_title="FX Chart Assistant", layout="wide")
st.title("FX Chart Assistant")
st.write("Screenshot + Data analýza (SAFE verze)")

# ======================================
# POVOLENÉ MĚNOVÉ PÁRY (WHITELIST)
# ======================================
ALLOWED_PAIRS = [
    "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
    "AUD/USD", "NZD/USD", "USD/CAD",
    "EUR/GBP", "EUR/JPY"
]


# ======================================
# OCR – pouze návrh
# ======================================
@st.cache_resource
def load_ocr():
    return easyocr.Reader(['en'], gpu=False)


def ocr_suggest_pair(image: Image.Image):
    reader = load_ocr()
    results = reader.readtext(np.array(image))
    text = " ".join([r[1].upper() for r in results])

    for pair in ALLOWED_PAIRS:
        if pair.replace("/", "") in text:
            return pair
    return None


# ======================================
# UI – REŽIM
# ======================================
mode = st.radio("Režim:", ["Screenshot analýza", "Data analýza"])


# ======================================
# REŽIM 1 – SCREENSHOT (jednoduchý)
# ======================================
if mode == "Screenshot analýza":
    st.info("Tento režim je pouze vizuální – bez API.")

    uploaded = st.file_uploader("Nahraj screenshot grafu", type=["png", "jpg", "jpeg"])
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, use_column_width=True)


# ======================================
# REŽIM 2 – DATA ANALÝZA (SAFE)
# ======================================
else:
    st.header("Data analýza (TwelveData – SAFE)")

    uploaded = st.file_uploader("Nahraj screenshot grafu", type=["png", "jpg", "jpeg"])
    timeframe = st.selectbox("Timeframe", ["1min", "5min", "15min", "1h", "4h"])

    indicators = st.multiselect(
        "Zobrazit indikátory v obrázku",
        ["EMA50", "EMA200", "RSI", "ADX"],
        default=["EMA50", "EMA200", "RSI", "ADX"]
    )

    if uploaded:
        image = Image.open(uploaded)

        # OCR návrh
        suggested_pair = ocr_suggest_pair(image)
        if suggested_pair:
            st.success(f"OCR návrh: {suggested_pair}")
        else:
            st.warning("OCR nenašlo měnový pár")

        # JEDINÝ zdroj pravdy
        pair = st.selectbox(
            "Vyber měnový pár (POVINNÉ)",
            ALLOWED_PAIRS,
            index=ALLOWED_PAIRS.index(suggested_pair)
            if suggested_pair in ALLOWED_PAIRS else 0
        )

        analyze = st.button("Analyzovat")

        if analyze:
            try:
                df = td.get_ohlc(pair, timeframe)
                trend, signal, ind_vals = td.determine_trend(df)
                sl, tp1, tp2 = td.calculate_sl_tp(df, signal)

                annotated, note = draw_analysis_on_image(
                    image=image,
                    df=df,
                    indicators=indicators,
                    trend=trend,
                    sl=sl,
                    tp1=tp1,
                    tp2=tp2
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Původní graf")
                    st.image(image, use_column_width=True)

                with col2:
                    st.subheader("Analýza")
                    st.image(annotated, use_column_width=True)
                    st.markdown(note)

                st.markdown("### Výsledky")
                st.write("Trend:", trend)
                st.write("Signál:", signal)
                for k, v in ind_vals.items():
                    st.write(f"{k}: {v:.5f}")

                st.write("SL:", sl)
                st.write("TP1:", tp1)
                st.write("TP2:", tp2)

            except Exception as e:
                st.error(f"Chyba analýzy: {e}")

