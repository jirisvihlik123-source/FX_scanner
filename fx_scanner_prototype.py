import streamlit as st
from PIL import Image
import io
import base64

# ==========================
# ZÁKLADNÍ NASTAVENÍ STRÁNKY
# ==========================
st.set_page_config(
    page_title="FX Chart Assistant",
    layout="wide"
)

st.title("📈 FX Chart Assistant – prototyp")
st.write(
    "Nahraj nebo vlož screenshot grafu (MT4/MT5/TradingView) a appka ti k němu ukáže demo analýzu.\n"
    "_Zatím jen ukázková verze – bez reálné AI logiky._"
)

# ============================
#  ENABLE CTRL+V IMAGE PASTE
# ============================
paste_js = """
<script>
document.addEventListener('paste', function(event) {
    const items = (event.clipboardData || event.originalEvent.clipboardData).items;
    for (const item of items) {
        if (item.type.indexOf("image") === 0) {
            const blob = item.getAsFile();
            const reader = new FileReader();
            reader.onload = function(event) {
                const dataUrl = event.target.result;
                const input = document.getElementById("paste-image-input");
                if (input) {
                    input.value = dataUrl;
                    input.dispatchEvent(new Event('change'));
                }
            };
            reader.readAsDataURL(blob);
        }
    }
});
</script>
"""

st.markdown(paste_js, unsafe_allow_html=True)

st.sidebar.header("ℹ️ Jak to použít")
st.sidebar.write(
    """
    **Možnosti:**
    - Nahraj screenshot grafu jako soubor (PNG/JPG).
    - Nebo udělej screenshot → zkopíruj ho → klikni na stránku → CTRL+V / CMD+V.

    Zatím se zobrazuje jen demo textová analýza.
    Později sem doplníme reálnou AI logiku, S/R zóny, SL/TP atd.
    """
)

# Skrytý input pro uložený base64 obrázek z clipboardu
pasted_base64 = st.text_input(
    "Sem můžeš vložit obrázek pomocí CTRL + V (klikni sem a pak CTRL+V)",
    key="paste-image-input"
)

# Konverze base64 → PIL Image
image_from_paste = None
if pasted_base64 and pasted_base64.startswith("data:image"):
    try:
        header, encoded = pasted_base64.split(",", 1)
        image_bytes = base64.b64decode(encoded)
        image_from_paste = Image.open(io.BytesIO(image_bytes))
    except Exception:
        image_from_paste = None

# ==========================
#  KLASICKÝ UPLOAD SOUBORU
# ==========================
uploaded_file = st.file_uploader(
    "Nebo nahraj screenshot grafu (PNG / JPG)",
    type=["png", "jpg", "jpeg"]
)

# ==========================
#  LAYOUT STRÁNKY
# ==========================
col1, col2 = st.columns(2)

with col1:
    st.subheader("🖼 Zobrazení grafu")

    if image_from_paste is not None:
        st.image(image_from_paste, caption="Vložený obrázek (Ctrl+V)", use_column_width=True)
    elif uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Nahraný obrázek", use_column_width=True)
    else:
        st.info("Zatím není žádný obrázek. Nahraj soubor nebo klikni do pole výše a použij CTRL+V.")

with col2:
    st.subheader("🧠 Demo analýza grafu")

    if (image_from_paste is not None) or (uploaded_file is not None):
        st.write(
            """
            _Poznámka: Tohle je zatím jen ukázkový text, žádná skutečná AI analýza._

            **Detekce (fake demo):**
            - Trend: mírný uptrend.
            - Možná support zóna: oblast posledních spodních knotů.
            - Možná rezistence: předchozí swing high.
            - SL: pod posledním lokálním minimem.
            - TP1: první výraznější rezistence.
            - TP2: druhé výraznější swing high.

            **Plán do další verze:**
            - vzít obrázek → poslat do AI → přečíst svíčky / patterny,
            - spočítat S/R zóny,
            - navrhnout konkrétní SL/TP podle volatility a timeframe.
            """
        )
    else:
        st.info("Až nahraješ nebo vložíš obrázek, zobrazí se tady demo analýza.")
