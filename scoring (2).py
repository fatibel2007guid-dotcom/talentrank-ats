"""Calcul d'un score indicatif pour une candidature de chargé de recrutement RH."""

import re
import unicodedata


PONDERATIONS = {
    "Compétences techniques": 40,
    "Expérience": 25,
    "Formation": 20,
    "Langues": 10,
    "Mots-clés / soft skills": 5,
}


def _normaliser(texte: str) -> str:
    """Met le texte en minuscules et retire les accents pour faciliter la recherche."""
    texte = unicodedata.normalize("NFD", texte.lower())
    return "".join(caractere for caractere in texte if unicodedata.category(caractere) != "Mn")


# Rubriques d'un CV. Pour chacune : (racines de mots, expressions complètes).
# L'ordre compte : « Compétences linguistiques » doit aller dans Langues, pas dans Compétences.
RUBRIQUES = {
    "langues": (("langue", "linguistique", "language"), ()),
    "formation": (
        ("formation", "diplome", "education", "etudes", "cursus"),
        ("parcours academique", "parcours scolaire", "parcours universitaire"),
    ),
    "experience": (("experience",), ("parcours professionnel",)),
    "competences": (
        ("competence", "technologie", "outils", "logiciel", "skills", "aptitudes"),
        ("savoir faire",),
    ),
}

# Mots « neutres » autorisés dans un titre : « Formation et diplômes », « Langues parlées »...
MOTS_NEUTRES = {
    "et", "de", "des", "du", "d", "la", "le", "les", "en", "mes", "mon", "ma",
    "professionnel", "professionnelle", "professionnels", "professionnelles",
    "technique", "techniques", "informatique", "informatiques", "competences",
    "academique", "academiques", "scolaire", "universitaire", "parlees", "principales",
    "cles", "generales", "complementaires", "acquises", "pratiques", "stage", "stages",
    "diplomes", "formations", "certifications", "cv",
}

# Titres connus qui ne comptent pas pour le score : ils terminent la rubrique en cours.
AUTRES_TITRES = {
    "profil", "profil professionnel", "resume", "resume professionnel", "objectif",
    "objectif professionnel", "centres d interet", "centre d interet", "centres d interets",
    "loisirs", "interets", "references", "contact", "contacts", "informations personnelles",
    "coordonnees", "qualites", "atouts", "a propos",
}


def _reconnaitre_titre(fragment: str) -> str | None:
    """Retourne la rubrique si le texte ressemble à un titre de rubrique, sinon None.

    Un titre est court (5 mots max), sans chiffre, et ne contient que le mot-clé
    de la rubrique et des mots neutres. Exemples reconnus : « FORMATION & DIPLÔMES »,
    « Langues parlées », « 3. Parcours professionnel ».
    """
    # On remplace la ponctuation, les symboles (&, :, -, •...) par des espaces.
    texte = re.sub(r"[^a-z0-9]+", " ", _normaliser(fragment)).strip()
    mots = texte.split()
    if not mots or len(mots) > 5:
        return None
    # Seuls les petits numéros de rubrique (« 1. Formation ») sont tolérés, pas les années.
    if any(mot.isdigit() and len(mot) > 2 for mot in mots):
        return None
    if texte in AUTRES_TITRES:
        return "autre"

    for rubrique, (racines, expressions) in RUBRIQUES.items():
        reste = texte
        trouve = False
        for expression in expressions:
            if expression in reste:
                reste = reste.replace(expression, " ")
                trouve = True
        autres_mots = []
        for mot in reste.split():
            if any(mot.startswith(racine) for racine in racines):
                trouve = True
            else:
                autres_mots.append(mot)
        # Les numéros de rubrique (« 1. Formation ») sont tolérés.
        autres_mots = [mot for mot in autres_mots if not mot.isdigit()]
        if trouve and all(mot in MOTS_NEUTRES for mot in autres_mots):
            return rubrique
    return None


