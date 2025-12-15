# fx_scanner_prototype.py
import streamlit as st
from PIL import Image
import numpy as np
import easyocr
import re

import twelvedata_api as td
from fx_indikator import annotate_chart_with_strategy


# ======================================
# ZÁKLADNÍ NASTAVENÍ
# ======================================
st.set_page_config(page_title="FX Chart Assistant", layout="wide")
st.title("FX Chart Assistant")
st.write("Screenshot + Data analýza (bez zbytečného zahlcení grafu)")


# ======================================
# OCR – DETEKCE MĚNOVÉHO PÁRU
# ======================================
@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(["en"], gpu=False)


def detect_currency_pair(image):
    reader = get_ocr_reader()
    img_array = np.array(image)
    results = reader.readtext(img_array)

    text = " ".join(r[1] for r in results)
    match = re.search(r"\b([A-Z]{3})/?([A-Z]{3})\b", text)

    if match:
        return f"{match.group(1)}{match.group(2)}"

    return None


# ======================================
# REŽIM
# ======================================
mode = st.radio("Režim:", ["Screenshot analýza", "Data analýza"])


# ======================================
# SCREENSHOT ANALÝZA (JEN OBRÁZEK)
# ======================================
if mode == "Screenshot analýza":
    st.header("Screenshot analýza")

    uploaded_file = st.file_uploader(
        "Nahraj screenshot grafu", type=["png", "jpg", "jpeg"]
    )

    if uploaded_file:
        image = Image.open(uploaded_file)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Původní graf")
            st.image(image, use_column_width=True)

        with col2:
            st.subheader("Info")
            st.info(
                "Screenshot analýza je čistě vizuální.\n"
                "Pro indikátory a SL/TP použij Data analýzu."
            )


# ======================================
# DATA ANALÝZA
# ======================================
else:
    st.header("Data analýza (TwelveData)")

    uploaded_file = st.file_uploader(
        "Nahraj screenshot grafu", type=["png", "jpg", "jpeg"]
    )

    timeframe = st.selectbox(
        "Timeframe", ["1min", "5min", "15min", "1h", "4h"]
    )

    indicators = st.multiselect(
        "Indikátory k vykreslení",
        ["EMA50", "EMA200", "RSI", "ADX"],
        default=["EMA50", "EMA200"]
    )

    manual_pair = st.text_input(
        "Měnový pár (např. EURUSD) – přepíše OCR"
    )

    analyze_button = st.button("Analyzovat")

    if uploaded_file and analyze_button:
        image = Image.open(uploaded_file)

        # ===== SYMBOL =====
        pair = manual_pair.strip().upper()
        if not pair:
            pair = detect_currency_pair(image)

        if not pair or len(pair) != 6:
            st.error("Nelze určit měnový pár. Zadej ho ručně (např. EURUSD).")
            st.stop()

        st.write(f"Použitý symbol: **{pair}**")

        # ===== DATA =====
        try:
            df = td.get_ohlc(pair, timeframe)
            trend, signal, ind_values = td.determine_trend(df)
            sl, tp1, tp2 = td.calculate_sl_tp(df, signal)

            # ===== PŘIDÁNÍ INDIKÁTORŮ DO DF =====
            if "EMA50" in indicators:
                df["EMA50"] = td.calculate_ema(df, 50)
            if "EMA200" in indicators:
                df["EMA200"] = td.calculate_ema(df, 200)
            if "RSI" in indicators:
                df["RSI"] = td.calculate_rsi(df)
            if "ADX" in indicators:
                df["ADX"] = td.calculate_adx(df)

            annotated, desc = annotate_chart_with_strategy(
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
                st.subheader("Výsledek")
                st.image(annotated, use_column_width=True)
                st.markdown(desc)

            st.markdown("### Detail signálu")
            st.write(f"Trend: **{trend}**")
            st.write(f"Signál: **{signal}**")

            for k, v in ind_values.items():
                if k in indicators:
                    st.write(f"{k}: {v:.5f}")

            if sl:
                st.write(f"SL: {sl:.5f}")
                st.write(f"TP1: {tp1:.5f}")
                st.write(f"TP2: {tp2:.5f}")
            else:
                st.warning("Signál není dostatečně silný pro SL / TP.")

        except Exception as e:
            st.error(f"Chyba během zpracování: {e}")
