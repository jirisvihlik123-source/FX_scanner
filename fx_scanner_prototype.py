import streamlit as st
from PIL import Image, ImageDraw


st.set_page_config(
    page_title="FX Chart Assistant",
    layout="wide"
)

st.title("FX scanner - alfa 1.1")

st.write(a
    "Vyber režim analýzy(demo). Nebo vyber Data rezim(demo)."
)


mode = st.radio(
    "Vyber režim:",
    ["📷 Screenshot analýza", "Data analýza"]
)



if mode == "📷 Screenshot analýza":
    st.header("📷 Screenshot analýza")

    st.sidebar.header("Nastavení strategie (Screenshot)")

    direction = st.sidebar.radio(
        "Směr obchodu:",
        ["Long (buy)", "Short (sell)"]
    )

    strategy = st.sidebar.selectbox(
        "Strategie:",
        [
            "Swing – pullback do zóny",
            "Breakout – průraz rezistence",
            "Range – obchod v pásmu"
        ]
    )

    rrr = st.sidebar.slider(
        "Risk : Reward (RRR)",
        min_value=1.0,
        max_value=4.0,
        value=2.0,
        step=0.5
    )

    uploaded_file = st.file_uploader(
        "Nahraj screenshot grafu (PNG / JPG)",
        type=["png", "jpg", "jpeg"]
    )

    analyze_button = st.button("Vygenerovat analýzu ze screenshotu")


    def annotate_chart_with_strategy(image, direction, strategy, rrr):
        img = image.convert("RGBA")
        draw = ImageDraw.Draw(img)
        w, h = img.size


        base_sl_y = int(h * 0.78)
        base_entry_y = int(h * 0.60)
        base_tp1_y = int(h * 0.40)
        base_tp2_y = int(h * 0.25)


        if direction.startswith("Short"):
            base_sl_y = int(h * 0.22)
            base_entry_y = int(h * 0.40)
            base_tp1_y = int(h * 0.60)
            base_tp2_y = int(h * 0.75)


        if strategy == "Breakout – průraz rezistence":
            if direction.startswith("Long"):
                base_entry_y = int(h * 0.50)
                base_sl_y = int(h * 0.65)
                base_tp1_y = int(h * 0.35)
            else:
                base_entry_y = int(h * 0.50)
                base_sl_y = int(h * 0.35)
                base_tp1_y = int(h * 0.62)

        if strategy == "Range – obchod v pás
