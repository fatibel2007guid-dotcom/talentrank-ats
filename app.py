"""TalentRank ATS - Smart Recruitment Platform."""

import base64
import hashlib
import hmac
import io
import re
import secrets
import subprocess
import sys
import unicodedata
import uuid
from datetime import date, datetime
from pathlib import Path
from urllib.parse import quote

import altair as alt
import pandas as pd
import streamlit as st
from pypdf import PdfReader

from scoring import calculer_matching_offre, calculer_score

# ==========================================
# 1. CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="TalentRank ATS",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FICHIER_CANDIDATS = DATA_DIR / "candidats.csv"
FICHIER_OFFRES = DATA_DIR / "offres.csv"
FICHIER_ENTRETIENS = DATA_DIR / "entretiens.csv"

COLONNES_CSV = [
    "candidate_id", "nom", "email", "score", "matching_score",
    "statut", "date", "decision", "offre", "cv_path", "source",
]
COLONNES_OFFRES = [
    "id", "titre", "departement", "contrat", "localisation",
    "description", "competences_requises", "places", "date", "statut_offre",
]
COLONNES_ENTRETIENS = [
    "id", "candidate_id", "candidat", "offre", "date", "heure",
    "type", "recruteur", "feedback", "resultat",
]

STATUTS = ["À contacter", "À étudier", "Refusé"]
DECISIONS = ["À décider", "Présélectionné", "Entretien", "Accepté", "Refusé"]
RESULTATS = ["En attente", "Réussi", "Échoué"]

FICHIER_UTILISATEURS = DATA_DIR / "utilisateurs.csv"
COLONNES_UTILISATEURS = ["email", "nom", "role", "mot_de_passe", "date"]
ROLES = ["Admin", "Recruteur"]

FICHIER_NOTES = DATA_DIR / "notes.csv"
COLONNES_NOTES = ["id", "candidate_id", "auteur", "date", "note"]
SOURCES = ["LinkedIn", "Site carrières", "Recommandation", "ANAPEC", "Autre"]

COMPETENCES_DISPONIBLES = [
    "Recrutement", "Sourcing", "Entretien", "ATS", "Excel",
    "Rédaction d'annonces", "Paie", "Droit du travail", "GPEC",
    "Marketing", "Communication", "Gestion de projet",
    "Analyse de données", "Management", "Organisation",
]

PALETTE_DECISIONS = {
    "À décider": "#94A3B8", "Présélectionné": "#4F46E5",
    "Entretien": "#F59E0B", "Accepté": "#16A34A", "Refusé": "#DC2626",
}
PALETTE_STATUTS = {
    "À contacter": "#16A34A", "À étudier": "#F59E0B", "Refusé": "#DC2626",
}
COULEURS_GENERIQUES = [
    "#4F46E5", "#0EA5E9", "#16A34A", "#F59E0B",
    "#EC4899", "#14B8A6", "#DC2626",
]

# ==========================================
# 2. DESIGN (CSS + LOGO)
# ==========================================

st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #3730A3;
    --secondary: #4F46E5;
    --background: #F5F6FC;
    --surface: #FFFFFF;
    --text: #1E1B4B;
    --muted: #6B7280;
    --border: #E4E5F2;
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: var(--background); color: var(--text); }

.block-container { padding: 2rem 2.5rem 3rem; max-width: 1500px; }

h1 { color: var(--primary) !important; font-size: 2rem !important; font-weight: 800 !important; letter-spacing: -0.7px; }
h2, h3 { color: var(--primary) !important; font-weight: 700 !important; }
p, label { color: var(--text); }

/* SIDEBAR : indigo fonce */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #2B2670 0%, #231F5C 100%);
    border-right: none;
}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {
    min-height: 0 !important;
    height: auto !important;
    padding: 0.4rem 1rem 0 1rem !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {
    padding-top: 0.25rem !important;
}
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] button,
section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"] svg {
    color: #FFFFFF !important;
}
section[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.15); margin: 1rem 0; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #C7C4F0 !important; }

/* NAVIGATION : boutons simples, sans puces */
section[data-testid="stSidebar"] .stButton button {
    width: 100%;
    justify-content: flex-start;
    text-align: left;
    padding: 11px 14px;
    border-radius: 10px;
    font-weight: 500;
    box-shadow: none;
}
section[data-testid="stSidebar"] .stButton button[kind="secondary"],
section[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-secondary"] {
    background: transparent;
    border: none;
}
section[data-testid="stSidebar"] .stButton button[kind="secondary"] p,
section[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-secondary"] p {
    color: #E0E0FF !important;
}
section[data-testid="stSidebar"] .stButton button[kind="secondary"]:hover,
section[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-secondary"]:hover {
    background: rgba(255,255,255,0.10);
}
section[data-testid="stSidebar"] .stButton button[kind="primary"],
section[data-testid="stSidebar"] .stButton button[data-testid="stBaseButton-primary"] {
    background: #5B52E0;
    border: none;
}

