"""TalentRank ATS - Smart Recruitment Platform."""

import io
import base64
import subprocess
import sys
import uuid

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

from pypdf import PdfReader
from scoring import calculer_score


# ==========================================
# 1. CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="TalentRank ATS",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).parent

DOSSIER_CV = BASE_DIR / "data" / "cv"

FICHIER_CANDIDATS = BASE_DIR / "data" / "candidats.csv"
FICHIER_OFFRES = BASE_DIR / "data" / "offres.csv"

COLONNES_CSV = [
    "nom",
    "email",
    "score",
    "statut",
    "date",
    "decision",
    "cv_path"
]

STATUTS = [
    "À contacter",
    "À étudier",
    "Refusé"
]

DECISIONS = [
    "À décider",
    "Présélectionné",
    "Entretien",
    "Accepté",
    "Refusé"
]


# ==========================================
# 2. DESIGN CSS
# ==========================================

st.markdown("""
<style>

@import url(
'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
);

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #F5F6FA;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    max-width: 1450px;
}

section[data-testid="stSidebar"] {
    background-color: #172554;
}

section[data-testid="stSidebar"] * {
    color: white;
}

section[data-testid="stSidebar"] div[data-baseweb="radio"] label {
    color: white;
}

h1 {
    color: #172554 !important;
    font-weight: 800 !important;
}

h2, h3 {
    color: #172554 !important;
    font-weight: 700 !important;
}

div[data-testid="stMetric"] {
    background-color: white;
    border: 1px solid #E8EAF2;
    padding: 22px;
    border-radius: 14px;
    box-shadow: 0 3px 12px rgba(20, 35, 80, 0.04);
}

div[data-testid="stMetricLabel"] {
    color: #64748B;
    font-weight: 600;
}

div[data-testid="stMetricValue"] {
    color: #172554;
    font-weight: 800;
}

.stButton button,
.stFormSubmitButton button {
    background-color: #635BDB;
    color: white;
    border: none;
    border-radius: 9px;
    font-weight: 600;
    padding: 10px 20px;
}

.stButton button:hover,
.stFormSubmitButton button:hover {
    background-color: #5148C8;
    color: white;
}

.stTextInput input {
    border-radius: 8px;
}

div[data-testid="stDataFrame"] {
    border-radius: 12px;
}

hr {
    border-color: #E5E7EB;
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 3. DATABASE FUNCTIONS
# ==========================================

def lancer_seed_demo():

    resultat = subprocess.run(
        [sys.executable, str(BASE_DIR / "seed_demo.py")],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False
    )

    if resultat.returncode != 0:

        raise RuntimeError(
            resultat.stderr or "Erreur d'initialisation"
        )


def charger_candidats():

    if not FICHIER_CANDIDATS.exists():

        return pd.DataFrame(columns=COLONNES_CSV)

    tableau = pd.read_csv(
        FICHIER_CANDIDATS,
        encoding="utf-8-sig"
    ).fillna("")

    for colonne in COLONNES_CSV:

        if colonne not in tableau.columns:

            tableau[colonne] = ""

    return tableau


def enregistrer_candidats(tableau):

    tableau.reindex(
        columns=COLONNES_CSV
    ).to_csv(
        FICHIER_CANDIDATS,
        index=False,
        encoding="utf-8-sig"
    )


# ==========================================
# ==========================================
# ==========================================
# JOB OFFERS MANAGEMENT
# ==========================================

def afficher_offres():

    st.title("Job Offers Management")

    st.markdown(
        "Create and manage your recruitment offers."
    )

    st.markdown("---")

    st.subheader("➕ Create a New Job Offer")

    with st.form("formulaire_offre"):

        col1, col2 = st.columns(2)

        with col1:

            titre = st.text_input("Job Title *")

            departement = st.selectbox(
                "Department",
                [
                    "Human Resources",
                    "Marketing",
                    "Finance",
                    "IT",
                    "Management",
                    "Sales"
                ]
            )

            contrat = st.selectbox(
                "Contract Type",
                ["CDI", "CDD", "Stage", "Freelance"]
            )

        with col2:

            localisation = st.text_input(
                "Location",
                placeholder="Casablanca"
            )

            places = st.number_input(
                "Number of Positions",
                min_value=1,
                max_value=100,
                value=1
            )

        description = st.text_area(
            "Job Description *",
            height=150,
            placeholder="Describe the position and required skills..."
        )

        publier = st.form_submit_button(
            "Publish Job Offer",
            use_container_width=True
        )

    if publier:

        if not titre.strip() or not description.strip():

            st.error("Job Title and Description are required.")

        else:

            offres = charger_offres()

            nouvelle_offre = pd.DataFrame([{

                "id": uuid.uuid4().hex[:8],

                "titre": titre.strip(),

                "departement": departement,

                "contrat": contrat,

                "localisation": localisation.strip(),

                "description": description.strip(),

                "places": places,

                "date": date.today().isoformat()

            }])

            offres = pd.concat(
                [offres, nouvelle_offre],
                ignore_index=True
            )

            enregistrer_offres(offres)

            st.success("Job offer published successfully!")

            st.rerun()

    st.markdown("---")

    st.subheader("📋 Published Job Offers")

    offres = charger_offres()

    if offres.empty:

        st.info("No job offers published yet.")

    else:

        st.metric("Total Job Offers", len(offres))

        for _, offre in offres.iterrows():

            with st.container(border=True):

                st.markdown(f"### 💼 {offre['titre']}")

                col1, col2, col3 = st.columns(3)

                col1.write(f"**Department:** {offre['departement']}")

                col2.write(f"**Contract:** {offre['contrat']}")

                col3.write(f"**Location:** {offre['localisation']}")

                st.write(
                    f"**Available Positions:** {offre['places']}"
                )

                with st.expander("View Job Description"):

                    st.write(offre["description"])

                st.caption(f"Published on: {offre['date']}")
                # ==========================================
# JOB OFFERS DATABASE
# ==========================================

COLONNES_OFFRES = [
    "id",
    "titre",
    "departement",
    "contrat",
    "localisation",
    "description",
    "places",
    "date"
]


def charger_offres():

    if not FICHIER_OFFRES.exists():

        return pd.DataFrame(columns=COLONNES_OFFRES)

    offres = pd.read_csv(
        FICHIER_OFFRES,
        encoding="utf-8-sig"
    ).fillna("")

    for colonne in COLONNES_OFFRES:

        if colonne not in offres.columns:

            offres[colonne] = ""

    return offres


def enregistrer_offres(offres):

    offres.reindex(
        columns=COLONNES_OFFRES
    ).to_csv(
        FICHIER_OFFRES,
        index=False,
        encoding="utf-8-sig"
    )
# 4. SIDEBAR
# ==========================================

with st.sidebar:

    st.title("🎯 TalentRank")
    st.caption("SMART RECRUITMENT PLATFORM")

    st.markdown("---")

    st.caption("OVERVIEW")

    page = st.radio(
    "Navigation",
    [
        "Dashboard",
        "Candidates",
        "Add Candidate",
        "Job Offers"
    ],
    label_visibility="collapsed"
)

    st.markdown("---")

    st.caption("SYSTEM")

    st.markdown(
    """
    <div style="
        background:#26376B;
        padding:15px;
        border-radius:10px;
        margin-top:10px;
    ">
        <p style="font-size:12px;color:#C7D2FE;">
            RECRUITMENT MANAGEMENT
        </p>
        <p style="font-size:13px;color:white;">
            Manage your candidates and simplify
            your recruitment process.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

    st.markdown("---")

    if st.button(
        "🔄 Reset Demo",
        use_container_width=True
    ):

        try:

            lancer_seed_demo()

            st.success("Demo réinitialisée.")

            st.rerun()

        except Exception as erreur:

            st.error(str(erreur))
# 5. INITIALISATION
# ==========================================

FICHIER_CANDIDATS.parent.mkdir(
    parents=True,
    exist_ok=True
)

if (
    not FICHIER_CANDIDATS.exists()
    or FICHIER_CANDIDATS.stat().st_size == 0
):

    try:

        lancer_seed_demo()

    except Exception as erreur:

        st.error(f"Erreur : {erreur}")

        st.stop()


tableau = charger_candidats()

tableau["score"] = pd.to_numeric(
    tableau["score"],
    errors="coerce"
).fillna(0)


# ==========================================
# 6. DASHBOARD
# ==========================================

def afficher_dashboard():

    st.title("Dashboard")

    st.markdown(
        "Bienvenue dans votre espace de gestion du recrutement."
    )

    st.markdown("---")

    total = len(tableau)

    score_moyen = (
        tableau["score"].mean()
        if total > 0 else 0
    )

    presel = len(
        tableau[
            tableau["decision"] == "Présélectionné"
        ]
    )

    recrutes = len(
        tableau[
            tableau["decision"] == "Accepté"
        ]
    )

    st.subheader("Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Candidates",
        total
    )

    col2.metric(
        "Average Score",
        f"{score_moyen:.1f}/100"
    )

    col3.metric(
        "Shortlisted",
        presel
    )

    col4.metric(
        "Hired",
        recrutes
    )

    st.markdown("---")

    st.subheader("Recruitment Analytics")

    gauche, droite = st.columns(2)

    with gauche:

        st.markdown("**Candidates by Status**")

        if total > 0:

            distribution = tableau["statut"].value_counts()

            st.bar_chart(
                distribution,
                color="#635BDB"
            )

        else:

            st.info("Aucune candidature disponible.")

    with droite:

        st.markdown("**Recruitment Decisions**")

        if total > 0:

            decisions = tableau["decision"].value_counts()

            st.bar_chart(
                decisions,
                color="#172554"
            )

        else:

            st.info("Aucune donnée disponible.")

    st.markdown("---")
    # ======================================
    # RECRUITMENT FUNNEL & TOP CANDIDATES
    # ======================================

    st.markdown("---")

    gauche, droite = st.columns(2)

    with gauche:

        st.subheader("Recruitment Funnel")

        etapes = [
            "À décider",
            "Présélectionné",
            "Entretien",
            "Accepté"
        ]

        funnel = pd.DataFrame({
            "Stage": etapes,
            "Candidates": [
                int((tableau["decision"] == etape).sum())
                for etape in etapes
            ]
        })

        st.bar_chart(
            funnel.set_index("Stage"),
            color="#635BDB"
        )

    with droite:

        st.subheader("🏆 Top Candidates")

        top = tableau.sort_values(
            "score",
            ascending=False
        ).head(5)

        if not top.empty:

            st.dataframe(
                top[
                    ["nom", "score", "decision"]
                ].rename(
                    columns={
                        "nom": "Candidate",
                        "score": "Matching Score",
                        "decision": "Decision"
                    }
                ),
                hide_index=True,
                use_container_width=True
            )

        else:

            st.info("No candidates available.")

    st.subheader("Recent Applications")

    if total > 0:

        recent = tableau.sort_values(
            "date",
            ascending=False
        ).head(5)

        st.dataframe(
            recent[
                ["nom", "email", "score", "statut", "date"]
            ].rename(
                columns={
                    "nom": "Candidate",
                    "email": "Email",
                    "score": "Score",
                    "statut": "Status",
                    "date": "Application Date"
                }
            ),
            hide_index=True,
            use_container_width=True
        )

    else:

        st.info("Aucune candidature enregistrée.")


# ==========================================
# 7. CANDIDATE MANAGEMENT
# ==========================================

def afficher_candidats():

    st.title("Candidate Management")

    st.markdown(
        "Consultez et gérez les candidatures reçues."
    )
    # ======================================
    # KANBAN BOARD
    # ======================================

    st.markdown("---")
    st.subheader("📋 Recruitment Pipeline")

    etapes_kanban = [
        "À décider",
        "Présélectionné",
        "Entretien",
        "Accepté",
        "Refusé"
    ]

    colonnes = st.columns(5)

    for colonne, etape in zip(colonnes, etapes_kanban):

        with colonne:

            st.markdown(f"**{etape}**")

            candidats_etape = tableau[
                tableau["decision"].astype(str) == etape
            ]

            st.caption(f"{len(candidats_etape)} candidats")

            for idx, candidat_kanban in candidats_etape.iterrows():

                with st.container(border=True):

                    st.markdown(
                        f"**{candidat_kanban['nom']}**"
                    )

                    st.caption(
                        candidat_kanban["email"]
                    )

                    st.metric(
                        "Matching Score",
                        f"{candidat_kanban['score']}/100"
                    )
                    nouvelle_etape = st.selectbox(
                        "Move to",
                        etapes_kanban,
                        index=etapes_kanban.index(etape),
                        key=f"move_{idx}"
                    )

                    if st.button(
                        "Update Stage",
                        key=f"update_{idx}",
                        use_container_width=True
                    ):

                        tableau.at[idx, "decision"] = nouvelle_etape

                        enregistrer_candidats(tableau)

                        st.success("Stage updated!")

                        st.rerun()

    st.markdown("---")

    if tableau.empty:

        st.info("Aucun candidat enregistré.")

        return

    recherche = st.text_input(
        "🔎 Rechercher un candidat",
        placeholder="Nom ou adresse e-mail..."
    )

    filtre = st.selectbox(
        "Filtrer par statut",
        ["Tous"] + STATUTS
    )

    affiches = tableau.copy()

    if recherche:

        affiches = affiches[
            affiches["nom"].str.contains(
                recherche,
                case=False,
                na=False
            )
            |
            affiches["email"].str.contains(
                recherche,
                case=False,
                na=False
            )
        ]

    if filtre != "Tous":

        affiches = affiches[
            affiches["statut"] == filtre
        ]

    affiches = affiches.sort_values(
        "score",
        ascending=False
    )

    if affiches.empty:

        st.info("Aucun résultat trouvé.")

        return

    st.dataframe(
        affiches[
            [
                "nom",
                "email",
                "score",
                "statut",
                "date",
                "decision"
            ]
        ].rename(
            columns={
                "nom": "Candidate",
                "email": "Email",
                "score": "Score",
                "statut": "Status",
                "date": "Date",
                "decision": "Recruiter Decision"
            }
        ),
        hide_index=True,
        use_container_width=True
    )

    st.markdown("---")

    st.subheader("Candidate Profile")

    index = st.selectbox(
        "Sélectionner un candidat",
        affiches.index,
        format_func=lambda i: (
            f"{tableau.at[i, 'nom']} — "
            f"{tableau.at[i, 'email']}"
        )
    )

    candidat = tableau.loc[index]

    st.markdown(f"### {candidat['nom']}")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Matching Score",
        f"{candidat['score']}/100"
    )

    c2.metric(
        "Status",
        candidat["statut"]
    )

    c3.metric(
        "Decision",
        candidat["decision"]
    )

    st.write(f"**Email:** {candidat['email']}")

    # ======================================
    # CV DOWNLOAD AND PREVIEW
    # ======================================

    st.markdown("---")

    st.subheader("Candidate Documents")

    cv_path_rel = str(
        candidat.get("cv_path", "")
    ).strip().replace("\\", "/")

    if cv_path_rel:

        chemin_cv = (
            BASE_DIR / cv_path_rel
        ).resolve()

        try:

            chemin_cv.relative_to(BASE_DIR.resolve())

            fichier_existe = chemin_cv.is_file()

        except ValueError:

            fichier_existe = False

        if fichier_existe:

            contenu_pdf = chemin_cv.read_bytes()

            st.download_button(
                "📄 Télécharger le CV",
                data=contenu_pdf,
                file_name=f"{candidat['nom']}_CV.pdf",
                mime="application/pdf",
                key=f"cv_{index}"
            )

            st.markdown("### Aperçu du CV")

            pdf_base64 = base64.b64encode(
                contenu_pdf
            ).decode("utf-8")

            st.markdown(
                f"""
                <iframe
                    src="data:application/pdf;base64,{pdf_base64}"
                    width="100%"
                    height="700"
                    style="
                        border:1px solid #E5E7EB;
                        border-radius:10px;
                    ">
                </iframe>
                """,
                unsafe_allow_html=True
            )

        else:

            st.warning("CV non disponible.")

    else:

        st.info("Aucun CV enregistré pour ce candidat.")

    # ======================================
    # RECRUITER DECISION
    # ======================================

    st.markdown("---")

    st.subheader("Recruitment Decision")

    decision_actuelle = str(
        candidat["decision"]
    )

    if decision_actuelle not in DECISIONS:

        decision_actuelle = "À décider"

    nouvelle_decision = st.selectbox(
        "Décision du recruteur",
        DECISIONS,
        index=DECISIONS.index(decision_actuelle),
        key=f"decision_{index}"
    )

    if st.button(
        "Save Decision",
        key=f"save_{index}"
    ):

        tableau.at[index, "decision"] = nouvelle_decision

        enregistrer_candidats(tableau)

        st.success("Décision enregistrée.")

        st.rerun()


