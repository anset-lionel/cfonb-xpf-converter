import streamlit as st

TAUX = 119.3317  # Taux fixe euro/XPF

def convert_euro_to_xpf(euro_cents):
    euro = int(euro_cents)
    montant_xpf = round((euro / 100) * TAUX)
    # CFONB: montant sur 16 positions, padding à gauche de zéros
    return str(montant_xpf).rjust(16, "0")

def convert_cfonb(content):
    lines = content.decode("utf-8").splitlines()
    new_lines = []
    for line in lines:
        # On convertit uniquement les lignes de virement (ex: type 0602)
        if line.startswith("0602"):
            # À AJUSTER selon ton fichier source : ici on suppose que le montant est de la position 66 à 81 (index 65 à 81 en Python, car Python commence à 0)
            euro_cents = line[65:81]
            xpf = convert_euro_to_xpf(euro_cents)
            new_line = line[:65] + xpf + line[81:]
            new_lines.append(new_line)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)

st.title("Convertisseur CFONB Euro → XPF")
st.markdown("""
Charge ton **fichier CFONB extrait en euro**.  
Le montant de chaque virement sera converti en XPF, format strict **CFONB**, prêt à importer pour la Polynésie.
""")

uploaded_file = st.file_uploader("Dépose ici ton fichier CFONB en euros (.txt)", type="txt")
if uploaded_file:
    new_content = convert_cfonb(uploaded_file.read())
    st.download_button(
        label="Télécharger le fichier CFONB converti (XPF)",
        data=new_content,
        file_name="CFONB_XPF.txt",
        mime="text/plain"
    )
    st.code(new_content[:1000])  # aperçu des premières lignes
