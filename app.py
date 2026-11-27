from pathlib import Path

code = r'''import streamlit as st
import re
from pathlib import Path

# HR TRACK - AI CV Scanner (prototype)
# Run: streamlit run app.py
# Optional packages for file reading:
# pip install streamlit pypdf python-docx pillow pytesseract
# OCR for images also requires installing the Tesseract application on your computer.

st.set_page_config(
    page_title="HR TRACK | AI CV Scanner",
    page_icon="💜",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------- STYLE --------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #f7f5ff; color: #21164d; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #241747 0%, #35216d 100%);
}
[data-testid="stSidebar"] * { color: #fff !important; }
.brand { font-size: 27px; font-weight: 800; letter-spacing: .5px; }
.brand-sub { color: #c8b8ff; font-size: 13px; margin-top: -8px; }
.main-title { font-size: 34px; font-weight: 800; color: #21164d; margin-bottom: 0; }
.subtitle { color: #655b85; font-size: 15px; margin-top: 4px; }
.panel {
    background: white; border: 1px solid #e7ddff; border-radius: 18px;
    padding: 20px 22px; box-shadow: 0 5px 20px rgba(58,31,120,.045);
}
.soft-panel {
    background: linear-gradient(135deg,#f0eaff,#faf8ff);
    border: 1px solid #e1d4ff; border-radius: 18px; padding: 20px;
}
.metric { font-size: 38px; font-weight: 800; color: #6335d7; }
.muted { color: #766d91; font-size: 13px; }
.tag {
    display:inline-block; background:#eee8ff; color:#4c2aa9;
    padding:5px 10px; border-radius:20px; margin:3px; font-size:12px;
}
.success {
    display:inline-block; background:#d9faed; color:#087b55;
    border-radius:20px; padding:7px 12px; font-size:13px; font-weight:700;
}
div.stButton > button {
    background: linear-gradient(90deg,#6234d4,#8056e9); color:white;
    border:0; border-radius:12px; padding: .65rem 1.1rem; font-weight:700;
}
div.stButton > button:hover { background:#4c27ad; color:white; border:0; }
[data-testid="stFileUploader"] {
    background:#faf8ff; border:2px dashed #b99aff; border-radius:16px; padding:12px;
}
h1,h2,h3 { color:#24184f; }
</style>
""", unsafe_allow_html=True)

# -------------------- HELPERS --------------------
def extract_text(uploaded_file):
    """Extract text from PDF/DOCX/TXT; attempt OCR for JPG/PNG."""
    name = uploaded_file.name.lower()
    raw = uploaded_file.getvalue()

    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader
            import io
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            return f"Impossible de lire le PDF : {e}"

    if name.endswith(".docx"):
        try:
            from docx import Document
            import io
            doc = Document(io.BytesIO(raw))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"Impossible de lire le DOCX : {e}"

    if name.endswith(".txt"):
        return raw.decode("utf-8", errors="ignore")

    if name.endswith((".jpg", ".jpeg", ".png")):
        try:
            from PIL import Image
            import pytesseract
            import io
            image = Image.open(io.BytesIO(raw))
            return pytesseract.image_to_string(image, lang="fra+eng")
        except ImportError:
            return "OCR indisponible : installez Pillow et pytesseract."
        except Exception as e:
            return ("Lecture OCR impossible. Vérifiez que Tesseract OCR est installé "
                    f"sur votre ordinateur. Détail : {e}")
    return "Format non pris en charge."

def find_email(text):
    match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return match.group(0) if match else "Non détecté"

def find_phone(text):
    match = re.search(r"(?:\+212|0)[\s.-]?(?:[5-7])(?:[\s.-]?\d){8}", text)
    return match.group(0) if match else "Non détecté"

def guess_name(text):
    lines = [re.sub(r"\s+", " ", x).strip() for x in text.splitlines() if x.strip()]
    ignored = ("curriculum", "resume", "cv", "profil", "contact", "formation", "expérience")
    for line in lines[:12]:
        if len(line) < 45 and not any(x in line.lower() for x in ignored):
            if not re.search(r"[@:|]", line) and len(line.split()) <= 5:
                return line
    return "Candidat à identifier"

def get_keywords(text):
    dictionary = [
        "Excel", "Word", "PowerPoint", "Communication", "Gestion de projet",
        "Marketing", "Ressources humaines", "Recrutement", "Comptabilité",
        "Python", "Anglais", "Français", "Arabe", "Leadership", "Analyse de données",
        "Service client", "Organisation", "Management", "Canva"
    ]
    low = text.lower()
    return [word for word in dictionary if word.lower() in low]

def compatibility_score(text, job_keywords):
    """Simple demo score based on keyword overlap; not an AI hiring decision."""
    if not job_keywords:
        return None
    low = text.lower()
    found = sum(1 for word in job_keywords if word.lower() in low)
    return round(found / len(job_keywords) * 100)

def section_excerpt(text, terms, limit=450):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if any(term in line.lower() for term in terms):
            return "\n".join(lines[i:i+5])[:limit]
    return "Aucune information clairement détectée."

# -------------------- SIDEBAR --------------------
with st.sidebar:
    st.markdown("<div style='text-align:center;padding:18px 0 26px'>"
                "<div style='font-size:44px'>✦</div>"
                "<div class='brand'>HR TRACK</div>"
                "<div class='brand-sub'>Hire Smarter</div></div>", unsafe_allow_html=True)
    st.markdown("### 🏠  Dashboard")
    st.markdown("### 💼  Offres d'emploi")
    st.markdown("### 👥  Candidats")
    st.markdown("### 🪄  CV Scanner")
    st.markdown("### 📅  Entretiens")
    st.markdown("### 📊  Analytics")
    st.markdown("### ⚙️  Paramètres")
    st.markdown("---")
    st.caption("Digitalisez votre recrutement")

# -------------------- HEADER --------------------
header_left, header_right = st.columns([5, 1])
with header_left:
    st.markdown("<div class='main-title'>🪄 AI CV Scanner</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>Importez un CV (même sous forme de photo) et laissez HR TRACK extraire les informations.</div>", unsafe_allow_html=True)
with header_right:
    st.markdown("<div style='text-align:right;padding-top:15px'><span class='success'>✦ Powered by AI</span></div>", unsafe_allow_html=True)

st.write("")
st.markdown("<div class='panel'>", unsafe_allow_html=True)
st.markdown("### 📤 Importer un CV")
st.write("Glissez votre fichier ici ou cliquez pour le sélectionner.")
uploaded = st.file_uploader(
    "Formats acceptés : PDF, JPG, JPEG, PNG, DOCX, TXT",
    type=["pdf", "jpg", "jpeg", "png", "docx", "txt"],
    label_visibility="visible",
)
st.markdown("</div>", unsafe_allow_html=True)

# Job criteria used for the illustrative matching score
with st.expander("⚙️ Configurer le poste à comparer (facultatif)", expanded=False):
    job_title = st.text_input("Intitulé du poste", "Assistant(e) RH")
    job_keywords_text = st.text_input(
        "Compétences recherchées (séparées par des virgules)",
        "Excel, Communication, Organisation, Recrutement"
    )
    job_keywords = [x.strip() for x in job_keywords_text.split(",") if x.strip()]

if uploaded:
    with st.spinner("Lecture du CV en cours..."):
        cv_text = extract_text(uploaded)

    if cv_text.startswith(("Impossible", "OCR indisponible", "Lecture OCR impossible")):
        st.error(cv_text)
    elif len(cv_text.strip()) < 20:
        st.warning("Peu de texte a été détecté. Essayez un scan plus net ou un PDF avec texte sélectionnable.")
        st.text_area("Texte extrait", cv_text, height=150)
    else:
        name = guess_name(cv_text)
        email = find_email(cv_text)
        phone = find_phone(cv_text)
        skills = get_keywords(cv_text)
        score = compatibility_score(cv_text, job_keywords)

        st.write("")
        left, right = st.columns([1.55, 1])
        with left:
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("### ✨ Résultat de l'analyse")
            st.markdown("<span class='success'>✓ CV lu avec succès</span>", unsafe_allow_html=True)
            st.write("")
            a, b = st.columns([1, 1.5])
            with a:
                st.markdown(f"#### 👤 {name}")
                st.caption("Fiche candidat extraite automatiquement")
                st.markdown("**Contact**")
                st.write(f"✉️ {email}")
                st.write(f"📞 {phone}")
            with b:
                st.markdown("**Informations détectées**")
                st.write(f"**Nom & prénom :** {name}")
                st.write(f"**Email :** {email}")
                st.write(f"**Téléphone :** {phone}")
                st.write(f"**Poste comparé :** {job_title}")
                st.markdown("**Compétences repérées**")
                if skills:
                    st.markdown("".join(f"<span class='tag'>{s}</span>" for s in skills), unsafe_allow_html=True)
                else:
                    st.write("Aucune compétence de la liste de démonstration détectée.")
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown("<div class='soft-panel'>", unsafe_allow_html=True)
            st.markdown("### 📊 Score de compatibilité")
            if score is not None:
                st.markdown(f"<div class='metric'>{score}%</div>", unsafe_allow_html=True)
                st.progress(score / 100)
                st.caption(f"Correspondance des mots-clés pour : {job_title}")
            else:
                st.info("Ajoutez des compétences recherchées pour calculer un score.")
            st.markdown("</div>", unsafe_allow_html=True)
            st.write("")
            st.markdown("<div class='panel'>", unsafe_allow_html=True)
            st.markdown("### 📄 Résumé du profil")
            st.write("**Formation**")
            st.write(section_excerpt(cv_text, ["formation", "education", "diplôme", "diplome"]))
            st.write("**Expérience**")
            st.write(section_excerpt(cv_text, ["expérience", "experience", "stage", "emploi"]))
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        st.markdown("### 🔎 Texte extrait du CV")
        with st.expander("Afficher le texte complet détecté"):
            st.text_area("Contenu", cv_text, height=260)

        st.download_button(
            "⬇️ Télécharger les informations extraites (.txt)",
            data=(
                f"HR TRACK - Fiche candidat\nNom : {name}\nEmail : {email}\n"
                f"Téléphone : {phone}\nCompétences : {', '.join(skills)}\n"
                f"Score indicatif : {score}%\n\nTexte extrait :\n{cv_text}"
            ),
            file_name="fiche_candidat_hr_track.txt",
            mime="text/plain",
        )

        st.warning(
            "Prototype pédagogique : le score est un simple calcul de mots-clés, "
            "pas une décision de recrutement ni une véritable analyse IA. "
            "Vérifiez toujours les informations extraites manuellement."
        )
else:
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("<div class='panel'><h3>📁 Import facile</h3><p class='muted'>CV en PDF, image, DOCX ou TXT.</p></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='panel'><h3>🔍 Extraction</h3><p class='muted'>Détection du nom, email, téléphone et mots-clés.</p></div>", unsafe_allow_html=True)
    with c3:
        st.markdown("<div class='panel'><h3>📊 Matching</h3><p class='muted'>Comparaison indicative avec les critères du poste.</p></div>", unsafe_allow_html=True)

st.markdown("<div style='text-align:center;color:#8b82a5;padding:28px 0 10px;font-size:12px'>HR TRACK · Prototype académique de gestion du recrutement</div>", unsafe_allow_html=True)
'''
path = Path("/mnt/data/app.py")
path.write_text(code, encoding="utf-8")
print(f"Fichier créé : {path}")
print(f"Taille : {path.stat().st_size} octets")

      