def _extraire_sections(texte: str) -> dict[str, str]:
    """Associe les lignes aux rubriques reconnues d'un CV (compétences, expérience...)."""
    sections = {nom: [] for nom in RUBRIQUES}
    section_actuelle = None
    for ligne in texte.splitlines():
        rubrique = _reconnaitre_titre(ligne)
        if rubrique:
            # « autre » = titre connu mais sans effet sur le score : on ferme la rubrique.
            section_actuelle = None if rubrique == "autre" else rubrique
            continue

        # Cas « Langues : Français, Anglais B2 » : titre et contenu sur la même ligne.
        if ":" in ligne:
            gauche, droite = ligne.split(":", 1)
            rubrique = _reconnaitre_titre(gauche)
            if rubrique and rubrique != "autre" and droite.strip():
                section_actuelle = rubrique
                sections[rubrique].append(droite)
                continue

        if section_actuelle:
            sections[section_actuelle].append(ligne)
    return {nom: _normaliser("\n".join(lignes)) for nom, lignes in sections.items()}


def _annees_depuis_periodes(texte_experience: str) -> int:
    """Additionne les durées calendaires des périodes d'expérience, sans double compte."""
    intervalles = []
    for debut, fin in re.findall(r"\b(19\d{2}|20\d{2})\s*[-–—a]\s*(19\d{2}|20\d{2})\b", texte_experience):
        debut, fin = int(debut), int(fin)
        if fin >= debut:
            intervalles.append((debut, fin))

    if not intervalles:
        # Accepte aussi une durée indiquée explicitement si aucune période n'est listée.
        durees = [float(valeur.replace(",", ".")) for valeur in re.findall(
            r"(\d+(?:[,.]\d+)?)\s*ans?\s+(?:d['’ ]experience|experience)", texte_experience
        )]
        return round(max(durees, default=0))

    intervalles.sort()
    debut_courant, fin_courante = intervalles[0]
    annees = 0
    for debut, fin in intervalles[1:]:
        if debut <= fin_courante:
            fin_courante = max(fin_courante, fin)
        else:
            annees += fin_courante - debut_courant
            debut_courant, fin_courante = debut, fin
    return annees + fin_courante - debut_courant