# ==========================================
# 8. ADD CANDIDATE
# ==========================================

def ajouter_candidat():

    st.title("Add New Candidate")

    st.markdown(
        "Enregistrez une nouvelle candidature dans TalentRank."
    )

    st.markdown("---")

    with st.form("formulaire_candidature"):

        st.subheader("Personal Information")

        nom = st.text_input("Full Name *")

        email = st.text_input("Email Address *")

        st.subheader("Documents")

        cv = st.file_uploader(
            "Upload CV (PDF) *",
            type=["pdf"]
        )

        envoyer = st.form_submit_button(
            "Submit Application",
            use_container_width=True
        )

    if envoyer:

        erreurs = []

        if not nom.strip():

            erreurs.append("Le nom est obligatoire.")

        if not email.strip() or "@" not in email:

            erreurs.append("Veuillez saisir un e-mail valide.")

        if cv is None:

            erreurs.append("Veuillez joindre un CV.")

        if erreurs:

            for erreur in erreurs:

                st.error(erreur)

            return

        try:

            lecteur = PdfReader(
                io.BytesIO(cv.getvalue())
            )

            texte_cv = "\n".join(
                page.extract_text() or ""
                for page in lecteur.pages
            )

            if not texte_cv.strip():

                st.error(
                    "Impossible d'extraire du texte de ce CV."
                )

                return

            DOSSIER_CV.mkdir(
                parents=True,
                exist_ok=True
            )

            nom_fichier = f"{uuid.uuid4().hex}.pdf"

            chemin_cv = DOSSIER_CV / nom_fichier

            chemin_cv.write_bytes(
                cv.getvalue()
            )

            resultat = calculer_score(texte_cv)

            nouvelle = pd.DataFrame([{

                "nom": nom.strip(),

                "email": email.strip(),

                "score": resultat["score"],

                "statut": resultat["statut"],

                "date": date.today().isoformat(),

                "decision": "À décider",

                "cv_path": str(
                    chemin_cv.relative_to(BASE_DIR)
                )

            }])

            nouveau_tableau = pd.concat(
                [tableau, nouvelle],
                ignore_index=True
            )

            enregistrer_candidats(
                nouveau_tableau
            )

            st.success(
                f"Candidature reçue pour {nom} !"
            )

            st.subheader("CV Analysis")

            st.metric(
                "Matching Score",
                f"{resultat['score']}/100"
            )

            st.write(
                f"**Status : {resultat['statut']}**"
            )

            details = resultat.get(
                "détails",
                resultat.get("details", {})
            )

            if isinstance(details, dict) and details:

                st.subheader("Score Details")

                lignes = []

                for critere, detail in details.items():

                    if isinstance(detail, dict):

                        lignes.append({
                            "Critère": critere,
                            "Score": (
                                f"{detail.get('score', '—')} / "
                                f"{detail.get('maximum', '—')}"
                            ),
                            "Détail": detail.get(
                                "détail",
                                detail.get("detail", "")
                            )
                        })

                    else:

                        lignes.append({
                            "Critère": critere,
                            "Score": "—",
                            "Détail": str(detail)
                        })

                st.dataframe(
                    pd.DataFrame(lignes),
                    hide_index=True,
                    use_container_width=True
                )

            st.caption(
                "L'évaluation est indicative. "
                "La décision finale appartient au recruteur."
            )

        except Exception as erreur:

            st.error(
                f"Erreur lors du traitement du CV : {erreur}"
            )


# ==========================================
# ==========================================
# 9. PAGE NAVIGATION
# ==========================================

if page == "Dashboard":

    afficher_dashboard()

elif page == "Candidates":

    afficher_candidats()

elif page == "Add Candidate":

    ajouter_candidat()

elif page == "Job Offers":

    afficher_offres()
