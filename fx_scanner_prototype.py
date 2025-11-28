import streamlit as st
from PIL import Image
import io
import base64

# JS pro zachycení vloženého obrázku
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

# Neviditelný input na vložený obrázek
pasted_image = st.text_input("Sem můžeš vložit obrázek pomocí CTRL + V", key="paste-image-input")

image_from_paste = None
if pasted_image.startswith("data:image"):
    header, encoded = pasted_image.split(",", 1)
    image_data = base64.b64decode(encoded)
    image_from_paste = Image.open(io.BytesIO(imag


