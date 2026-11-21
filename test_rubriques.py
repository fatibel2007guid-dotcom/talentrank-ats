"""Tests simples de la détection des rubriques (lancer : python test_rubriques.py)."""

from scoring import _extraire_sections, _reconnaitre_titre, calculer_score

# 1. Variantes de titres qui doivent être reconnues.
TITRES_OK = {
    "Formation & Diplômes": "formation",
    "FORMATION ET DIPLOMES": "formation",
    "Parcours académique": "formation",
    "Études": "formation",
    "1. Formation": "formation",
    "Parcours professionnel": "experience",
    "EXPÉRIENCES PROFESSIONNELLES": "experience",
    "Expérience & stages": "experience",
    "Langues parlées": "langues",
    "Compétences linguistiques": "langues",
    "• LANGUES :": "langues",
    "Compétences techniques": "competences",
    "Outils et logiciels": "competences",
    "Savoir-faire": "competences",
    "Centres d'intérêt": "autre",
}
for titre, attendu in TITRES_OK.items():
    obtenu = _reconnaitre_titre(titre)
    assert obtenu == attendu, f"{titre!r} : attendu {attendu}, obtenu {obtenu}"

# 2. Lignes ordinaires qui ne doivent PAS être prises pour des titres.
PAS_DES_TITRES = [
    "Rédaction d'offres d'emploi",
    "Études de marché sur les salaires",
    "Formation des managers au recrutement",
    "Expérience en sourcing de profils IT",
    "Chargée de recrutement 2018 - 2024",
    "Master RH 2016",
    "Anglais B2",
]
for ligne in PAS_DES_TITRES:
    assert _reconnaitre_titre(ligne) is None, f"{ligne!r} reconnu à tort"

# 3. CV complet avec des titres « non standard » : doit désormais être noté.
cv = """Profil
Passionnée par les RH.
Parcours professionnel
Chargée de recrutement 2018 - 2024
Sourcing, entretiens structurés, ATS
Formation & Diplômes
Master RH Bac+5
Langues parlées
Français, Anglais B2
Centres d'intérêt
Lecture, équipe de foot
"""
sections = _extraire_sections(cv)
assert "chargee de recrutement" in sections["experience"]
assert "master rh" in sections["formation"]
assert "anglais b2" in sections["langues"]
assert "foot" not in sections["langues"], "les centres d'intérêt ne doivent pas déborder"
resultat = calculer_score(cv)
assert resultat["détails"]["Expérience"]["score"] > 0
assert resultat["détails"]["Formation"]["score"] == 20
assert resultat["détails"]["Langues"]["score"] == 10.0

# 4. Titre et contenu sur la même ligne.
sections = _extraire_sections("Langues : Français, Anglais C1\nFormation : Master RH")
assert "anglais c1" in sections["langues"] and "master rh" in sections["formation"]

print("Tous les tests passent.")