/* METRIC CARDS */
div[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 18px 20px;
}
div[data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
div[data-testid="stMetricValue"] { color: var(--primary); font-weight: 800; }

/* BUTTONS */
.stButton button, .stFormSubmitButton button, .stDownloadButton button {
    background: var(--secondary);
    color: #FFFFFF;
    border: none;
    border-radius: 9px;
    font-weight: 600;
    padding: 10px 18px;
}
.stButton button p, .stFormSubmitButton button p, .stDownloadButton button p {
    color: #FFFFFF !important;
}
.stButton button:hover, .stFormSubmitButton button:hover, .stDownloadButton button:hover {
    background: #4338CA;
    color: #FFFFFF;
    border: none;
}

/* INPUTS */
.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div { border-radius: 9px; }

/* CONTAINERS / TABLES / EXPANDERS */
div[data-testid="stVerticalBlockBorderWrapper"] { background: white; border-radius: 12px; border-color: var(--border); }
div[data-testid="stDataFrame"] { background: white; border: 1px solid var(--border); border-radius: 12px; overflow: hidden; }
div[data-testid="stExpander"] { background: white; border: 1px solid var(--border); border-radius: 10px; }

hr { border-color: var(--border); margin-top: 1.5rem; margin-bottom: 1.5rem; }
div[data-testid="stAlert"] { border-radius: 10px; }

</style>
""", unsafe_allow_html=True)

LOGO_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
    '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#3730A3"/><stop offset="1" stop-color="#7C3AED"/>'
    '</linearGradient></defs>'
    '<rect width="48" height="48" rx="12" fill="url(#g)"/>'
    '<rect x="11" y="29" width="6" height="9" rx="1.5" fill="#fff" fill-opacity="0.55"/>'
    '<rect x="21" y="23" width="6" height="15" rx="1.5" fill="#fff" fill-opacity="0.8"/>'
    '<rect x="31" y="17" width="6" height="21" rx="1.5" fill="#fff"/>'
    '<circle cx="34" cy="10.5" r="3.5" fill="#38BDF8"/>'
    '</svg>'
)

LOGO_B64 = base64.b64encode(LOGO_SVG.encode("utf-8")).decode("utf-8")

LOGO_HTML = (
    '<div style="display:flex;align-items:center;gap:12px;padding:2px 0 14px 0;">'
    f'<img src="data:image/svg+xml;base64,{LOGO_B64}" width="42" height="42" alt="TalentRank">'
    '<div>'
    '<div style="font-size:22px;font-weight:800;color:#312E81;line-height:1.1;letter-spacing:-0.5px;">'
    'Talent<span style="color:#4F46E5;">Rank</span></div>'
    '<div style="font-size:12px;color:#64748B;margin-top:2px;">Smart recruitment platform</div>'
    '</div></div>'
)

# ==========================================
# 3. DATA FUNCTIONS
# ==========================================


def lancer_seed_demo():
    resultat = subprocess.run(
        [sys.executable, str(BASE_DIR / "seed_demo.py")],
        cwd=BASE_DIR, capture_output=True, text=True, check=False,
    )
    if resultat.returncode != 0:
        raise RuntimeError(resultat.stderr or "Erreur d'initialisation")


def lire_csv(chemin, colonnes):
    if not chemin.exists() or chemin.stat().st_size == 0:
        return pd.DataFrame(columns=colonnes)
    tableau = pd.read_csv(
        chemin, encoding="utf-8-sig", dtype=str, keep_default_na=False
    )
    for colonne in colonnes:
        if colonne not in tableau.columns:
            tableau[colonne] = ""
    return tableau


def ecrire_csv(tableau, chemin, colonnes):
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tableau.reindex(columns=colonnes).to_csv(
        chemin, index=False, encoding="utf-8-sig"
    )


def enregistrer_candidats(tableau):
    ecrire_csv(tableau, FICHIER_CANDIDATS, COLONNES_CSV)


def enregistrer_offres(tableau):
    ecrire_csv(tableau, FICHIER_OFFRES, COLONNES_OFFRES)


def enregistrer_entretiens(tableau):
    ecrire_csv(tableau, FICHIER_ENTRETIENS, COLONNES_ENTRETIENS)


def charger_candidats():
    tableau = lire_csv(FICHIER_CANDIDATS, COLONNES_CSV)

    # Identifiant unique pour les anciens candidats
    sans_id = tableau["candidate_id"].astype(str).str.strip() == ""
    if sans_id.any():
        tableau.loc[sans_id, "candidate_id"] = [
            uuid.uuid4().hex[:8] for _ in range(int(sans_id.sum()))
        ]
        enregistrer_candidats(tableau)

    tableau["score"] = pd.to_numeric(
        tableau["score"], errors="coerce"
    ).fillna(0)
    tableau["decision"] = tableau["decision"].where(
        tableau["decision"].isin(DECISIONS), "À décider"
    )
    return tableau


def charger_offres():
    offres = lire_csv(FICHIER_OFFRES, COLONNES_OFFRES)
    sans_doublon = offres.drop_duplicates(
        subset=[c for c in COLONNES_OFFRES if c != "id"], keep="first"
    ).reset_index(drop=True)
    if len(sans_doublon) != len(offres):
        enregistrer_offres(sans_doublon)
    return sans_doublon


def charger_entretiens():
    return lire_csv(FICHIER_ENTRETIENS, COLONNES_ENTRETIENS)


def competences_offre(titre):
    offres = charger_offres()
    ligne = offres[offres["titre"] == titre]
    if ligne.empty:
        return []
    return [
        c.strip()
        for c in str(ligne.iloc[0]["competences_requises"]).split(",")
        if c.strip()
    ]


def chemin_cv(cv_path):
    relatif = str(cv_path).strip().replace("\\", "/")
    if not relatif:
        return None
    chemin = (BASE_DIR / relatif).resolve()
    try:
        chemin.relative_to(BASE_DIR.resolve())
    except ValueError:
        return None
    return chemin if chemin.is_file() else None


def texte_pdf(contenu):
    lecteur = PdfReader(io.BytesIO(contenu))
    return "\n".join(page.extract_text() or "" for page in lecteur.pages)


def modifier_decision(candidate_id, decision):
    candidats = charger_candidats()
    masque = candidats["candidate_id"].astype(str) == str(candidate_id)
    candidats.loc[masque, "decision"] = decision
    enregistrer_candidats(candidats)


def graphique_cercle(serie, palette=None):
    """Diagramme en cercle (donut) a partir d'un value_counts()."""
    donnees = serie.reset_index()
    donnees.columns = ["categorie", "total"]
    donnees["categorie"] = donnees["categorie"].astype(str)
    donnees = donnees[donnees["total"] > 0]

    if donnees.empty:
        st.info("Aucune donnée disponible.")
        return

    domaine = donnees["categorie"].tolist()
    if palette:
        couleurs = [palette.get(c, "#64748B") for c in domaine]
    else:
        couleurs = [
            COULEURS_GENERIQUES[i % len(COULEURS_GENERIQUES)]
            for i in range(len(domaine))
        ]

    base = alt.Chart(donnees).encode(
        theta=alt.Theta("total:Q", stack=True),
        color=alt.Color(
            "categorie:N",
            scale=alt.Scale(domain=domaine, range=couleurs),
            legend=alt.Legend(title=None, orient="bottom", labelFontSize=12),
        ),
        tooltip=[
            alt.Tooltip("categorie:N", title="Catégorie"),
            alt.Tooltip("total:Q", title="Candidats"),
        ],
    )
    arcs = base.mark_arc(innerRadius=55, outerRadius=100)
    nombres = base.mark_text(
        radius=78, size=14, fontWeight="bold", color="white"
    ).encode(text=alt.Text("total:Q"))

    st.altair_chart(
        (arcs + nombres).properties(height=270).configure_view(strokeWidth=0),
        use_container_width=True,
    )


# ==========================================
# 3B. AUTHENTIFICATION & UTILISATEURS
# ==========================================


def hacher_mot_de_passe(mot_de_passe, sel=None):
    sel = sel or secrets.token_hex(8)
    empreinte = hashlib.pbkdf2_hmac(
        "sha256", mot_de_passe.encode("utf-8"), sel.encode("utf-8"), 100_000
    ).hex()
    return f"{sel}${empreinte}"


def verifier_mot_de_passe(mot_de_passe, stocke):
    if "$" not in str(stocke):
        return False
    sel = str(stocke).split("$", 1)[0]
    return hmac.compare_digest(hacher_mot_de_passe(mot_de_passe, sel), str(stocke))


def charger_utilisateurs():
    return lire_csv(FICHIER_UTILISATEURS, COLONNES_UTILISATEURS)


def enregistrer_utilisateurs(tableau):
    ecrire_csv(tableau, FICHIER_UTILISATEURS, COLONNES_UTILISATEURS)


def utilisateur_courant():
    return st.session_state.get("user")


def est_admin():
    utilisateur = utilisateur_courant()
    return bool(utilisateur) and utilisateur["role"] == "Admin"


def creer_compte(nom, email, mot_de_passe, confirmation):
    email = email.strip().lower()
    utilisateurs = charger_utilisateurs()

    if not nom.strip():
        return "Le nom est obligatoire."
    if "@" not in email or "." not in email:
        return "Veuillez saisir un e-mail valide."
    if len(mot_de_passe) < 6:
        return "Le mot de passe doit contenir au moins 6 caractères."
    if mot_de_passe != confirmation:
        return "Les mots de passe ne correspondent pas."
    if (utilisateurs["email"].str.lower() == email).any():
        return "Un compte existe déjà avec cet e-mail."

    nouveau = pd.DataFrame([{
        "email": email,
        "nom": nom.strip(),
        # Le premier compte créé devient administrateur
        "role": "Admin" if utilisateurs.empty else "Recruteur",
        "mot_de_passe": hacher_mot_de_passe(mot_de_passe),
        "date": date.today().isoformat(),
    }])
    enregistrer_utilisateurs(pd.concat([utilisateurs, nouveau], ignore_index=True))
    return None


def authentifier(email, mot_de_passe):
    email = email.strip().lower()
    utilisateurs = charger_utilisateurs()
    ligne = utilisateurs[utilisateurs["email"].str.lower() == email]
    if ligne.empty:
        return None
    compte = ligne.iloc[0]
    if not verifier_mot_de_passe(mot_de_passe, compte["mot_de_passe"]):
        return None
    return {"email": compte["email"], "nom": compte["nom"], "role": compte["role"]}


def afficher_connexion():
    st.markdown(
        "<style>section[data-testid='stSidebar'], "
        "[data-testid='collapsedControl'] {display: none;}</style>",
        unsafe_allow_html=True,
    )

    _, centre, _ = st.columns([1, 1.2, 1])

    with centre:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(LOGO_HTML, unsafe_allow_html=True)
        st.markdown("### Bienvenue")

        onglet_connexion, onglet_inscription = st.tabs(
            ["Log in", "Create account"]
        )

        with onglet_connexion:
            with st.form("form_login"):
                email = st.text_input("Email")
                mot_de_passe = st.text_input("Password", type="password")
                connecter = st.form_submit_button(
                    "Log in", use_container_width=True
                )

            if connecter:
                utilisateur = authentifier(email, mot_de_passe)
                if utilisateur:
                    st.session_state["user"] = utilisateur
                    st.session_state["page"] = "Dashboard"
                    st.rerun()
                else:
                    st.error("E-mail ou mot de passe incorrect.")

        with onglet_inscription:
            if charger_utilisateurs().empty:
                st.info("Le premier compte créé devient Administrateur.")

            with st.form("form_inscription"):
                nom = st.text_input("Full Name")
                email_new = st.text_input("Email Address")
                mdp = st.text_input("Password (6 caractères min.)", type="password")
                mdp2 = st.text_input("Confirm Password", type="password")
                creer = st.form_submit_button(
                    "Create account", use_container_width=True
                )

            if creer:
                erreur = creer_compte(nom, email_new, mdp, mdp2)
                if erreur:
                    st.error(erreur)
                else:
                    st.success("Compte créé. Vous pouvez vous connecter.")


def afficher_compte():
    st.title("My Account")
    st.markdown("Vos informations et votre mot de passe.")
    st.markdown("---")

    utilisateur = utilisateur_courant()

    c1, c2, c3 = st.columns(3)
    c1.metric("Name", utilisateur["nom"])
    c2.metric("Role", utilisateur["role"])
    c3.write(f"**Email:** {utilisateur['email']}")

    st.markdown("---")
    st.subheader("Change Password")

    with st.form("form_mdp"):
        actuel = st.text_input("Current Password", type="password")
        nouveau = st.text_input("New Password", type="password")
        confirmation = st.text_input("Confirm New Password", type="password")
        valider = st.form_submit_button("Update Password")

    if valider:
        if authentifier(utilisateur["email"], actuel) is None:
            st.error("Mot de passe actuel incorrect.")
        elif len(nouveau) < 6:
            st.error("Le nouveau mot de passe doit contenir au moins 6 caractères.")
        elif nouveau != confirmation:
            st.error("Les mots de passe ne correspondent pas.")
        else:
            utilisateurs = charger_utilisateurs()
            masque = utilisateurs["email"].str.lower() == utilisateur["email"].lower()
            utilisateurs.loc[masque, "mot_de_passe"] = hacher_mot_de_passe(nouveau)
            enregistrer_utilisateurs(utilisateurs)
            st.success("Mot de passe mis à jour.")


def afficher_utilisateurs():
    st.title("User Management")
    st.markdown("Gérez les comptes et les rôles de l'équipe.")
    st.markdown("---")

    if not est_admin():
        st.error("Accès réservé aux administrateurs.")
        return

    utilisateurs = charger_utilisateurs()
    moi = utilisateur_courant()["email"].lower()

    st.dataframe(
        utilisateurs[["nom", "email", "role", "date"]].rename(columns={
            "nom": "Name", "email": "Email", "role": "Role", "date": "Created",
        }),
        hide_index=True, use_container_width=True,
    )

    st.markdown("---")
    st.subheader("Edit an account")

    email = st.selectbox("Account", utilisateurs["email"].tolist())
    ligne = utilisateurs[utilisateurs["email"] == email].iloc[0]
    role = st.selectbox(
        "Role", ROLES,
        index=ROLES.index(ligne["role"]) if ligne["role"] in ROLES else 1,
    )

    b1, b2 = st.columns(2)
    nb_admins = int((utilisateurs["role"] == "Admin").sum())

    if b1.button("Save role", use_container_width=True):
        if ligne["role"] == "Admin" and role != "Admin" and nb_admins <= 1:
            st.error("Il faut garder au moins un administrateur.")
        else:
            utilisateurs.loc[utilisateurs["email"] == email, "role"] = role
            enregistrer_utilisateurs(utilisateurs)
            st.success("Rôle mis à jour.")
            st.rerun()

    if b2.button(
        "Delete account", use_container_width=True,
        disabled=(email.lower() == moi),
    ):
        enregistrer_utilisateurs(utilisateurs[utilisateurs["email"] != email])
        st.success("Compte supprimé.")
        st.rerun()


# ==========================================
# 3C. NOTES, EMAILS ET PAGE CARRIERES
# ==========================================

MODELES_EMAIL = {
    "Accusé de réception": (
        "Votre candidature – {offre}",
        "Bonjour {nom},\n\nNous avons bien reçu votre candidature pour le poste "
        "de {offre}. Notre équipe l'étudie et reviendra vers vous rapidement.\n\n"
        "Cordialement,\n{recruteur}",
    ),
    "Invitation à un entretien": (
        "Invitation à un entretien – {offre}",
        "Bonjour {nom},\n\nVotre profil a retenu notre attention pour le poste "
        "de {offre}. Nous souhaiterions vous rencontrer pour un entretien.\n"
        "Merci de nous indiquer vos disponibilités.\n\nCordialement,\n{recruteur}",
    ),
    "Offre positive": (
        "Suite favorable – {offre}",
        "Bonjour {nom},\n\nNous avons le plaisir de vous informer que votre "
        "candidature pour le poste de {offre} a été retenue. Nous reviendrons "
        "vers vous pour les prochaines étapes.\n\nCordialement,\n{recruteur}",
    ),
    "Réponse négative": (
        "Votre candidature – {offre}",
        "Bonjour {nom},\n\nMerci pour l'intérêt porté à notre entreprise. "
        "Après étude de votre dossier, nous ne pouvons malheureusement pas donner "
        "suite à votre candidature pour le poste de {offre}.\n\n"
        "Nous vous souhaitons une pleine réussite.\n\nCordialement,\n{recruteur}",
    ),
}


def generer_email(modele, candidat, recruteur):
    sujet, corps = MODELES_EMAIL[modele]
    valeurs = {
        "nom": candidat["nom"],
        "offre": candidat["offre"] or "ce poste",
        "recruteur": recruteur["nom"],
    }
    return sujet.format(**valeurs), corps.format(**valeurs)


def lien_mailto(destinataire, sujet, corps):
    return f"mailto:{destinataire}?subject={quote(sujet)}&body={quote(corps)}"


def charger_notes():
    return lire_csv(FICHIER_NOTES, COLONNES_NOTES)


def enregistrer_notes(tableau):
    ecrire_csv(tableau, FICHIER_NOTES, COLONNES_NOTES)


def offres_ouvertes():
    offres = charger_offres()
    return offres[offres["statut_offre"] != "Closed"]


def creer_candidature(nom, email, offre, contenu_pdf, source):
    """Enregistre une candidature. Retourne un message d'erreur ou None."""
    if not nom.strip():
        return "Le nom est obligatoire."
    if "@" not in email:
        return "Veuillez saisir un e-mail valide."
    if contenu_pdf is None:
        return "Veuillez joindre un CV (PDF)."

    existants = charger_candidats()
    if not existants.empty and (
        (existants["email"].astype(str).str.lower() == email.strip().lower())
        & (existants["offre"].astype(str) == str(offre))
    ).any():
        return "Vous avez déjà postulé à cette offre."

    try:
        texte_cv = texte_pdf(contenu_pdf)
    except Exception:
        return "Le fichier PDF est illisible."

    resultat = calculer_score(texte_cv)

    dossier_cvs = DATA_DIR / "cvs"
    dossier_cvs.mkdir(parents=True, exist_ok=True)
    chemin = dossier_cvs / f"{uuid.uuid4().hex[:8]}.pdf"
    chemin.write_bytes(contenu_pdf)

    requises = competences_offre(offre)
    matching = calculer_matching_offre(texte_cv, requises) if requises else None

    nouvelle = pd.DataFrame([{
        "candidate_id": uuid.uuid4().hex[:8],
        "offre": offre,
        "nom": nom.strip(),
        "email": email.strip(),
        "score": resultat["score"],
        "matching_score": matching["score"] if matching else "",
        "statut": resultat["statut"],
        "date": date.today().isoformat(),
        "decision": "À décider",
        "cv_path": str(chemin.relative_to(BASE_DIR)),
        "source": source,
    }])
    enregistrer_candidats(
        pd.concat([lire_csv(FICHIER_CANDIDATS, COLONNES_CSV), nouvelle],
                  ignore_index=True)
    )
    return None


def afficher_carrieres():
    st.markdown(
        "<style>section[data-testid='stSidebar'], "
        "[data-testid='collapsedControl'] {display: none;}</style>",
        unsafe_allow_html=True,
    )

    _, centre, _ = st.columns([1, 2, 1])

    with centre:
        st.markdown(LOGO_HTML, unsafe_allow_html=True)
        st.title("Careers")
        st.markdown("Découvrez nos offres et postulez en ligne.")

        ouvertes = offres_ouvertes()

        if ouvertes.empty:
            st.info("Aucune offre ouverte pour le moment.")
            return

        for _, offre in ouvertes.iterrows():
            with st.container(border=True):
                st.markdown(f"### {offre['titre']}")
                st.caption(
                    f"{offre['departement']} · {offre['contrat']} · "
                    f"{offre['localisation']}"
                )
                with st.expander("Description"):
                    st.write(offre["description"])
                    st.write(f"**Skills:** {offre['competences_requises']}")

        st.markdown("---")
        st.subheader("Apply")

        with st.form("form_postuler"):
            offre_choisie = st.selectbox("Position", ouvertes["titre"].tolist())
            nom = st.text_input("Full Name *")
            email = st.text_input("Email Address *")
            cv = st.file_uploader("Upload CV (PDF) *", type=["pdf"])
            envoyer = st.form_submit_button(
                "Submit application", use_container_width=True
            )

        if envoyer:
            erreur = creer_candidature(
                nom, email, offre_choisie,
                cv.getvalue() if cv else None, "Site carrières",
            )
            if erreur:
                st.error(erreur)
            else:
                st.success("Merci ! Votre candidature a bien été envoyée.")


# ==========================================
# 3D. CV SCANNER
# ==========================================

LOGO_HTML_SIDEBAR = (
    LOGO_HTML.replace("color:#312E81", "color:#FFFFFF")
    .replace("color:#4F46E5", "color:#A5B4FC")
    .replace("color:#64748B", "color:#C7C4F0")
)

COMPETENCES_SCAN = COMPETENCES_DISPONIBLES + [
    "Word", "PowerPoint", "Python", "SQL", "Power BI", "Canva",
    "SEO", "Photoshop", "Réseaux sociaux",
]

LANGUES_SCAN = {
    "Français": r"francais|french",
    "Anglais": r"anglais|english",
    "Arabe": r"arabe|arabic",
    "Espagnol": r"espagnol|spanish",
    "Allemand": r"allemand|german",
    "Amazigh": r"amazigh|tamazight",
}

ENTETES_CV = {
    "formation": ("formation", "formations", "diplomes", "education",
                  "parcours academique"),
    "experience": ("experience", "experiences", "experience professionnelle",
                   "experiences professionnelles", "stages",
                   "parcours professionnel"),
    "competences": ("competences", "competences techniques", "competences cles",
                    "competences informatiques", "skills", "technologies"),
    "langues": ("langues", "langue", "languages"),
    "autres": ("contact", "profil", "resume", "centres d'interet", "loisirs",
               "interets", "certifications", "projets", "coordonnees",
               "informations personnelles", "objectif"),
}


def normaliser_texte(texte):
    texte = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in texte if unicodedata.category(c) != "Mn")


