# fx_scanner_prototype.py
import streamlit as st
from PIL import Image
import twelvedata_api as td
import easyocr
import re
import numpy as np
from chart_generator import draw_chart

st.set_page_config(page_title="FX Chart Assistant", layout="wide")
st.title("FX Chart Assistant – screenshot + data režim")
st.write("Vyber režim analýzy.")

# režim
mode = st.radio("Vyber režim:", ["Screenshot analýza", "Data analýza"])

# funkce OCR
def detect_currency_pair(image):
    reader = easyocr.Reader(['en'])
    img_array = np.array(image)
    results = reader.readtext(img_array)
    text = " ".join([res[1] for res in results])
    match = re.search(r'\b([A-Z]{3}/[A-Z]{3})\b', text)
    if match:
        return match.group(1).replace("/", "").upper()
    return None

# screenshot analyza (zůstává jednoduchá)
def annotate_chart_with_strategy(image, direction, strategy, rrr):
    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img) if hasattr(Image, "Draw") else None
    # jednoduché zabarvení a text
    return img, "Screenshot analyza (vizualizace)"

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
            st.image(Image.open(uploaded_file), use_column_width=True)
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

    indicator_options = ["EMA50", "EMA200", "RSI", "ADX"]
    selected_indicators = st.multiselect("Zobrazit indikátory v grafu:", indicator_options, default=indicator_options)

    pair_input = st.text_input("Měnový pár (volitelně, OCR):")
    analyze_button = st.button("Analyzovat")

    if uploaded_file and analyze_button:
        image = Image.open(uploaded_file)

        # OCR navrh
        detected = detect_currency_pair(image)
        st.write("OCR návrh páru:", detected)

        pair = pair_input if pair_input else (detected if detected else "")
        pair = pair.replace("/", "").upper()

        if not pair:
            st.error("Nepodařilo se rozpoznat měnový pár. Zadej ho ručně.")
        else:
            try:
                st.write("DEBUG – pair:", pair)
                st.write("DEBUG – timeframe:", timeframe)

                df = td.get_ohlc(pair, timeframe)
                trend, signal, ind_values = td.determine_trend(df)
                sl, tp1, tp2 = td.calculate_sl_tp(df, signal)

                # Pokud trend není vhodný, ponecheme None a nabídneme doporučení
                if sl is None or trend == "Neutrální":
                    # spočítat ATR pro doporučení
                    atr = df['high'].rolling(14).max().iloc[-1] - df['low'].rolling(14).min().iloc[-1]
                    st.warning(f"Není vhodná doba pro SL/TP podle pravidel strategie. Doporučená velikost SL (ATR): {atr:.5f}")
                    # Můžeme ale doplnit navrhované SL/TP pro vizualizaci (volitelné)
                    # zde ponecháme sl,tp1,tp2 None -> draw_chart je vykreslí pouze pokud nejsou None

                # vykreslení grafu (draw_chart vrací fig)
                fig = draw_chart(
                    df=df,
                    ema50=ind_values.get("EMA50"),
                    ema200=ind_values.get("EMA200"),
                    rsi=ind_values.get("RSI"),
                    adx=ind_values.get("ADX"),
                    signal=signal,
                    sl=sl,
                    tp1=tp1,
                    tp2=tp2,
                    show_ema50=("EMA50" in selected_indicators),
                    show_ema200=("EMA200" in selected_indicators),
                    show_rsi=("RSI" in selected_indicators),
                    show_adx=("ADX" in selected_indicators)
                )

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Původní graf")
                    st.image(image, use_column_width=True)
                with col2:
                    st.subheader("Graf s indikátory")
                    st.pyplot(fig)

                st.markdown("### Indikátory (poslední hodnoty)")
                for k, v in ind_values.items():
                    if k.startswith("_"):
                        continue
                    st.write(f"- {k}: {v if v is not None else '–'}")

            except Exception as e:
                st.error(f"Chyba při načítání nebo výpočtu: {e}")
