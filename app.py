import streamlit as st
from datetime import datetime
import math
import pandas as pd
from io import BytesIO
from fpdf import FPDF

st.title("Ordre de virement SANTE ANSET")

# Taux de conversion fixe
conversion_rate = 0.00838

uploaded_file = st.file_uploader("Importer un fichier CFONB", type=None)

if uploaded_file:
    if len(uploaded_file.name.strip()) == 0:
        st.warning("⚠️ Le fichier n'a pas d'extension, vérifie bien qu'il s'agit d'un fichier CFONB.")

    lines = uploaded_file.read().decode("iso-8859-1").splitlines()
    converted_lines = []
    pdf_data = []
    excel_data = []
    compte_emetteur = "Non détecté"

    for line in lines:
        if line.startswith("0302"):
            compte_emetteur = line[91:102].strip()

        if line.startswith("0602"):
            try:
                name = line[30:54].strip()
                code_banque = line[149:154].strip()
                num_compte = line[91:102].strip()
                original_amount_str = line[102:118]
                original_amount = int(original_amount_str)

                # Conversion avec arrondi supérieur
                euros = original_amount / 100
                xpf = math.ceil(euros / conversion_rate)
                new_amount_str = str(xpf).rjust(16, "0")

                line = line[:102] + new_amount_str + line[118:]

                pdf_data.append({"Nom-Prénom": name, "Montant (XPF)": xpf})
                excel_data.append({
                    "NOM PRENOM": name,
                    "CODE BANQUE": code_banque,
                    "NUM DE COMPTE": num_compte,
                    "MONTANT DU VIREMENT": xpf
                })
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

    # Données statistiques pour panneau récapitulatif
    nb_virements = len(pdf_data)
    montant_total = sum([row["Montant (XPF)"] for row in pdf_data])

    st.subheader("📊 Récapitulatif de l'ordre de virement")
    st.markdown(f"**Nombre de personnes à virer :** {nb_virements}")
    st.markdown(f"**Montant total des virements :** {montant_total:,} XPF".replace(",", " "))
    st.markdown(f"**Compte émetteur :** {compte_emetteur}")

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

    # Génération du fichier Excel de contrôle
    if excel_data:
        df_excel = pd.DataFrame(excel_data)
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            df_excel.to_excel(writer, index=False, sheet_name="Contrôle Virements")
        excel_buffer.seek(0)

        st.download_button(
            label="📄 Télécharger le fichier Excel de contrôle",
            data=excel_buffer,
            file_name=f"controle_CFONB_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