def lire_texte_fichier(fichier):
    """Extrait le texte d'un CV (PDF, DOCX ou photo)."""
    nom = fichier.name.lower()
    contenu = fichier.getvalue()

    if nom.endswith(".pdf"):
        return texte_pdf(contenu)

    if nom.endswith(".docx"):
        try:
            from docx import Document
        except ImportError:
            raise RuntimeError(
                "Pour lire les fichiers DOCX, ajoutez python-docx à requirements.txt."
            )
        document = Document(io.BytesIO(contenu))
        lignes = [p.text for p in document.paragraphs]
        for tableau in document.tables:
            for rangee in tableau.rows:
                lignes.extend(cellule.text for cellule in rangee.cells)
        return "\n".join(lignes)

    if nom.endswith((".jpg", ".jpeg", ".png")):
        try:
            import pytesseract
            from PIL import Image
        except ImportError:
            raise RuntimeError(
                "Pour lire les photos de CV, ajoutez pytesseract et pillow à "
                "requirements.txt, et tesseract-ocr à packages.txt."
            )
        image = Image.open(io.BytesIO(contenu))
        try:
            return pytesseract.image_to_string(image, lang="fra+eng")
        except Exception:
            return pytesseract.image_to_string(image)

    raise RuntimeError("Format non supporté.")


