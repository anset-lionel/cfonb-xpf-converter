# CFONB XPF Converter

Cette application Streamlit convertit un fichier CFONB160 en euros vers un fichier CFONB160 en XPF (Franc Pacifique), en respectant la structure de 160 caractères par ligne.

## Fonctionnalités
- Prend en charge les lignes CFONB de type 0302 (entête), 0602 (virements) et 0802 (totaux).
- Convertit les montants de EUR vers XPF au taux de 1 EUR = 119.33 XPF.
- Génére un fichier prêt à être transmis à votre banque.

## Lancer en local
```bash
pip install -r requirements.txt
streamlit run app.py
