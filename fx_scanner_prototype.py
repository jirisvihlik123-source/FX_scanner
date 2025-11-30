import streamlit as st
from PIL import Image, ImageDraw

# ======================================
# ZAKLADNI NASTAVENI STRANKY
# ======================================
st.set_page_config(
    page_title="FX Chart Assistant",
    layout="wide"
)

st.title("FX Chart Assistant – screenshot + data rezim")
st.write(
    "Vyber rezim analyzy. Screenshot rezim funguje, Data rezim je pripraveny a API se prida pozdeji."
)

# ======================================
# REZIMY
# ======================================
mode = st.radio(
    "Vyber rezim:",
    ["Screenshot analyza", "Data analyza (TwelveData – zatim bez API)"]
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
        if s