def decouper_sections(lignes):
    sections = {nom: [] for nom in ENTETES_CV}
    courante = None
    for ligne in lignes:
        cle = normaliser_texte(ligne).strip(" :-•").rstrip(":")
        trouve = next((n for n, v in ENTETES_CV.items() if cle in v), None)
        if trouve:
            courante = trouve
        elif courante:
            sections[courante].append(ligne)
    return sections


def extraire_infos_cv(texte):
    lignes = [l.strip() for l in texte.splitlines() if l.strip()]
    sections = decouper_sections(lignes)
    texte_norm = normaliser_texte(texte)

    email = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", texte)
    telephone = re.search(r"(?:\+212|00212|0)[\s.-]?[5-7](?:[\s.-]?\d{2}){4}", texte)

    interdits = {mot for v in ENTETES_CV.values() for mot in v}
    interdits |= {"cv", "curriculum vitae"}

    nom = ""
    for ligne in lignes[:10]:
        mots = ligne.split()
        if (
            "@" in ligne
            or re.search(r"\d", ligne)
            or not 2 <= len(mots) <= 4
            or len(ligne) > 40
            or normaliser_texte(ligne) in interdits
        ):
            continue
        nom = ligne.title() if ligne.isupper() else ligne
        break

    motif_diplome = (
        r"bac\s*\+\s*\d|licence|master|dut\b|bts\b|ingenieur|doctorat|"
        r"diplome|ofppt|\bests?\b|estc|technicien"
    )
    formation = sections["formation"][:2] or [
        l for l in lignes if re.search(motif_diplome, normaliser_texte(l))
    ][:2]
    experience = sections["experience"][:2] or [
        l for l in lignes
        if re.search(r"\bstage\b|\bexperience\b", normaliser_texte(l))
    ][:2]

    competences = [
        c for c in COMPETENCES_SCAN
        if re.search(
            r"(?<!\w)" + re.escape(normaliser_texte(c)) + r"(?!\w)", texte_norm
        )
    ]
    langues = [n for n, m in LANGUES_SCAN.items() if re.search(m, texte_norm)]

    return {
        "nom": nom,
        "email": email.group(0) if email else "",
        "telephone": re.sub(r"\s+", " ", telephone.group(0)).strip() if telephone else "",
        "formation": formation,
        "experience": experience,
        "competences": competences,
        "langues": langues,
    }


def score_compatibilite(texte, offre):
    """Mélange le score général (30%) et le matching avec l'offre (70%)."""
    general = calculer_score(texte)["score"]
    requises = competences_offre(offre) if offre else []
    if requises:
        matching = calculer_matching_offre(texte, requises)
        return round(0.7 * matching["score"] + 0.3 * general), matching
    return round(general), None


