import streamlit as st
from PIL import Image
import io

# ==========================
# ZÁKLADNÍ NASTAVENÍ STRÁNKY
# ==========================
st.set_page_config(
    page_title="FX Chart Assistant",
    layout="wide"
)

st.title("📈 FX Chart Assistant – prototyp")
st.write(
    "Nahraj screenshot grafu (MT4/MT5/TradingView) a aplikace ti k němu vrátí základní analýzu.\n"
    "_Zatím jen demo verze – bez reálné AI analýzy._"
)

# ==========================
# SIDEBAR – INFO
# ==========================
st.sidebar.header("ℹ️ Info")
st.sidebar.write(
    """
    **Jak to funguje teď:**
    1. Nahraješ obrázek grafu (screenshot).
    2. Appka ho zobrazí.
    3. Ukáže ti textovou „fake“ analýzu (zatím napevno – demo).

    Později sem doplníme:
    - AI analýzu (trend, S/R zóny, SL/TP návrhy),
    - případně dokreslení přímo do obrázku.
    """
)

# ==========================
# HLAVNÍ ČÁST – UPLOAD
# ==========================
uploaded_file = st.file_uploader(
    "Nahraj screenshot grafu (PNG / JPG)",
    type=["png", "jpg", "jpeg"]
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("🖼 Nahraný graf")

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, use_column_width=True)
    else:
        st.info("Zatím není nahraný žádný obrázek. Nahraj graf vlevo nahoře.")

with col2:
    st.subheader("🧠 Demo analýza grafu")

    if uploaded_file is not None:
        st.write(
            """
            _Poznámka: Tohle je jen ukázkový text, žádná skutečná AI analýza (zatím)._  

            **Detekce (fake demo):**
            - Trend: mírný uptrend.
            - Možná support zóna: poslední spodní wicky u lokálního dna.
            - Možná rezistence: předchozí swing high.
            - SL: pod posledním lokálním minimem.
            - TP1: první výraznější rezistence.
            - TP2: další swing high.

            Až to doděláme:
            - AI si z obrázku přečte svíčky a patterny.
            - Vypočítá ti S/R zóny a riziko.
            - Vrátí konkrétní SL/TP podle volatility.
            """
        )
    else:
        st.info("Až nahraješ graf, zobrazí se tady demo analýza.")
