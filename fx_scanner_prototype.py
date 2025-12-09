import sys
import os
import streamlit as st
from PIL import Image, ImageDraw
import plotly.graph_objects as go

# ======================================================
# Přidání složky s twelvedata_api.py do sys.path
# ======================================================
sys.path.append(os.path.join(os.path.dirname(__file__), "api"))
from twelvedata_api import (
    get_ohlc,
    calculate_ema,
    calculate_rsi,
    calculate_adx,
    determine_trend,
    calculate_sl_tp
)

# ======================================
# ZAKLADNI NASTAVENI STRANKY
# ======================================
st.set_page_config(
    page_title="FX Chart Assistant",
    layout="wide"
)

st.title("FX Chart Assistant – screenshot + data rezim")
st.write(
    "Vyber rezim analyzy. Screenshot rezim funguje, Data rezim je pripraveny s TwelveData API."
)

# ======================================
# REZIMY
# ======================================
mode = st.radio(
    "Vyber rezim:",
    ["Screenshot analyza", "Data analyza"]
)

# =============================================================
# =================  REZIM 1 – SCREENSHOT ANALYZA =============
# =============================================================
if mode == "Screenshot analyza":

    st.header("Screenshot analyza")

    st.sidebar.header("Nastaveni strategie")

    direction = st.sidebar.radio(
        "Smer obchodu:",
        ["Long (buy)", "Short (sell)"]
    )

    strategy = st.sidebar.selectbox(
        "Strategie:",
        [
            "Swing - pullback",
            "Breakout - pruraz",
            "Range - obchod v pasmu"
        ]
    )

    rrr = st.sidebar.slider(
        "RRR (Risk Reward):",
        min_value=1.0,
        max_value=4.0,
        value=2.0,
        step=0.5
    )

    uploaded_file = st.file_uploader(
        "Nahraj screenshot grafu:",
        type=["png", "jpg", "jpeg"]
    )

    analyze_button = st.button("Vygenerovat analyzu")

    # =====================================================
    # ============ FUNKCE PRO VYKRESLENI ZON ===============
    # =====================================================
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

        # kreslici funkce
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

Poznamka: Zona je relativni k obrazku (demo).
"""

        return img, description

    # =====================================================
    # ============ LAYOUT APPKY ===========================
    # =====================================================
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
            annotated, desc = annotate_chart_with_strategy(
                original, direction, strategy, rrr
            )
            st.image(annotated, use_column_width=True)
            st.markdown(desc)
        else:
            st.info("Nahraj screenshot a klikni na tlacitko.")


# =============================================================
# ==================  REZIM 2 – DATA ANALYZA ==================
# =============================================================
elif mode == "Data analyza":

    st.header("Data analyza (TwelveData API)")

    pair = st.text_input("Menovy par:", "EUR/USD")
    timeframe = st.selectbox(
        "Timeframe:",
        ["1min", "5min", "15min", "1h", "4h"]
    )

    st.subheader("Vyber indikátory k vykreslení")
    show_ema50 = st.checkbox("EMA 50", value=True)
    show_ema200 = st.checkbox("EMA 200", value=True)
    show_rsi = st.checkbox("RSI 14", value=True)
    show_adx = st.checkbox("ADX", value=True)

    go_btn = st.button("Analyzovat")

    if go_btn:
        try:
            df = get_ohlc(pair, timeframe)

            # vypočítáme jen vybrané indikátory
            if show_ema50:
                df["EMA50"] = calculate_ema(df, 50)
            if show_ema200:
                df["EMA200"] = calculate_ema(df, 200)
            if show_rsi:
                df["RSI14"] = calculate_rsi(df, 14)
            if show_adx:
                df["ADX14"] = calculate_adx(df, 14)

            # správné přiřazení z determine_trend
            trend_signal, signal, indicators = determine_trend(df)
            sl, tp1, tp2 = calculate_sl_tp(df, signal)

            st.subheader("Výsledky")
            st.markdown(f"**Trend:** {trend_signal}")
            st.markdown(f"**Signal:** {signal}")
            st.markdown(f"**Stop Loss:** {sl}")
            st.markdown(f"**Take Profit 1:** {tp1}")
            st.markdown(f"**Take Profit 2:** {tp2}")

            # ===================== GRAF =====================
            fig = go.Figure()

            # OHLC graf
            fig.add_trace(go.Candlestick(
                x=df.index,
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
                name="OHLC"
            ))

            # EMA linie
            if show_ema50:
                fig.add_trace(go.Scatter(x=df.index, y=df["EMA50"], line=dict(color="blue", width=1), name="EMA50"))
            if show_ema200:
                fig.add_trace(go.Scatter(x=df.index, y=df["EMA200"], line=dict(color="orange", width=1), name="EMA200"))

            fig.update_layout(
                title=f"{pair} – {timeframe}",
                xaxis_title="Čas",
                yaxis_title="Cena",
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                height=600
            )

            st.plotly_chart(fig, use_container_width=True)

            # ===================== RSI a ADX jako podgrafy =====================
            if show_rsi or show_adx:
                fig2 = go.Figure()
                if show_rsi:
                    fig2.add_trace(go.Scatter(x=df.index, y=df["RSI14"], line=dict(color="cyan", width=1), name="RSI14"))
                if show_adx:
                    fig2.add_trace(go.Scatter(x=df.index, y=df["ADX14"], line=dict(color="magenta", width=1), name="ADX14"))

                fig2.update_layout(
                    title="RSI / ADX",
                    xaxis_title="Čas",
                    yaxis_title="Hodnota",
                    template="plotly_dark",
                    height=300
                )
                st.plotly_chart(fig2, use_container_width=True)

            # ===================== TABULKA =====================
            st.subheader("Poslední data s indikátory")
            st.dataframe(df.tail(20))

        except Exception as e:
            st.error(f"Chyba při načítání nebo výpočtu: {e}")