def message_score(score):
    if score >= 80:
        return "Profil très intéressant ✅", "Ce candidat correspond parfaitement aux exigences du poste."
    if score >= 60:
        return "Profil intéressant", "Ce candidat répond à une bonne partie des exigences."
    if score >= 40:
        return "Profil à étudier", "Ce candidat répond partiellement aux exigences."
    return "Profil peu adapté", "Ce candidat répond peu aux exigences du poste."


def anneau_score(valeur):
    valeur = max(0, min(100, int(valeur)))
    couleur = "#16A34A" if valeur >= 70 else "#F59E0B" if valeur >= 40 else "#DC2626"
    circonference = 2 * 3.14159 * 60
    decalage = circonference * (1 - valeur / 100)
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160">'
        '<circle cx="80" cy="80" r="60" fill="none" stroke="#E5E7EB" stroke-width="14"/>'
        f'<circle cx="80" cy="80" r="60" fill="none" stroke="{couleur}" '
        'stroke-width="14" stroke-linecap="round" '
        f'stroke-dasharray="{circonference:.1f}" stroke-dashoffset="{decalage:.1f}" '
        'transform="rotate(-90 80 80)"/>'
        '<text x="80" y="80" text-anchor="middle" dominant-baseline="central" '
        'font-family="Arial, sans-serif" font-size="34" font-weight="800" '
        f'fill="#312E81">{valeur}%</text></svg>'
    )
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    return f'<img src="data:image/svg+xml;base64,{b64}" width="170" height="170">'


def afficher_scanner():
    st.title("CV Scanner")
    st.markdown(
        "Importez un CV (PDF, DOCX ou photo) et laissez TalentRank "
        "extraire les informations automatiquement."
    )
    st.markdown("---")

    ouvertes = offres_ouvertes()
    choix = st.selectbox(
        "Comparer avec l'offre",
        ["Score général (sans offre)"] + ouvertes["titre"].tolist(),
    )
    offre = "" if choix.startswith("Score général") else choix

    fichier = st.file_uploader(
        "Glissez votre CV ici ou cliquez pour importer",
        type=["pdf", "docx", "jpg", "jpeg", "png"],
        help="Formats acceptés : PDF, DOCX, JPG, PNG",
    )

    if fichier is None:
        st.info("Importez un CV pour lancer l'analyse.")
        return

    try:
        with st.spinner("Analyse en cours..."):
            texte = lire_texte_fichier(fichier)
    except RuntimeError as erreur:
        st.error(str(erreur))
        return
    except Exception:
        st.error("Impossible de lire ce fichier.")
        return

    if not texte.strip():
        st.warning("Aucun texte détecté. Essayez un CV plus net ou en PDF texte.")
        return

    infos = extraire_infos_cv(texte)
    score, matching = score_compatibilite(texte, offre)
    titre_message, texte_message = message_score(score)

    gauche, droite = st.columns([3, 2])

    with gauche:
        with st.container(border=True):
            t1, t2 = st.columns([3, 2])
            t1.subheader("✨ Résultat de l'analyse")
            t2.success("CV bien analysé !")

            lignes_infos = [
                ("👤", "Nom & Prénom", infos["nom"]),
                ("✉️", "Email", infos["email"]),
                ("📞", "Téléphone", infos["telephone"]),
                ("🎓", "Formation", " · ".join(infos["formation"])),
                ("💼", "Expérience", " · ".join(infos["experience"])),
                ("🧩", "Compétences", ", ".join(infos["competences"])),
                ("🌐", "Langues", ", ".join(infos["langues"])),
            ]
            for icone, libelle, valeur in lignes_infos:
                c1, c2 = st.columns([1, 2])
                c1.write(f"{icone} **{libelle}**")
                c2.write(valeur or "—")

    with droite:
        with st.container(border=True):
            st.markdown("#### 📊 Score de compatibilité")
            a, b = st.columns(2)
            a.markdown(anneau_score(score), unsafe_allow_html=True)
            b.markdown(f"**{titre_message}**")
            b.caption(texte_message)
            if matching and matching["competences_manquantes"]:
                st.caption(
                    "Compétences manquantes : "
                    + ", ".join(matching["competences_manquantes"])
                )

        with st.container(border=True):
            st.markdown("#### 📝 Résumé du profil")
            resume = [
                (bool(infos["experience"]), "Expérience pertinente"),
                (bool(infos["competences"]),
                 "Compétences clés : " + (", ".join(infos["competences"][:3]) or "non détectées")),
                (bool(infos["formation"]), "Niveau d'étude adapté"),
                (bool(infos["langues"]),
                 "Langues : " + (", ".join(infos["langues"]) or "non détectées")),
            ]
            for ok, ligne in resume:
                st.markdown(("✅ " if ok else "⚠️ ") + ligne)

    st.markdown("---")
    st.subheader("➕ Ajouter aux candidats")

    if not fichier.name.lower().endswith(".pdf"):
        st.info("L'ajout direct nécessite un CV au format PDF. "
                "Les autres formats servent à l'analyse seulement.")
    elif not offre:
        st.info("Choisissez une offre ci-dessus pour ajouter ce candidat.")
    else:
        with st.form("form_scan"):
            nom = st.text_input("Full Name", value=infos["nom"],
                                key=f"scan_nom_{fichier.name}")
            email = st.text_input("Email", value=infos["email"],
                                  key=f"scan_email_{fichier.name}")
            ajouter = st.form_submit_button(
                "Add to candidates", use_container_width=True
            )

        if ajouter:
            erreur = creer_candidature(
                nom, email, offre, fichier.getvalue(), "CV Scanner"
            )
            if erreur:
                st.error(erreur)
            else:
                st.success(f"{nom} a été ajouté(e) aux candidats.")


# ==========================================
# 4. DASHBOARD
# ==========================================


def afficher_dashboard():
    st.title("Dashboard")
    st.markdown("Bienvenue dans votre espace de gestion du recrutement.")
    st.markdown("---")

    tableau = charger_candidats()
    total = len(tableau)
    score_moyen = tableau["score"].mean() if total > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Candidates", total)
    c2.metric("Average Score", f"{score_moyen:.1f}/100")
    c3.metric("Shortlisted", int((tableau["decision"] == "Présélectionné").sum()))
    c4.metric("Hired", int((tableau["decision"] == "Accepté").sum()))
    c5.metric("Job Offers", len(charger_offres()))

    st.markdown("---")
    st.subheader("Recruitment Analytics")

    if total == 0:
        st.info("Aucune candidature disponible.")
    else:
        g1, g2, g3 = st.columns(3)
        with g1:
            st.markdown("**Candidates by Status**")
            graphique_cercle(
                tableau["statut"].replace("", "À étudier").value_counts(),
                PALETTE_STATUTS,
            )
        with g2:
            st.markdown("**Recruitment Decisions**")
            graphique_cercle(
                tableau["decision"].value_counts(), PALETTE_DECISIONS
            )
        with g3:
            st.markdown("**Candidates by Job Offer**")
            graphique_cercle(
                tableau["offre"].replace("", "Non spécifiée").value_counts()
            )

        g4, g5 = st.columns(2)

        with g4:
            st.markdown("**Candidates by Source**")
            graphique_cercle(
                tableau["source"].replace("", "Non spécifiée").value_counts()
            )

        with g5:
            st.markdown("**Hiring Conversion**")

            def taux(decisions):
                return f"{tableau['decision'].isin(decisions).sum() / total * 100:.0f}%"

            t1, t2, t3 = st.columns(3)
            t1.metric("Interview rate", taux(["Entretien", "Accepté"]))
            t2.metric("Hire rate", taux(["Accepté"]))
            t3.metric("Rejection rate", taux(["Refusé"]))


    st.markdown("---")
    gauche, droite = st.columns(2)

    with gauche:
        st.subheader("🏆 Top Candidates")
        if total > 0:
            st.dataframe(
                tableau.sort_values("score", ascending=False)
                .head(5)[["nom", "score", "decision"]]
                .rename(columns={
                    "nom": "Candidate", "score": "Matching Score",
                    "decision": "Decision",
                }),
                hide_index=True, use_container_width=True,
            )
        else:
            st.info("No candidates available.")

    with droite:
        st.subheader("📅 Upcoming Interviews")
        entretiens = charger_entretiens()
        a_venir = entretiens[
            (entretiens["date"].astype(str) >= date.today().isoformat())
            & (entretiens["resultat"] == "En attente")
        ].sort_values(["date", "heure"]).head(5)
        if not a_venir.empty:
            st.dataframe(
                a_venir[["candidat", "date", "heure", "type", "recruteur"]]
                .rename(columns={
                    "candidat": "Candidate", "date": "Date", "heure": "Time",
                    "type": "Type", "recruteur": "Recruiter",
                }),
                hide_index=True, use_container_width=True,
            )
        else:
            st.info("No upcoming interviews.")

    st.markdown("---")
    st.subheader("Recent Applications")
    if total > 0:
        st.dataframe(
            tableau.sort_values("date", ascending=False)
            .head(5)[["nom", "email", "score", "statut", "date"]]
            .rename(columns={
                "nom": "Candidate", "email": "Email", "score": "Score",
                "statut": "Status", "date": "Application Date",
            }),
            hide_index=True, use_container_width=True,
        )
    else:
        st.info("Aucune candidature enregistrée.")


