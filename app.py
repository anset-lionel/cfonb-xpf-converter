import streamlit as st
import datetime
import io
import re

CONVERSION_RATE = 119.33  # 1 EUR = 119.33 XPF

st.title("Convertisseur CFONB Euro vers XPF")

uploaded_file = st.file_uploader("Téléversez votre fichier CFONB en euros")

if uploaded_file:
    raw_lines = uploaded_file.read().decode("latin-1").splitlines()
    converted_lines = []
    total_amount = 0

    for line in raw_lines:
        line = line.ljust(160)[:160]  # Assurer une longueur de 160
        code_type = line[:4]

        if code_type == "0302":
            cleaned_line = re.sub(r"489308\d*", " " * 12, line)  # supprime 489308 et variantes numérotées
            converted_lines.append(cleaned_line.ljust(160)[:160])

        elif code_type == "0602":
            # Supprimer les zones contenant 489308 ou 48930845 et leur suffixe numérique éventuel
            clean_line = re.sub(r"489308\d*-?\d*", " " * 23, line)
            clean_line = clean_line.ljust(160)[:160]

            # Extraire et convertir le montant en euro à la position 100-114
            montant_euro_str = clean_line[100:114]
            try:
                montant_euro = int(montant_euro_str)
                montant_xpf = int(round(montant_euro * CONVERSION_RATE))
                total_amount += montant_xpf

                # Reconstituer la ligne avec le montant XPF
                new_montant_str = str(montant_xpf).rjust(14, '0')
                final_line = clean_line[:100] + new_montant_str + clean_line[114:160]
                converted_lines.append(final_line)
            except ValueError:
                st.error(f"Montant invalide dans la ligne : {line}")
                converted_lines.append(clean_line)

        elif code_type == "0802":
            continue  # on va recréer cette ligne proprement après

        else:
            converted_lines.append(line)

    # Ajouter une ligne 0802 de total
    total_line = f"0802TOTAL{' ' * 87}{str(total_amount).rjust(14, '0')}{' ' * (160 - 109)}"
    converted_lines.append(total_line)

    # Aperçu
    st.subheader("Aperçu du fichier converti")
    for l in converted_lines[:10]:
        st.text(l)

    # Télécharger le fichier
    output = io.StringIO()
    for line in converted_lines:
        output.write(line + "\n")

    st.download_button(
        label="Télécharger le fichier CFONB converti",
        data=output.getvalue(),
        file_name="cfobn_xpf_converti.txt",
        mime="text/plain"
    )
