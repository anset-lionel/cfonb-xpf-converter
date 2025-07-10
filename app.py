import streamlit as st
from datetime import datetime
import math
import pandas as pd
from io import BytesIO
from fpdf import FPDF

st.title("Convertisseur CFONB EUR ➞ XPF + Contrôle PDF & Excel")

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
    erreurs_format = []

    for i, line in enumerate(lines):
        if line.startswith("0602"):
            try:
                code_virement = "0602"  # Code fixe pour identifiant de ligne CFONB
                nom_prenom = line[18:42].ljust(24)           # Col 19–42
                banque = line[42:74].strip().ljust(32)       # Col 43–74
                code_guichet = line[74:79].strip().rjust(5, '0')  # Col 75–79
                num_compte = line[79:90].strip().rjust(11, '0')   # Col 80–90
                original_amount_str = line[90:106]               # Col 91–106
                euros = int(original_amount_str) / 100
                xpf = math.ceil(euros / conversion_rate)
                montant_xpf = str(xpf).rjust(16, "0")            # Col 91–106
                libelle = line[106:136].ljust(30)[:30]            # Col 107–136
                filler = " " * 14                                 # Col 137–150
                code_banque = line[150:160].strip().rjust(10)     # Col 151–160

                new_line = (
                    code_virement +
                    "" +  # suppression des 13 espaces
                    " " * 25 +  # effacer les 25 caractères suivants sauf pour première/dernière ligne si besoin

                    code_virement +
                    " " * 13 +
                    nom_prenom +
                    banque +
                    code_guichet +
                    num_compte +
                    montant_xpf +
                    libelle +
                    filler +
                    code_banque
                )[:160]

                if len(new_line) != 160:
                    erreurs_format.append((i + 1, len(new_line), new_line))

                converted_lines.append(new_line)

                pdf_data.append({"Nom-Prénom": nom_prenom.strip(), "Montant (XPF)": xpf})
                excel_data.append({
                    "NOM PRENOM": nom_prenom.strip(),
                    "CODE BANQUE": code_banque.strip(),
                    "NUM DE COMPTE": num_compte.strip(),
                    "MONTANT DU VIREMENT": xpf
                })
            except ValueError:
                converted_lines.append(line)

        elif line.startswith("0802"):
            try:
                total_eur = int(line[102:118])
                total_xpf = math.ceil((total_eur / 100) / conversion_rate)
                new_total_str = str(total_xpf).rjust(16, "0")
                line = line[:102] + new_total_str + line[118:]
                if len(line[:160]) != 160:
                    erreurs_format.append((i + 1, len(line[:160]), line[:160]))
                converted_lines.append(line[:160])
            except ValueError:
                converted_lines.append(line[:160])

        elif line.startswith("0302"):
            today = datetime.now()
            jjmma = today.strftime("%d%j")[:5]
            compte_emetteur = "05034250001"
            entete = (
                "0302" + " " * 21 + jjmma +
                "ANSET ASSURANCES".ljust(24) +
                " " * 26 +
                "F" + " " * 5 + "00001" + compte_emetteur.rjust(11, '0') +
                " " * 47 + "17469"
            )
            converted_lines.append(entete[:160])

        else:
            if len(line[:160]) != 160:
                erreurs_format.append((i + 1, len(line[:160]), line[:160]))
            converted_lines.append(line[:160])

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

    # Affichage des erreurs de longueur
    if erreurs_format:
        st.error("❌ Certaines lignes ne font pas 160 caractères :")
        for num_ligne, longueur, contenu in erreurs_format:
            st.code(f"Ligne {num_ligne} ({longueur} car.): {contenu}")

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
