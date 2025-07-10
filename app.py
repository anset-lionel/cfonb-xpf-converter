import streamlit as st
from datetime import datetime
import math
import pandas as pd
from io import BytesIO
from fpdf import FPDF

st.title("Convertisseur CFONB EUR ➞ XPF — Format officiel 160 colonnes")

conversion_rate = 0.00838

uploaded_file = st.file_uploader("Importer un fichier CFONB", type=None)

if uploaded_file:
    lines = uploaded_file.read().decode("iso-8859-1").splitlines()
    converted_lines = []
    pdf_data = []
    excel_data = []
    erreurs_format = []
    total_xpf = 0

    for i, line in enumerate(lines):
        if line.startswith("0302"):
            today = datetime.now()
            jjmma = today.strftime("%d%j")[:5]
            compte_emetteur = "05034250001"
            libelle = "ANSET ASSURANCES AREAS41" if compte_emetteur == "05034250001" else "ANSET ASSURANCES"

            entete = (
                "0302" +
                " " * 21 +
                jjmma +
                libelle.ljust(24) +
                " " * 26 +
                "F" +
                " " * 5 +
                "00001" + compte_emetteur.rjust(11, '0') +
                " " * 47 +
                "17469"
            )
            converted_lines.append(entete[:160])

        elif line.startswith("0602"):
            try:
                code_mouvement = "0602"
                espace_vide = " " * 26  # col 5 à 30

                nom_prenom = line[30:54].strip().upper().ljust(24)
                banque = line[54:86].strip().upper().ljust(32)
                code_guichet = line[86:91].strip().rjust(5, "0")
                compte = line[91:102].strip().rjust(11, "0")

                montant_eur_cents = int(line[102:118])
                montant_xpf = math.ceil((montant_eur_cents / 100) / conversion_rate)
                total_xpf += montant_xpf
                montant_cfonb = str(montant_xpf).rjust(16, "0")

                libelle = "Rglt Anset Santé RS0".ljust(31)
                code_banque = line[149:154].strip().rjust(5)

                new_line = (
                    code_mouvement +
                    espace_vide +
                    nom_prenom +
                    banque +
                    code_guichet +
                    compte +
                    montant_cfonb +
                    libelle +
                    code_banque
                ).ljust(160)[:160]

                if len(new_line) != 160:
                    erreurs_format.append((i + 1, len(new_line), new_line))

                converted_lines.append(new_line)

                pdf_data.append({"Nom-Prénom": nom_prenom.strip(), "Montant (XPF)": montant_xpf})
                excel_data.append({
                    "NOM PRENOM": nom_prenom.strip(),
                    "CODE BANQUE": code_banque.strip(),
                    "NUM DE COMPTE": compte.strip(),
                    "MONTANT DU VIREMENT": montant_xpf
                })

            except Exception as e:
                erreurs_format.append((i + 1, len(line), f"[ERREUR PARSE] {line}"))
                converted_lines.append(line[:160])

        elif line.startswith("0802"):
            try:
                montant_total_str = str(total_xpf).rjust(16, "0")
                new_footer = line[:102] + montant_total_str + line[118:]
                converted_lines.append(new_footer[:160])
            except:
                erreurs_format.append((i + 1, len(line), "[ERREUR TOTAL]"))
                converted_lines.append(line[:160])

        else:
            converted_lines.append(line[:160])

    # Export .txt
    today_str = datetime.now().strftime("%y%m%d")
    output_txt = "\n".join(converted_lines)
    st.download_button("💾 Télécharger le fichier CFONB", output_txt, file_name=f"VIRT_Cfonb_SAN{today_str}.txt")

    # Erreurs de format
    if erreurs_format:
        st.error("❌ Certaines lignes ne font pas 160 caractères ou sont incorrectes :")
        for num, length, content in erreurs_format:
            st.code(f"Ligne {num} ({length} car.) : {content}")

    # Export PDF
    if pdf_data:
        df = pd.DataFrame(pdf_data).sort_values(by="Nom-Prénom")
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
        st.download_button(
            "📄 Télécharger le PDF de contrôle",
            data=BytesIO(pdf_bytes),
            file_name=f"controle_CFONB_{today_str}.pdf"
        )

    # Export Excel
    if excel_data:
        df_excel = pd.DataFrame(excel_data)
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            df_excel.to_excel(writer, index=False, sheet_name="Contrôle Virements")
        excel_buffer.seek(0)

        st.download_button(
            "📄 Télécharger le fichier Excel de contrôle",
            data=excel_buffer,
            file_name=f"controle_CFONB_{today_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
