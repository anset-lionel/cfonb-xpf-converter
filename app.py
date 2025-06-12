import streamlit as st
from datetime import datetime
import math

st.title("Convertisseur CFONB EUR ➞ XPF")

# Taux de conversion fixe
conversion_rate = 0.00838

uploaded_file = st.file_uploader("Importer un fichier CFONB", type=None)

if uploaded_file:
    lines = uploaded_file.read().decode("iso-8859-1").splitlines()
    converted_lines = []

    for line in lines:
        if line.startswith("0602") or line.startswith("0802"):
            try:
                original_amount_str = line[102:118]
                original_amount = int(original_amount_str)

                # Conversion avec arrondi supérieur
                euros = original_amount / 100
                xpf = math.ceil(euros / conversion_rate)

                # Format 16 caractères, aligné à droite, sans les centimes (XPF entier)
                new_amount_str = str(xpf).rjust(16, "0")

                # Remplacement dans la ligne CFONB
                line = line[:102] + new_amount_str + line[118:]
            except ValueError:
                pass  # si une ligne est mal formatée, on la laisse telle quelle

        converted_lines.append(line)

    # Nom de fichier de sortie
    today_str = datetime.now().strftime("%y%m%d")
    output_filename = f"VIRT_Cfonb_SAN{today_str}.txt"
    output_content = "\n".join(converted_lines)

    st.download_button(
        label="💾 Télécharger le fichier converti",
        data=output_content,
        file_name=output_filename,
        mime="text/plain"
    )
