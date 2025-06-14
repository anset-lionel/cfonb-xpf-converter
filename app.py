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
    compte_emetteur = ""
    ligne_entete = ""

    for line in lines:
        if line.startswith("0302"):
            compte_emetteur = line[91:102].strip()
            date_jjmma = datetime.now().strftime("%d%j")[:5]  # JJ + MMA
            raison_sociale = "ANSET ASSURANCES AREAS41" if compte_emetteur == "05034250001" else "ANSET ASSURANCES"
            raison_sociale = raison_sociale.ljust(24)[:24]
            devise = "F"
            ligne_entete = (
                "0302" +
                " " * 22 +
                date_jjmma +
                raison_sociale +
                " " * (81 - 30 - 24) +
                devise +
                line[82:160]
            )
            continue

        if line.startswith("0602"):
            try:
                name = line[18:42].strip().ljust(24)[:24]      # colonne 19 à 42
                banque = line[42:74].strip().ljust(32)[:32]     # colonne 43 à 74 (32 caractères au total)
                code_guichet = line[74:79].strip().rjust(5, '0')  # colonne 75 à 79
                num_compte = line[79:90].strip().rjust(11, '0')   # colonne 80 à 90
                original_amount_str = line[90:106]               # colonne 91 à 106
                original_amount = int(original_amount_str)
                libelle = line[106:136].ljust(30)[:30]           # colonne 107 à 136
                code_banque = line[150:160].strip().rjust(10)    # colonne 151 à 160

                euros = original_amount / 100
                xpf = math.ceil(euros / conversion_rate)
                new_amount_str = str(xpf).rjust(16, "0")        # colonne 91 à 106

                new_line = (
                    line[:18] +       # Zone libre 1
                    name +            # colonne 19 à 42
                    banque +          # colonne 43 à 74 (manuelle)
                    code_guichet +    # colonne 75 à 79
                    num_compte +      # colonne 80 à 90
                    new_amount_str +  # colonne 91 à 106
                    libelle +         # colonne 107 à 136
                    line[136:150] +   # reste inchangé jusqu’à colonne 150
                    code_banque       # colonne 151 à 160
                )
                new_line = new_line[:160]

                converted_lines.append(new_line)

                pdf_data.append({"Nom-Prénom": name.strip(), "Montant (XPF)": xpf})
                excel_data.append({
                    "NOM PRENOM": name.strip(),
                    "CODE BANQUE": code_banque.strip(),
                    "NUM DE COMPTE": num_compte.strip(),
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
                converted_lines.append(line[:160])
            except ValueError:
                converted_lines.append(line[:160])
        else:
            converted_lines.append(line[:160])

    st.subheader("🔍 Vérification du compte émetteur")
    st.markdown(f"**Compte détecté dans le fichier :** `{compte_emetteur}`")
    compte_suggere = "05034250001" if compte_emetteur != "05034250001" else "50342500078"
    st.markdown(f"**Suggestion :** Souhaites-tu utiliser le compte proposé `{compte_suggere}` à la place ?")
    use_suggested = st.radio("Utiliser le compte suggéré ?", ("Oui", "Non"))

    compte_emetteur_corrige = compte_suggere if use_suggested == "Oui" else compte_emetteur

    if ligne_entete:
        ligne_entete = ligne_entete[:91] + compte_emetteur_corrige.rjust(11, "0") + ligne_entete[102:160]
        converted_lines.insert(0, ligne_entete[:160])

    nb_virements = len(pdf_data)
    montant_total = sum([row["Montant (XPF)"] for row in pdf_data])

    st.subheader("📊 Récapitulatif de l'ordre de virement")
    st.markdown(f"**Nombre de personnes à virer :** {nb_virements}")
    st.markdown(f"**Montant total des virements :** {montant_total:,} XPF".replace(",", " "))
    st.markdown(f"**Compte émetteur :** {compte_emetteur_corrige}")

    today_str = datetime.now().strftime("%y%m%d")
    output_filename = f"VIRT_Cfonb_SAN{today_str}.txt"
    output_content = "\n".join(converted_lines)

    st.download_button(
        label="💾 Télécharger le fichier converti",
        data=output_content,
        file_name=output_filename,
        mime="text/plain"
    )

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