# ==========================================
# 5. CANDIDATES
# ==========================================


def afficher_candidats():
    st.title("Candidate Management")
    st.markdown("Consultez et gérez les candidatures reçues.")
    st.markdown("---")

    tableau = charger_candidats()

    if tableau.empty:
        st.info("Aucun candidat enregistré.")
        return

    recherche = st.text_input(
        "🔎 Rechercher un candidat", placeholder="Nom ou adresse e-mail..."
    )

    f1, f2, f3 = st.columns(3)
    filtre = f1.selectbox("Filtrer par statut", ["Tous"] + STATUTS)
    liste_offres = sorted(o for o in tableau["offre"].astype(str).unique() if o)
    filtre_offre = f2.selectbox("Filtrer par offre", ["Toutes"] + liste_offres)
    score_min = f3.slider("Score minimum", 0, 100, 0)

    affiches = tableau.copy()

    if recherche:
        affiches = affiches[
            affiches["nom"].str.contains(recherche, case=False, na=False)
            | affiches["email"].str.contains(recherche, case=False, na=False)
        ]
    if filtre != "Tous":
        affiches = affiches[affiches["statut"] == filtre]
    if filtre_offre != "Toutes":
        affiches = affiches[affiches["offre"].astype(str) == filtre_offre]
    affiches = affiches[affiches["score"] >= score_min].sort_values(
        "score", ascending=False
    )

    if affiches.empty:
        st.info("Aucun résultat trouvé.")
        return

    st.dataframe(
        affiches[[
            "nom", "email", "offre", "score", "matching_score",
            "statut", "date", "decision",
        ]].rename(columns={
            "nom": "Candidate", "email": "Email", "offre": "Job Offer",
            "score": "Score", "matching_score": "Job Matching",
            "statut": "Status", "date": "Date",
            "decision": "Recruiter Decision",
        }),
        hide_index=True, use_container_width=True,
    )

    st.download_button(
        "⬇️ Export CSV",
        data=affiches.drop(columns=["cv_path"], errors="ignore")
        .to_csv(index=False).encode("utf-8-sig"),
        file_name="candidats_talentrank.csv",
        mime="text/csv",
    )

    st.markdown("---")
    st.subheader("Candidate Profile")

    fiches = affiches.set_index("candidate_id")
    cid = st.selectbox(
        "Sélectionner un candidat",
        fiches.index.tolist(),
        format_func=lambda i: f"{fiches.at[i, 'nom']} — {fiches.at[i, 'email']}",
    )
    candidat = fiches.loc[cid]

    st.markdown(f"### {candidat['nom']}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Matching Score", f"{candidat['score']}/100")
    m2.metric("Status", candidat["statut"])
    m3.metric("Decision", candidat["decision"])
    st.write(f"**Email:** {candidat['email']}")

    st.markdown("---")
    st.subheader("Application Information")
    i1, i2 = st.columns(2)
    i1.info(f"💼 **Job Offer:** {candidat['offre'] or 'Not specified'}")
    i2.info(f"📅 **Application Date:** {candidat['date'] or 'Not specified'}")
    st.write(f"**Source:** {candidat['source'] or 'Non spécifiée'}")

    # ---- CV
    st.markdown("---")
    st.subheader("Candidate Documents")

    if not str(candidat["cv_path"]).strip():
        st.info("Aucun CV enregistré pour ce candidat.")
    else:
        fichier = chemin_cv(candidat["cv_path"])
        if fichier is None:
            st.warning("CV non disponible.")
        else:
            contenu_pdf = fichier.read_bytes()

            st.download_button(
                "📄 Télécharger le CV",
                data=contenu_pdf,
                file_name=f"{candidat['nom']}_CV.pdf",
                mime="application/pdf",
                key=f"cv_{cid}",
            )

            st.markdown("### Aperçu du CV")
            pdf_base64 = base64.b64encode(contenu_pdf).decode("utf-8")
            st.markdown(
                f'<iframe src="data:application/pdf;base64,{pdf_base64}" '
                'width="100%" height="700" '
                'style="border:1px solid #E2E8F0;border-radius:10px;"></iframe>',
                unsafe_allow_html=True,
            )

            st.markdown("---")
            st.subheader("🧠 Skills & Competencies Analysis")
            texte_cv = texte_pdf(contenu_pdf)
            analyse = calculer_score(texte_cv)

            for critere, detail in analyse["détails"].items():
                st.write(f"**{critere}** — {detail['score']}/{detail['maximum']}")
                st.progress(min(max(detail["score"] / detail["maximum"], 0), 1))
                st.caption(detail["détail"])

            requises = competences_offre(candidat["offre"])
            if requises:
                st.markdown("---")
                st.subheader("🎯 Job Matching")
                matching = calculer_matching_offre(texte_cv, requises)
                st.metric("Job Matching Score", f"{matching['score']}/100")
                st.write(
                    "**Skills Found:** "
                    + (", ".join(matching["competences_trouvees"]) or "—")
                )
                st.write(
                    "**Missing Skills:** "
                    + (", ".join(matching["competences_manquantes"]) or "—")
                )

    # ---- Notes & emails
    st.markdown("---")
    st.subheader("📝 Recruiter Notes")

    notes = charger_notes()
    notes_candidat = notes[
        notes["candidate_id"].astype(str) == str(cid)
    ].sort_values("date", ascending=False)

    with st.form(f"form_note_{cid}", clear_on_submit=True):
        texte_note = st.text_area(
            "Add a note", placeholder="Impressions, points forts, questions..."
        )
        ajouter_note = st.form_submit_button("Add note")

    if ajouter_note and texte_note.strip():
        nouvelle_note = pd.DataFrame([{
            "id": uuid.uuid4().hex[:8],
            "candidate_id": cid,
            "auteur": utilisateur_courant()["nom"],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "note": texte_note.strip(),
        }])
        enregistrer_notes(pd.concat([notes, nouvelle_note], ignore_index=True))
        st.rerun()

    if notes_candidat.empty:
        st.caption("Aucune note pour le moment.")

    for _, note in notes_candidat.iterrows():
        st.markdown(f"**{note['auteur']}** · {note['date']}")
        st.write(note["note"])

    st.markdown("---")
    st.subheader("✉️ Email Templates")

    modele = st.selectbox(
        "Template", list(MODELES_EMAIL.keys()), key=f"modele_{cid}"
    )
    sujet, corps = generer_email(modele, candidat, utilisateur_courant())
    corps_final = st.text_area(
        "Preview (modifiable)", value=corps, height=220,
        key=f"apercu_{cid}_{modele}",
    )
    st.link_button(
        "Open in mail app",
        lien_mailto(candidat["email"], sujet, corps_final),
    )

    # ---- Décision
    st.markdown("---")
    st.subheader("Recruitment Decision")

    nouvelle = st.selectbox(
        "Décision du recruteur",
        DECISIONS,
        index=DECISIONS.index(candidat["decision"]),
        key=f"decision_{cid}",
    )
    if st.button("Save Decision", key=f"save_{cid}"):
        modifier_decision(cid, nouvelle)
        st.success("Décision enregistrée.")
        st.rerun()

    with st.expander("🗑️ Delete this candidate"):
        if not est_admin():
            st.caption("Réservé aux administrateurs.")
        confirme = st.checkbox("Je confirme la suppression", key=f"conf_{cid}")
        if st.button("Delete candidate", key=f"del_{cid}", disabled=not (confirme and est_admin())):
            enregistrer_candidats(
                tableau[tableau["candidate_id"].astype(str) != str(cid)]
            )
            st.success("Candidat supprimé.")
            st.rerun()