def calculer_score(texte_cv: str) -> dict[str, object]:
    """Retourne le détail pondéré, le total sur 100 et le statut associé."""
    texte = _normaliser(texte_cv)
    sections = _extraire_sections(texte_cv)

    # Une compétence compte seulement si elle figure sous Compétences ou Expérience.
    texte_competences = f"{sections['competences']}\n{sections['experience']}"
    competences = {
        "Recrutement": r"\brecrutement\b|\brecruter\b|\brecruteur\b|\brecruteuse\b",
        "Sourcing": r"\bsourcing\b|\bsourcer\b",
        "Entretien": r"\bentretiens?\b",
        "ATS": r"\bats\b|logiciel de recrutement",
        "Excel": r"\bexcel\b",
        "Rédaction d'annonces": r"redaction.{0,30}annonces?|annonces?.{0,30}redaction|offres d'emploi",
        "Paie": r"\bpaie\b|\bpaye\b",
        "Droit du travail": r"droit du travail|legislation sociale",
        "Entretien structuré": r"entretiens? structures?",
        "GPEC": r"\bgpec\b|gestion previsionnelle des emplois",
    }
    competences_trouvees = [nom for nom, motif in competences.items() if re.search(motif, texte_competences)]
    points_competences = PONDERATIONS["Compétences techniques"] * len(competences_trouvees) / len(competences)

    # Pour cette offre, seules les périodes d'expérience liées aux RH/recrutement comptent.
    texte_experience = sections["experience"]
    experience_recrutement = bool(re.search(
        r"\brecrutement\b|\brecruteur\b|\brecruteuse\b|\bchargee? de recrutement\b|\btalent acquisition\b|\brh\b",
        texte_experience,
    ))
    annees = _annees_depuis_periodes(texte_experience) if experience_recrutement else 0
    points_experience = PONDERATIONS["Expérience"] * min(annees / 4, 1)

    # Le niveau doit être explicitement indiqué dans la rubrique Formation.
    texte_formation = sections["formation"]
    niveau_bac = re.search(r"\bbac\s*\+\s*([3-9])\b", texte_formation)
    if niveau_bac:
        niveau = int(niveau_bac.group(1))
        points_formation = PONDERATIONS["Formation"] if niveau >= 5 else 12.0 if niveau == 3 else 16.0
        detail_formation = f"Bac+{niveau_bac.group(1)} explicite"
    elif re.search(r"\b(master|ingenieur|doctorat)\b", texte_formation):
        points_formation = float(PONDERATIONS["Formation"])
        detail_formation = "Diplôme de niveau Bac+5 ou supérieur détecté"
    elif re.search(r"\blicence\b", texte_formation):
        points_formation = 12.0
        detail_formation = "Licence détectée (score partiel Bac+3; Bac+5 requis pour le maximum)"
    else:
        points_formation = 0.0
        detail_formation = "Aucun diplôme Bac+3 ou supérieur détecté"

    # Français vaut 5 points. L'anglais est gradué selon le niveau CECRL indiqué.
    texte_langues = sections["langues"]
    francais_present = bool(re.search(r"\bfrancais\b", texte_langues))
    anglais_present = bool(re.search(r"\banglais\b", texte_langues))
    anglais_niveau = re.search(r"\b(a1|a2|b1|b2|c1|c2)\b", texte_langues)
    points_anglais = 0.0
    if anglais_present:
        niveau = anglais_niveau.group(1) if anglais_niveau else None
        points_anglais = {"a1": 1.25, "a2": 2.5, "b1": 3.75, "b2": 5.0, "c1": 5.0, "c2": 5.0}.get(niveau, 5.0)
    points_langues = (5.0 if francais_present else 0.0) + points_anglais

    mots_cles = ("communication", "equipe", "autonomie", "organisation", "resolution de problemes")
    nb_mots_cles = sum(mot in texte for mot in mots_cles)
    points_mots_cles = PONDERATIONS["Mots-clés / soft skills"] * nb_mots_cles / len(mots_cles)

    if anglais_present and anglais_niveau:
        detail_langues = f"Français : {'détecté' if francais_present else 'non détecté'}; anglais {anglais_niveau.group(1).upper()}"
    else:
        detail_langues = f"Français : {'détecté' if francais_present else 'non détecté'}; anglais : {'détecté' if anglais_present else 'non détecté'}"

    details = {
        "Compétences techniques": {"score": round(points_competences, 2), "maximum": 40, "détail": f"{len(competences_trouvees)}/{len(competences)} : {', '.join(competences_trouvees) or 'aucune'}"},
        "Expérience": {"score": round(points_experience, 2), "maximum": 25, "détail": f"{annees} an(s) détecté(s), 4 requis"},
        "Formation": {"score": round(points_formation, 2), "maximum": 20, "détail": detail_formation},
        "Langues": {"score": round(points_langues, 2), "maximum": 10, "détail": detail_langues},
        "Mots-clés / soft skills": {"score": round(points_mots_cles, 2), "maximum": 5, "détail": f"{nb_mots_cles}/5 mots-clés"},
    }
    total = round(sum(critere["score"] for critere in details.values()), 2)
    statut = "Refusé" if total < 50 else "À contacter" if total >= 70 else "À étudier"
    return {"score": total, "statut": statut, "détails": details}


if __name__ == "__main__":
    # Exécution directe : calcule et affiche les résultats des CV de démonstration.
    from pathlib import Path

    from pypdf import PdfReader

    dossier_cvs = Path(__file__).parent / "data" / "test_cv"
    for chemin_cv in sorted(dossier_cvs.glob("*.pdf")):
        lecteur = PdfReader(str(chemin_cv))
        texte_extrait = "\n".join(page.extract_text() or "" for page in lecteur.pages)
        resultat = calculer_score(texte_extrait)
        print(f"\n{chemin_cv.name} — {resultat['score']}/100 — {resultat['statut']}")
        for critere, detail in resultat["détails"].items():
            print(f"  {critere}: {detail['score']}/{detail['maximum']} — {detail['détail']}")
