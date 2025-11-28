import streamlit as st
from PIL import Image
import io
import base64

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
                input.value = dataUrl;
                input.dispatchEvent(new Event('change'));
            };
            reader.readAsDataURL(blob);
        }
    }
});
</script>
"""

st.markdown(paste_js, unsafe_allow_html=True)

# Skrytý input pro uložený base64 obrázek
pasted_base64 = st.text_input(
    "Sem můžeš vložit obrázek pomocí CTRL + V",
    key="paste-image-input"
)

# Konverze base64 → PIL Image
image_from_paste = None
if pasted_base64 and pasted_base64.startswith("data:image"):
    header, encoded = pasted_base64.split(",", 1)
    image_bytes = base64.b64decode(encoded)
    image_from_paste = Image.open(io.BytesIO(image_bytes))