# ==========================================
# 6. ADD CANDIDATE
# ==========================================


def ajouter_candidat():
    st.title("Add New Candidate")
    st.markdown("Enregistrez une nouvelle candidature dans TalentRank.")
    st.markdown("---")

    offres = charger_offres()

    with st.form("formulaire_candidature"):
        st.subheader("Personal Information")
        nom = st.text_input("Full Name *")
        email = st.text_input("Email Address *")

        if not offres.empty:
            offre_choisie = st.selectbox(
                "Select Job Offer *", offres_ouvertes()["titre"].tolist()
            )
        else:
            offre_choisie = ""
            st.warning("No job offers available. Create a Job Offer first.")

        st.subheader("Documents")
        cv = st.file_uploader("Upload CV (PDF) *", type=["pdf"])
        source = st.selectbox("Source", SOURCES)

        envoyer = st.form_submit_button(
            "Submit Application", use_container_width=True
        )

    if not envoyer:
        return

    erreurs = []
    if not nom.strip():
        erreurs.append("Le nom est obligatoire.")
    if not email.strip() or "@" not in email:
        erreurs.append("Veuillez saisir un e-mail valide.")
    if cv is None:
        erreurs.append("Veuillez joindre un CV.")
    if not offre_choisie:
        erreurs.append("Créez d'abord une offre d'emploi.")

    existants = charger_candidats()
    if email.strip() and not existants.empty:
        deja = (
            (existants["email"].astype(str).str.lower() == email.strip().lower())
            & (existants["offre"].astype(str) == str(offre_choisie))
        ).any()
        if deja:
            erreurs.append("Ce candidat a déjà postulé à cette offre.")

    if erreurs:
        for erreur in erreurs:
            st.error(erreur)
        return

    try:
        texte_cv = texte_pdf(cv.getvalue())
        resultat = calculer_score(texte_cv)

        dossier_cvs = DATA_DIR / "cvs"
        dossier_cvs.mkdir(parents=True, exist_ok=True)
        chemin = dossier_cvs / f"{uuid.uuid4().hex[:8]}.pdf"
        chemin.write_bytes(cv.getvalue())

        requises = competences_offre(offre_choisie)
        matching = calculer_matching_offre(texte_cv, requises) if requises else None

        nouvelle = pd.DataFrame([{
            "candidate_id": uuid.uuid4().hex[:8],
            "offre": offre_choisie,
            "nom": nom.strip(),
            "email": email.strip(),
            "score": resultat["score"],
            "matching_score": matching["score"] if matching else "",
            "statut": resultat["statut"],
            "date": date.today().isoformat(),
            "decision": "À décider",
            "cv_path": str(chemin.relative_to(BASE_DIR)),
            "source": source,
        }])

        enregistrer_candidats(
            pd.concat([lire_csv(FICHIER_CANDIDATS, COLONNES_CSV), nouvelle],
                      ignore_index=True)
        )

        st.success(f"Candidature reçue pour {nom} !")

        st.subheader("CV Analysis")
        st.metric("General Score", f"{resultat['score']}/100")
        st.write(f"**Status : {resultat['statut']}**")

        if matching:
            st.metric("Job Matching Score", f"{matching['score']}/100")
            st.write("**Skills Found:**")
            st.write(matching["competences_trouvees"])
            st.write("**Missing Skills:**")
            st.write(matching["competences_manquantes"])
        else:
            st.info("No required skills defined for this offer.")

        lignes = [
            {
                "Critère": critere,
                "Score": f"{d['score']} / {d['maximum']}",
                "Détail": d["détail"],
            }
            for critere, d in resultat["détails"].items()
        ]
        st.subheader("Score Details")
        st.dataframe(
            pd.DataFrame(lignes), hide_index=True, use_container_width=True
        )
        st.caption(
            "L'évaluation est indicative. "
            "La décision finale appartient au recruteur."
        )

    except Exception as erreur:
        st.error(f"Erreur lors du traitement du CV : {erreur}")


# ==========================================
# 7. JOB OFFERS
# ==========================================


def afficher_offres():
    st.title("Job Offers Management")
    st.markdown("Create and manage your recruitment offers.")
    st.caption("Page publique de candidature : ajoutez ?careers=1 à l'adresse de l'application.")
    st.markdown("---")

    st.subheader("➕ Create a New Job Offer")

    with st.form("formulaire_offre"):
        col1, col2 = st.columns(2)
        with col1:
            titre = st.text_input("Job Title *")
            departement = st.selectbox(
                "Department",
                ["Human Resources", "Marketing", "Finance", "IT",
                 "Management", "Sales"],
            )
            contrat = st.selectbox(
                "Contract Type", ["CDI", "CDD", "Stage", "Freelance"]
            )
        with col2:
            localisation = st.text_input("Location", placeholder="Casablanca")
            places = st.number_input(
                "Number of Positions", min_value=1, max_value=100, value=1
            )

        description = st.text_area(
            "Job Description *", height=150,
            placeholder="Describe the position and required skills...",
        )
        competences = st.multiselect(
            "Required Skills *", COMPETENCES_DISPONIBLES
        )
        publier = st.form_submit_button(
            "Publish Job Offer", use_container_width=True
        )

    if publier:
        if not titre.strip() or not description.strip():
            st.error("Job Title and Description are required.")
        elif not competences:
            st.error("Select at least one required skill.")
        else:
            offres = charger_offres()
            nouvelle = pd.DataFrame([{
                "id": uuid.uuid4().hex[:8],
                "titre": titre.strip(),
                "departement": departement,
                "contrat": contrat,
                "localisation": localisation.strip(),
                "description": description.strip(),
                "competences_requises": ", ".join(competences),
                "places": places,
                "statut_offre": "Open",
                "date": date.today().isoformat(),
            }])
            enregistrer_offres(pd.concat([offres, nouvelle], ignore_index=True))
            st.success("Job offer published successfully!")
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Published Job Offers")

    offres = charger_offres()
    candidats = charger_candidats()

    if offres.empty:
        st.info("No job offers published yet.")
        return

    st.metric("Total Job Offers", len(offres))

    for _, offre in offres.iterrows():
        postulants = candidats[candidats["offre"].astype(str) == str(offre["titre"])]
        total = len(postulants)
        score_moyen = postulants["score"].mean() if total > 0 else 0
        presel = int((postulants["decision"] == "Présélectionné").sum())

        with st.container(border=True):
            st.markdown(f"### 💼 {offre['titre']}")

            a, b, c = st.columns(3)
            a.write(f"**Department:** {offre['departement']}")
            b.write(f"**Contract:** {offre['contrat']}")
            c.write(f"**Location:** {offre['localisation']}")

            st.markdown("---")
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Applicants", total)
            k2.metric("Average Score", f"{score_moyen:.1f}/100")
            k3.metric("Shortlisted", presel)
            k4.metric("Available Positions", offre["places"])

            with st.expander("📄 View Job Description"):
                st.write(offre["description"])
                st.write(f"**Required Skills:** {offre['competences_requises']}")
                st.caption(f"Published on: {offre['date']}")

            with st.expander("👥 View Applicants"):
                if total > 0:
                    st.dataframe(
                        postulants[["nom", "email", "score", "decision"]]
                        .rename(columns={
                            "nom": "Candidate", "email": "Email",
                            "score": "Matching Score", "decision": "Decision",
                        }),
                        hide_index=True, use_container_width=True,
                    )
                else:
                    st.info("No applicants for this offer yet.")

            ouverte = offre["statut_offre"] != "Closed"
            st.caption("Status : " + ("🟢 Open" if ouverte else "🔴 Closed"))

            if st.button(
                "Close offer" if ouverte else "Reopen offer",
                key=f"toggle_{offre['id']}",
            ):
                offres.loc[offres["id"] == offre["id"], "statut_offre"] = (
                    "Closed" if ouverte else "Open"
                )
                enregistrer_offres(offres)
                st.rerun()

            with st.expander("🗑️ Delete this offer"):
                ok = st.checkbox(
                    "Je confirme la suppression", key=f"conf_offre_{offre['id']}"
                )
                if not est_admin():
                    st.caption("Réservé aux administrateurs.")
                if st.button(
                    "Delete offer", key=f"del_offre_{offre['id']}", disabled=not (ok and est_admin())
                ):
                    enregistrer_offres(offres[offres["id"] != offre["id"]])
                    st.rerun()


