from pathlib import Path

import streamlit as st
from pypdf import PdfReader
from scoring import calculer_score


# Dossier où les CV déposés seront conservés.
DOSSIER_CV = Path(__file__).parent / "data" / "cv"

st.set_page_config(
    page_title="TalentRank ATS",
    page_icon="📄",
    layout="centered",
)

st.title("TalentRank ATS")
st.subheader("Bienvenue dans votre espace de recrutement")
st.write(
    "Cette application vous aide à organiser les candidatures et à faciliter "
    "leur examen. La décision finale reste toujours entre les mains du recruteur."
)

st.header("Déposer une candidature")
with st.form("formulaire_candidature"):
    nom = st.text_input("Nom complet *")
    email = st.text_input("Adresse e-mail *")
    cv = st.file_uploader("CV au format PDF *", type=["pdf"])
    candidature_envoyee = st.form_submit_button("Envoyer la candidature")

if candidature_envoyee:
    erreurs = []

    if not nom.strip():
        erreurs.append("Veuillez renseigner votre nom.")
    if not email.strip():
        erreurs.append("L'adresse e-mail est obligatoire.")
    if cv is None:
        erreurs.append("Veuillez joindre votre CV au format PDF.")
    elif not cv.name.lower().endswith(".pdf"):
        erreurs.append("Le fichier fourni n'est pas un PDF. La candidature est rejetée.")
    elif not cv.getvalue():
        erreurs.append("Le fichier PDF est vide. La candidature est rejetée.")

    if erreurs:
        for erreur in erreurs:
            st.error(erreur)
    else:
        try:
            # Vérifie que le contenu est bien un PDF lisible et en extrait le texte.
            import io

            lecteur_pdf = PdfReader(io.BytesIO(cv.getvalue()))
            texte_cv = "\n".join(page.extract_text() or "" for page in lecteur_pdf.pages)

            if not texte_cv.strip():
                st.error(
                    "Aucun texte n'a pu être extrait de ce PDF. "
                    "Vérifiez le fichier et envoyez un CV contenant du texte."
                )
            else:
                DOSSIER_CV.mkdir(parents=True, exist_ok=True)
                # Utilise le nom d'origine sans chemin pour éviter toute traversée de dossier.
                nom_fichier = Path(cv.name).name
                chemin_cv = DOSSIER_CV / nom_fichier
                chemin_cv.write_bytes(cv.getvalue())

                st.success(f"Candidature reçue pour {nom.strip()} ({email.strip()}).")
                st.caption(f"CV sauvegardé : {chemin_cv.relative_to(Path(__file__).parent)}")
                st.subheader("Texte extrait du CV")
                st.text_area("Contenu du CV", texte_cv, height=300, disabled=True)

                # Le score est indicatif; la décision finale reste celle du recruteur.
                resultat = calculer_score(texte_cv)
                st.subheader("Évaluation indicative de la candidature")
                st.metric("Score total", f"{resultat['score']} / 100")
                st.write(f"**Statut : {resultat['statut']}**")
                st.caption("Cette évaluation aide à la décision. Le recruteur prend la décision finale.")
                lignes = [
                    {
                        "Critère": critere,
                        "Score": f"{detail['score']} / {detail['maximum']}",
                        "Détail": detail["détail"],
                    }
                    for critere, detail in resultat["détails"].items()
                ]
                st.dataframe(lignes, hide_index=True, use_container_width=True)
        except Exception as erreur:
            st.error(
                "Le fichier n'est pas un PDF valide ou lisible. "
                f"La candidature est rejetée. Détail : {erreur}"
            )
