"""Interface Streamlit du système de suivi des candidatures TalentRank."""

import csv
import io
import subprocess
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from pypdf import PdfReader

from scoring import calculer_score

st.set_page_config(page_title="TalentRank ATS", page_icon="📄", layout="wide")


DOSSIER_PROJET = Path(__file__).parent
DOSSIER_CV = DOSSIER_PROJET / "data" / "cv"
DOSSIER_CV_DEMO = DOSSIER_PROJET / "data" / "test_cv"
FICHIER_CANDIDATS = DOSSIER_PROJET / "data" / "candidats.csv"
COLONNES_CSV = ["nom", "email", "score", "statut", "date", "decision", "cv_path"]
STATUTS = ["À contacter", "À étudier", "Refusé"]
DECISIONS = ["À décider", "Présélectionné", "Entretien", "Accepté", "Refusé"]


def lancer_seed_demo() -> None:
    """Génère les CV de démonstration et initialise le CSV avec leurs scores."""
    resultat = subprocess.run(
        [sys.executable, str(DOSSIER_PROJET / "seed_demo.py")],
        cwd=DOSSIER_PROJET,
        capture_output=True,
        text=True,
        check=False,
    )
    if resultat.returncode != 0:
        raise RuntimeError(resultat.stderr or resultat.stdout or "Échec de seed_demo.py")


def charger_candidats() -> pd.DataFrame:
    """Charge les données et complète les colonnes ajoutées aux anciennes démos."""
    tableau = pd.read_csv(FICHIER_CANDIDATS, encoding="utf-8-sig").fillna("")
    for colonne, valeur in (("decision", "À décider"), ("cv_path", "")):
        if colonne not in tableau.columns:
            tableau[colonne] = valeur
    return tableau


def enregistrer_candidats(tableau: pd.DataFrame) -> None:
    """Enregistre le tableau complet, dont la décision du recruteur."""
    tableau.reindex(columns=COLONNES_CSV).to_csv(
        FICHIER_CANDIDATS, index=False, encoding="utf-8-sig"
    )


def chemin_cv_candidat(candidat: pd.Series) -> Path | None:
    """Retrouve le PDF enregistré pour une candidature de démonstration ou reçue."""
    chemin_indique = str(candidat.get("cv_path", "")).strip()
    if chemin_indique:
        chemin = (DOSSIER_PROJET / chemin_indique).resolve()
        if chemin.is_relative_to(DOSSIER_PROJET.resolve()) and chemin.is_file():
            return chemin

    # Compatibilité avec les anciens CSV de démo qui ne contenaient pas cv_path.
    from make_test_cvs import CANDIDATS

    email = str(candidat.get("email", ""))
    for demo in CANDIDATS:
        if demo["email"] == email:
            chemin = DOSSIER_CV_DEMO / str(demo["fichier"])
            if chemin.is_file():
                return chemin
    return None


