import streamlit as st
from PIL import Image, ImageDraw
import numpy as np
import re
import easyocr

import twelvedata_api as td


# ======================================
# NASTAVENÍ STRÁNKY
# ======================================
st.set_page_config(
    page_title="FX Chart Assistant",
    layout="wide"
)

st.title("FX Chart Assistant")
st.write("Screenshot + Data analýza")


# ======================================
# NORMALIZACE SYMBOLU (KRITICKÉ)
# ======================================
def normalize_pair(pair_raw: str):
    if not pair_raw:
        return None

    pair = pair_raw.strip().upper()

    # EURUSD → EUR/USD
    if re.fullmatch(r"[A-Z]{6}", pair):
        pair = pair[:3] + "/" + pair[3:]

    # finální validace
    if not re.fullmatch(r"[A-Z]{3}/[A-Z]{3}", pair):
        return None

    return pair


# ======================================
# OCR – DETEKCE PÁRU
# ======================================
@st.cache_resource
def get_ocr_reader():
    return easyocr.Reader(["en"], gpu=False)


def detect_currency_pair(image):
    reader = get_ocr_reader()
    img_array = np.array(image)
    results = reader.readtext(img_array)

    text = " ".join([r[1] for r in results])
    match = re.search(r"\b([A-Z]{3}/?[A-Z]{3})\b", text.upper())

    if match:
        return match.group(1)

    return None


# ======================================
# VYKRESLENÍ SL / TP DO OBRÁZKU
# ======================================
def draw_sl_tp(image, df, sl, tp1, tp2):
    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)
    w, h = img.size

    price_min = df["close"].min()
    price_max = df["close"].max()
    price_range = price_max - price_min

    def price_to_y(price):
        return int(h * (1 - (price - price_min) / price_range))

    def draw_level(y, label, color):
        draw.rectangle([(0, y - 6), (w, y + 6)], outline=color, width=3)
        draw.rectangle([(10, y - 28), (160, y - 6)], fill=(0, 0, 0, 180))
        draw.text((15, y - 24), label, fill="white")

    if sl:
        draw_level(price_to_y(sl), "STOP LOSS", "red")
    if tp1:
        draw_level(price_to_y(tp1), "TP1", "green")
    if tp2:
        draw_level(price_to_y(tp2), "TP2", "green")

    return img


# ======================================
# REŽIMY
# ======================================
mode = st.radio(
    "Vyber režim:",
    ["Screenshot analýza", "Data analýza"]
)


# ======================================
# SCREENSHOT ANALÝZA
# ======================================
if mode == "Screenshot analýza":
    st.header("Screenshot analýza")

    uploaded_file = st.file_uploader(
        "Nahraj screenshot grafu",
        type=["png", "jpg", "jpeg"]
    )

    analyze_button = st.button("Vygenerovat analýzu")

    if uploaded_file and analyze_button:
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)
        st.info("Screenshot režim zatím pouze vizuální (bez API).")


# ======================================
# DATA ANALÝZA
# ======================================
else:
    st.header("Data analýza (TwelveData)")

    uploaded_file = st.file_uploader(
        "Nahraj screenshot grafu",
        type=["png", "jpg", "jpeg"]
    )

    timeframe = st.selectbox(
        "Timeframe:",
        ["1min", "5min", "15min", "1h", "4h"]
    )

    pair_manual = st.text_input(
        "Měnový pár (EURUSD nebo EUR/USD – volitelné):"
    )

    analyze_button = st.button("Analyzovat")

    if uploaded_file and analyze_button:
        image = Image.open(uploaded_file)

        # OCR → fallback na ruční vstup
        pair_raw = detect_currency_pair(image)
        if pair_manual:
            pair_raw = pair_manual

        pair = normalize_pair(pair_raw)

        st.write("DEBUG – OCR/INPUT:", pair_raw)
        st.write("DEBUG – NORMALIZOVANÝ SYMBOL:", pair)
        st.write("DEBUG – TIMEFRAME:", timeframe)

        if not pair:
            st.error("Nepodařilo se rozpoznat platný měnový pár.")
            st.stop()

        try:
            df = td.get_ohlc(pair, timeframe)

            trend, signal, indicators = td.determine_trend(df)
            sl, tp1, tp2 = td.calculate_sl_tp(df, signal)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Původní graf")
                st.image(image, use_column_width=True)

            with col2:
                st.subheader("Analýza")
                annotated = draw_sl_tp(image, df, sl, tp1, tp2)
                st.image(annotated, use_column_width=True)

            st.markdown("### Výsledek")
            st.write("**Pár:**", pair)
            st.write("**Trend:**", trend)
            st.write("**Signál:**", signal)

            st.markdown("**Indikátory:**")
            for k, v in indicators.items():
                st.write(f"- {k}: {v:.5f}")

            if sl:
                st.success(f"SL: {sl:.5f} | TP1: {tp1:.5f} | TP2: {tp2:.5f}")
            else:
                st.warning("Není vhodná doba pro obchod – SL/TP nebyly stanoveny.")

        except Exception as e:
            st.error(f"Chyba při načítání nebo výpočtu: {e}")
