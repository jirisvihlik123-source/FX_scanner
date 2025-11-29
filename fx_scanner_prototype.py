import streamlit as st
from PIL import Image, ImageDraw


st.set_page_config(
    page_title="FX scanner",
    layout="wide"
)

st.title("FX scanner – alfa 1.0")
st.write(
    "Nahraj screenshot grafu (MT4/MT5/TradingView) a appka ti ukáže grafickou ukázku SL / ENTRY / TP zón.\n"
    "_Zatím jen ukázkové rozkreslení._"
)

st.sidebar.header("Jak to použít")
st.sidebar.write(
    """
    **1. Udělej screenshot grafu(pro Vojtu snímek obrazovky)**  
    - MT4/MT5 / TradingView / cokoliv.

    **2. Ulož ho jako obrázek (PNG/JPG).**  

    **3. Nahraj ho sem.**  

    Appka:
    - vlevo ukáže původní screenshot,
    - vpravo zobrazí stejný graf s nakreslenými zónami:
      - TP1, ENTRY, SL (jen demo pozice).
    """
)


uploaded_file = st.file_uploader(
    "Nahraj screenshot grafu (PNG / JPG)",
    type=["png", "jpg", "jpeg"]
)


def annotate_chart(image: Image.Image) -> Image.Image:
    """
    Vezme obrázek grafu a nakreslí na něj:
    - SL zónu dole
    - ENTRY někde uprostřed
    - TP1/TP2 nahoře

    Jedná se pouze o demo.
    """
    img = image.convert("RGBA")
    draw = ImageDraw.Draw(img)

    w, h = img.size

    
    sl_y = int(h * 0.75)      
    entry_y = int(h * 0.55)   
    tp1_y = int(h * 0.35)     
    tp2_y = int(h * 0.20)     

    
    def draw_level(y: int, label: str, color: str):
        draw.line([(0, y), (w, y)], fill=color, width=3)

        draw.rectangle([(10, y - 22), (110, y - 2)], fill=(0, 0, 0, 160))
        draw.text((15, y - 20), label, fill="white")

    draw_level(sl_y, "SL zóna (demo)", "#ff4b4b")
    draw_level(entry_y, "ENTRY (demo)", "#facc15")
    draw_level(tp1_y, "TP1 (demo)", "#22c55e")
    draw_level(tp2_y, "TP2 (demo)", "#16a34a")

    return img


col1, col2 = st.columns(2)

with col1:
    st.subheader("1)Původní graf")

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Nahraný screenshot grafu", use_column_width=True)
    else:
        st.info("Zatím není žádný obrázek. Nahraj screenshot grafu nahoře.")

with col2:
    st.subheader("2)Grafická demo analýza")

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        annotated = annotate_chart(image)
        st.image(annotated, caption="Graf s vyznačenými demo SL/ENTRY/TP zónami", use_column_width=True)

        st.markdown(
            """
            ### Co to teď dělá:
            - Zóny jsou nakreslené jen **podle výšky obrázku**, ne podle skutečné ceny.
            - Slouží jako ukázka, jak může vypadat grafická analýza.

            ### Další krok do budoucna:
            - Napojit to na reálná data (OHLC),
            - nebo použít AI model, který čte z obrázku svíčky / patterny.
            """
        )
    else:
        st.info("Až nahraješ obrázek, zobrazí se tady verze s demo zónami.")