# ==========================================
# 8. CANDIDATE COMPARISON
# ==========================================


def afficher_comparaison():
    st.title("⚖️ Candidate Comparison")
    st.markdown("Comparez plusieurs candidats pour une même offre d'emploi.")

    candidats = charger_candidats()
    if candidats.empty:
        st.warning("No candidates available.")
        return

    offres = [o for o in candidats["offre"].astype(str).unique() if o]
    if not offres:
        st.info("No Job Offers linked to candidates.")
        return

    offre_choisie = st.selectbox("Select Job Offer", offres)
    candidats_offre = candidats[candidats["offre"] == offre_choisie].copy()

    if len(candidats_offre) < 2:
        st.warning("You need at least 2 candidates for comparison.")
        return

    candidats_offre["label"] = (
        candidats_offre["nom"].astype(str) + " — "
        + candidats_offre["email"].astype(str)
    )

    selection = st.multiselect(
        "Select candidates to compare",
        candidats_offre["label"].tolist(),
        max_selections=3,
    )
    if len(selection) < 2:
        st.info("Select at least 2 candidates.")
        return

    comparaison = candidats_offre[
        candidats_offre["label"].isin(selection)
    ].sort_values("score", ascending=False)

    requises = competences_offre(offre_choisie)

    st.markdown("---")
    st.subheader("📊 Detailed Skills Comparison")

    lignes = []
    for _, candidat in comparaison.iterrows():
        fichier = chemin_cv(candidat["cv_path"])
        if fichier is None:
            continue
        try:
            texte_cv = texte_pdf(fichier.read_bytes())
            resultat = calculer_score(texte_cv)
            ligne = {"Candidate": candidat["nom"]}
            for critere, d in resultat["détails"].items():
                ligne[critere] = f"{d['score']}/{d['maximum']}"
            if requises:
                matching = calculer_matching_offre(texte_cv, requises)
                ligne["Job Matching"] = f"{matching['score']}%"
                ligne["Missing Skills"] = (
                    ", ".join(matching["competences_manquantes"]) or "—"
                )
            lignes.append(ligne)
        except Exception:
            continue

    if lignes:
        st.dataframe(
            pd.DataFrame(lignes), hide_index=True, use_container_width=True
        )
    else:
        st.warning("No CV details available for comparison.")

    st.markdown("---")
    st.subheader("📊 Comparative Analysis")
    st.dataframe(
        comparaison[["nom", "email", "score", "statut", "decision"]].rename(
            columns={
                "nom": "Candidate", "email": "Email",
                "score": "Matching Score", "statut": "Status",
                "decision": "Recruitment Decision",
            }
        ),
        hide_index=True, use_container_width=True,
    )

    meilleur = comparaison.iloc[0]
    st.success(
        f"🏆 Highest Matching Score: {meilleur['nom']} ({meilleur['score']}/100)"
    )


# ==========================================
# 9. KANBAN BOARD
# ==========================================


def afficher_kanban():
    st.title("📋 Kanban Board")
    st.markdown(
        "Suivez l'évolution des candidatures "
        "à travers les différentes étapes du recrutement."
    )

    candidats = charger_candidats()
    if candidats.empty:
        st.info("Aucun candidat disponible.")
        return

    colonnes = st.columns(len(DECISIONS))

    for colonne, decision in zip(colonnes, DECISIONS):
        with colonne:
            st.subheader(decision)
            selection = candidats[candidats["decision"] == decision]
            st.caption(f"{len(selection)} candidat(s)")

            for _, candidat in selection.iterrows():
                cid = candidat["candidate_id"]
                with st.container(border=True):
                    st.write(f"**{candidat['nom']}**")
                    st.caption(candidat["email"])
                    st.write(f"Score : **{candidat['score']}/100**")

                    nouvelle = st.selectbox(
                        "Changer la décision",
                        DECISIONS,
                        index=DECISIONS.index(decision),
                        key=f"kanban_{cid}",
                    )
                    if st.button("Mettre à jour", key=f"update_{cid}"):
                        modifier_decision(cid, nouvelle)
                        st.rerun()


# ==========================================
# 10. INTERVIEW MANAGEMENT
# ==========================================


def afficher_entretiens():
    st.title("📅 Interview Management")
    st.markdown("Planifiez et gérez les entretiens de recrutement.")
    st.markdown("---")

    candidats = charger_candidats()
    entretiens = charger_entretiens()

    st.subheader("📌 Schedule Interview")

    if candidats.empty:
        st.warning("No candidates available.")
        return

    candidats["label"] = (
        candidats["nom"].astype(str) + " — " + candidats["email"].astype(str)
    )

    with st.form("form_entretien"):
        choix = st.selectbox("Select Candidate", candidats["label"].tolist())
        ligne = candidats[candidats["label"] == choix].iloc[0]
        st.info(f"Job Offer: {ligne['offre']}")

        date_entretien = st.date_input("Interview Date", min_value=date.today())
        heure_entretien = st.time_input("Interview Time")
        type_entretien = st.selectbox("Interview Type", ["Online", "Présentiel"])
        recruteur = st.text_input(
            "Recruiter Name", value=utilisateur_courant()["nom"]
        )

        envoyer = st.form_submit_button(
            "📅 Schedule Interview", use_container_width=True
        )

    if envoyer:
        if not recruteur.strip():
            st.error("Please enter the recruiter name.")
        else:
            nouvelle = pd.DataFrame([{
                "id": uuid.uuid4().hex[:8],
                "candidate_id": ligne["candidate_id"],
                "candidat": ligne["nom"],
                "offre": ligne["offre"],
                "date": date_entretien.isoformat(),
                "heure": heure_entretien.strftime("%H:%M"),
                "type": type_entretien,
                "recruteur": recruteur.strip(),
                "feedback": "",
                "resultat": "En attente",
            }])
            enregistrer_entretiens(
                pd.concat([entretiens, nouvelle], ignore_index=True)
            )
            if ligne["decision"] in ("À décider", "Présélectionné"):
                modifier_decision(ligne["candidate_id"], "Entretien")
            st.success("Interview scheduled successfully! 🎉")
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Interview History")

    if entretiens.empty:
        st.info("No interviews scheduled yet.")
      

      

