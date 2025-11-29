import streamlit as st
from PIL import Image

# ==========================
# ZÁKLADNÍ NASTAVENÍ STRÁNKY
# ==========================
st.set_page_config(
    page_title="FX Chart Assistant",
    layout="wide"
)

st.title("📈 FX Chart Assistant – prototyp")
st.write(
    "Nahraj screenshot grafu (MT4/MT5/TradingView) a appka ti k němu ukáže demo analýzu.\n"
    "_Zatím jen ukázková verze – bez reálné AI logiky._"
)

st.sidebar.header("ℹ️ Jak to použít")
st.sidebar.write(
    """
    **1. Udělej screenshot grafu**  
    - MT4/MT5 / TradingView / cokoliv.

    **2. Ulož ho jako obrázek (PNG/JPG).**  
    - Windows: `Win + Shift + S` → uložit.  
    - Mac: `CMD + Shift + 4` → obrázek na plochu.

    **3. Nahraj ho sem do aplikace.**

    Zatím se zobrazuje jen demo textová analýza.
    Později přidáme reálnou AI logiku (trend, S/R, SL/TP).
    """
)

# ==========================
#  KLASICKÝ UPLOAD SOUBORU
# ==========================
uploaded_file = st.file_uploader(
    "Nahraj screenshot grafu (PNG / JPG)",
    type=["png", "jpg", "jpeg"]
)

# ==========================
#  LAYOUT STRÁNKY
# ==========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🖼 Zobrazení grafu")

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Nahraný screenshot grafu", use_column_width=True)
    else:
        st.info("Zatím není žádný obrázek. Nahraj screenshot grafu nahoře.")

with col2:
    st.subheader("🧠 Demo analýza grafu")

    if uploaded_file is not None:
        st.write(
            """
            _Poznámka: Tohle je zatím jen ukázkový text, žádná skutečná AI analýza._

            **Detekce (fake demo):**
            - Trend: mírný uptrend (jen příklad).
            - Možná support zóna: oblast posledních spodních knotů.
            - Možná rezistence: předchozí swing high.
            - SL: pod posledním lokálním minimem.
            - TP1: první výraznější rezistence.
            - TP2: druhé výraznější swing high.

            **Plán do další verze:**
            - vzít obrázek → poslat do AI / logiky,
            - identifikovat trend a S/R zóny,
            - navrhnout konkrétní SL/TP podle volatility a timeframe.
            """
        )
    else:
        st.info("Až nahraješ obrázek, zobrazí se tady demo analýza.")