def afficher_classement() -> None:
    """Affiche le classement puis la fiche détaillée du candidat sélectionné."""
    st.header("Classement des candidats")
    tableau = charger_candidats()
    if tableau.empty:
        st.info("Aucune candidature enregistrée pour le moment.")
        return

    tableau["score"] = pd.to_numeric(tableau["score"], errors="coerce").fillna(0)
    filtre_statut = st.selectbox("Filtrer par statut", ["Tous"] + STATUTS)
    affiches = tableau if filtre_statut == "Tous" else tableau[tableau["statut"] == filtre_statut]
    affiches = affiches.sort_values("score", ascending=False)
    st.dataframe(
        affiches[["nom", "email", "score", "statut", "date", "decision"]].rename(columns={
            "nom": "Nom", "email": "E-mail", "score": "Score", "statut": "Statut",
            "date": "Date", "decision": "Décision du recruteur",
        }),
        hide_index=True,
        use_container_width=True,
    )
    if affiches.empty:
        st.info("Aucun candidat ne correspond à ce statut.")
        return

    options = affiches.index.tolist()
    index_selectionne = st.selectbox(
        "Sélectionner un candidat",
        options,
        format_func=lambda index: f"{tableau.at[index, 'nom']} — {tableau.at[index, 'email']}",
    )
    candidat = tableau.loc[index_selectionne]
    st.subheader(str(candidat["nom"]))

    chemin_cv = chemin_cv_candidat(candidat)
    if chemin_cv:
        try:
            lecteur = PdfReader(str(chemin_cv))
            texte_cv = "\n".join(page.extract_text() or "" for page in lecteur.pages)
        except Exception as erreur:
            texte_cv = f"Impossible de lire ce PDF : {erreur}"
        st.text_area("CV — texte extrait", texte_cv, height=320, disabled=True)
        resultat = calculer_score(texte_cv)
        st.metric("Score calculé", f"{resultat['score']} / 100")
        st.dataframe(
            pd.DataFrame([
                {
                    "Critère": critere,
                    "Score": f"{detail['score']} / {detail['maximum']}",
                    "Détail": detail["détail"],
                }
                for critere, detail in resultat["détails"].items()
            ]),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.warning("Aucun CV associé à cette candidature n'a été retrouvé.")

    decision_actuelle = str(candidat.get("decision", "À décider"))
    if decision_actuelle not in DECISIONS:
        decision_actuelle = "À décider"
    decision = st.selectbox(
        "Décision du recruteur", DECISIONS,
        index=DECISIONS.index(decision_actuelle), key=f"decision_{index_selectionne}",
    )
    if decision != candidat.get("decision", ""):
        tableau.at[index_selectionne, "decision"] = decision
        enregistrer_candidats(tableau)
        st.success("Décision enregistrée dans le fichier des candidatures.")
        st.rerun()


def afficher_tableau_de_bord() -> None:
    """Présente les indicateurs et le nombre de candidatures par statut."""
    st.header("Tableau de bord")
    tableau = charger_candidats()
    if tableau.empty:
        st.info("Aucune candidature à afficher.")
        return

    tableau["score"] = pd.to_numeric(tableau["score"], errors="coerce")
    total = len(tableau)
    score_moyen = tableau["score"].mean()
    metriques = st.columns(2 + len(STATUTS))
    metriques[0].metric("Candidatures", total)
    metriques[1].metric("Score moyen", f"{score_moyen:.1f} / 100" if pd.notna(score_moyen) else "—")

    par_statut = tableau["statut"].value_counts().reindex(STATUTS, fill_value=0)
    for index, statut in enumerate(STATUTS, start=2):
        metriques[index].metric(statut, int(par_statut[statut]))

    st.subheader("Candidatures par statut")
    graphique = pd.DataFrame({"Nombre de candidatures": par_statut})
    st.bar_chart(graphique, use_container_width=True)


FICHIER_CANDIDATS.parent.mkdir(parents=True, exist_ok=True)
if not FICHIER_CANDIDATS.exists() or FICHIER_CANDIDATS.stat().st_size == 0:
    try:
        lancer_seed_demo()
    except Exception as erreur:
        st.error(f"Impossible d'initialiser la démo : {erreur}")
        st.stop()

st.title("TalentRank ATS")
with st.sidebar:
    page = st.radio("Navigation", ["Déposer une candidature", "Classement des candidats", "Tableau de bord"])
    if st.button("Réinitialiser la démo", use_container_width=True):
        try:
            lancer_seed_demo()
            st.success("Les candidatures de démonstration ont été réinitialisées.")
            st.rerun()
        except Exception as erreur:
            st.error(f"Impossible de réinitialiser la démo : {erreur}")

if page == "Tableau de bord":
    afficher_tableau_de_bord()
elif page == "Classement des candidats":
    afficher_classement()
else:
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
                lecteur_pdf = PdfReader(io.BytesIO(cv.getvalue()))
                texte_cv = "\n".join(page.extract_text() or "" for page in lecteur_pdf.pages)
                if not texte_cv.strip():
                    st.error("Aucun texte n'a pu être extrait de ce PDF. Envoyez un CV contenant du texte.")
                else:
                    DOSSIER_CV.mkdir(parents=True, exist_ok=True)
                    nom_fichier = f"candidature_{date.today().isoformat()}_{Path(cv.name).name}"
                    chemin_cv = DOSSIER_CV / nom_fichier
                    chemin_cv.write_bytes(cv.getvalue())
                    resultat = calculer_score(texte_cv)
                    tableau = charger_candidats()
                    nouvelle_candidature = pd.DataFrame([{
                        "nom": nom.strip(), "email": email.strip(), "score": resultat["score"],
                        "statut": resultat["statut"], "date": date.today().isoformat(),
                        "decision": "À décider",
                        "cv_path": str(chemin_cv.relative_to(DOSSIER_PROJET)),
                    }])
                    enregistrer_candidats(pd.concat([tableau, nouvelle_candidature], ignore_index=True))
                    st.success(f"Candidature reçue pour {nom.strip()} ({email.strip()}).")
                    st.text_area("Texte extrait du CV", texte_cv, height=300, disabled=True)
                    st.subheader("Évaluation indicative de la candidature")
                    st.metric("Score total", f"{resultat['score']} / 100")
                    st.write(f"**Statut : {resultat['statut']}**")
                    st.caption("Cette évaluation aide à la décision. Le recruteur prend la décision finale.")
                    st.dataframe(pd.DataFrame([
                        {"Critère": critere, "Score": f"{detail['score']} / {detail['maximum']}", "Détail": detail['détail']}
                        for critere, detail in resultat["détails"].items()
                    ]), hide_index=True, use_container_width=True)
            except Exception as erreur:
                st.error(f"Le fichier n'est pas un PDF valide ou lisible. La candidature est rejetée. Détail : {erreur}")
