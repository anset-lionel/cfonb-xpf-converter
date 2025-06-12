import streamlit as st
from datetime import datetime
import math
import pandas as pd
from io import BytesIO
from fpdf import FPDF

st.title("Convertisseur CFONB EUR ➞ XPF + Contrôle PDF")

# Taux de conversion fixe
conversion_rate = 0.00838

uploaded_file = st.file_uploader("Importer un fichier CFONB", type=None)

if uploaded_file:
    if len(uploaded_file.name.strip()) == 0:
        st.warning("⚠️ Le fichier n'a pas d'extension, vérifie bien qu'il s'agit d'un fichier CFONB.")

    lines = uploaded_file.read().decode("iso-8859-1").splitlines()
    converted_lines = []
    pdf_data = []

    for line in lines:
        if line.startswith("0602"):
            try:
                name = line[30:54].strip()
                original_amount_str = line[102:118]
                original_amount = int(original_amount_str)

                # Conversion avec arrondi supérieur
                euros = original_amount / 100
                xpf = math.ceil(euros / conversion_rate)
                new_amount_str = str(xpf).rjust(16, "0")

                line = line[:102] + new_amount_str + line[118:]

                pdf_data.append({"Nom-Prénom": name, "Montant (XPF)": xpf})
            except ValueError:
                pass

        elif line.startswith("0802"):
            try:
                total_eur = int(line[102:118])
                total_xpf = math.ceil((total_eur / 100) / conversion_rate)
                new_total_str = str(total_xpf).rjust(16, "0")
                line = line[:102] + new_total_str + line[118:]
            except ValueError:
                pass

        converted_lines.append(line)

    # Nom de fichier texte de sortie
    today_str = datetime.now().strftime("%y%m%d")
    output_filename = f"VIRT_Cfonb_SAN{today_str}.txt"
    output_content = "\n".join(converted_lines)

    st.download_button(
        label="💾 Télécharger le fichier converti",
        data=output_content,
        file_name=output_filename,
        mime="text/plain"
    )

    # Génération du PDF de contrôle
    if pdf_data:
        df = pd.DataFrame(pdf_data)
        df = df.sort_values(by="Nom-Prénom")
        total_xpf = df["Montant (XPF)"].sum()

        class PDF(FPDF):
            def header(self):
                self.set_font("Arial", "B", 12)
                self.cell(0, 10, "Contrôle des virements CFONB", 0, 1, "C")

        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)

        for _, row in df.iterrows():
            pdf.cell(100, 8, row["Nom-Prénom"], border=1)
            pdf.cell(40, 8, f"{row['Montant (XPF)']:,}".replace(",", " "), border=1, ln=1)

        pdf.set_font("Arial", "B", 10)
        pdf.cell(100, 8, "Total", border=1)
        pdf.cell(40, 8, f"{total_xpf:,}".replace(",", " "), border=1, ln=1)

        pdf_bytes = pdf.output(dest="S").encode("latin1")
        pdf_buffer = BytesIO(pdf_bytes)


        st.download_button(
            label="📄 Télécharger le PDF de contrôle",
            data=pdf_buffer,
            file_name=f"controle_CFONB_{today_str}.pdf",
            mime="application/pdf"
        )
