"""Calcul d'un score indicatif pour une candidature de chargé de recrutement RH."""

import re
import unicodedata
from datetime import date


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


# Mots qui indiquent un poste lié aux RH / au recrutement (offre « chargé de recrutement »).
MOTIF_POSTE_RH = re.compile(
    r"\brecrutement\b|\brecruter\b|\brecruteur\b|\brecruteuse\b|\btalent acquisition\b"
    r"|\bsourcing\b|\brh\b|\bgrh\b|\bressources humaines\b"
)

# Noms de mois (sans accents) -> numéro. Permet de lire « janvier 2020 - mars 2022 ».
MOIS = {
    "janvier": 1, "janv": 1, "fevrier": 2, "fevr": 2, "fev": 2, "mars": 3, "avril": 4, "avr": 4,
    "mai": 5, "juin": 6, "juillet": 7, "juil": 7, "aout": 8, "septembre": 9, "sept": 9,
    "octobre": 10, "oct": 10, "novembre": 11, "nov": 11, "decembre": 12, "dec": 12,
}
_MOIS = "|".join(MOIS)  # « janvier|janv|... » (les formes longues sont avant les courtes)
# Une date : année seule (2020), mois/année (01/2020) ou « mars 2020 ».
_DATE = r"(?:(?:(" + _MOIS + r")\.?\s+)|(?:(\d{1,2})\s*[/.\-]\s*))?\b(19\d{2}|20\d{2})\b"
_EN_COURS = r"present|aujourd.?hui|actuel|actuellement|en cours|ce jour|now|current"
# Une période : « 2018 - 2020 », « 01/2021 - 11/2026 », « 2021 - Présent ».
MOTIF_PERIODE = re.compile(
    _DATE + r"\s*(?:-|–|—|a|au|jusqu'a|jusqu'au|to)\s*(?:" + _DATE + r"|(" + _EN_COURS + r"))"
)
MOTIF_DEPUIS = re.compile(r"\bdepuis\s+" + _DATE)


def _en_mois(annee: str, nom_mois: str | None, num_mois: str | None, est_fin: bool) -> int:
    """Convertit une date en nombre de mois (année seule : on garde l'ancien calcul en années)."""
    mois = MOIS.get(nom_mois) if nom_mois else (int(num_mois) if num_mois else None)
    if mois is None or not 1 <= mois <= 12:
        return int(annee) * 12
    # Début : le mois commence le 1er ; fin : le mois est compté en entier.
    return int(annee) * 12 + (mois if est_fin else mois - 1)


def _periodes_de_ligne(ligne: str, aujourdhui: date) -> list[tuple[int, int]]:
    """Retourne les périodes (début, fin) en mois trouvées dans une ligne."""
    maintenant = aujourdhui.year * 12 + aujourdhui.month
    periodes = []
    for m in MOTIF_PERIODE.finditer(ligne):
        nom_d, num_d, an_d, nom_f, num_f, an_f, en_cours = m.groups()
        debut = _en_mois(an_d, nom_d, num_d, est_fin=False)
        fin = maintenant if en_cours else _en_mois(an_f, nom_f, num_f, est_fin=True)
        if fin >= debut:
            periodes.append((debut, fin))
    if not periodes:  # « depuis 2021 » = période en cours
        for m in MOTIF_DEPUIS.finditer(ligne):
            nom, num, annee = m.groups()
            debut = _en_mois(annee, nom, num, est_fin=False)
            if maintenant >= debut:
                periodes.append((debut, maintenant))
    return periodes


def _dates_seules(ligne: str) -> bool:
    """Vrai si la ligne ne contient presque que des dates (le titre du poste est ailleurs)."""
    reste = MOTIF_DEPUIS.sub(" ", MOTIF_PERIODE.sub(" ", ligne))
    return len(re.findall(r"[a-z]{3,}", reste)) <= 2


def _annees_experience_rh(texte_experience: str, aujourdhui: date | None = None) -> float:
    """Calcule les années d'expérience RH, sans double compte.

    Chaque poste (une période + le texte qui l'accompagne) n'est compté que s'il parle
    de RH / recrutement. Un poste de vendeur ne compte donc pas, même placé à côté
    d'un poste de recruteur.
    """
    aujourdhui = aujourdhui or date.today()
    texte_experience = _normaliser(texte_experience)  # sans effet si déjà normalisé
    lignes = [ligne.strip() for ligne in texte_experience.splitlines() if ligne.strip()]
    periodes_par_ligne = {i: _periodes_de_ligne(ligne, aujourdhui) for i, ligne in enumerate(lignes)}
    indices = [i for i, periodes in periodes_par_ligne.items() if periodes]

    if not indices:
        # Aucune période : on accepte une durée explicite (« 8 ans d'expérience »), si RH.
        if not MOTIF_POSTE_RH.search(" ".join(lignes)):
            return 0.0
        durees = [float(valeur.replace(",", ".")) for valeur in re.findall(
            r"(\d+(?:[,.]\d+)?)\s*ans?\s+(?:d['’ ]experience|experience)", " ".join(lignes)
        )]
        return round(max(durees, default=0.0), 1)

    # Où est le titre du poste ? Si la 1re date est seule sur sa ligne et qu'un titre court
    # la précède, on suppose que chaque titre est AU-DESSUS de ses dates ; sinon il est
    # sur la même ligne ou en dessous.
    premier = indices[0]
    titre_au_dessus = premier > 0 and _dates_seules(lignes[premier]) and len(lignes[premier - 1].split()) <= 8

    intervalles = []
    for rang, i in enumerate(indices):
        a_un_suivant = rang + 1 < len(indices)
        suivant = indices[rang + 1] if a_un_suivant else len(lignes)
        if titre_au_dessus:
            debut_bloc, fin_bloc = i - 1, (suivant - 1 if a_un_suivant else suivant)
        else:
            debut_bloc, fin_bloc = i, suivant
        bloc = " ".join(lignes[max(debut_bloc, 0):max(fin_bloc, i)])
        if MOTIF_POSTE_RH.search(bloc):
            intervalles.extend(periodes_par_ligne[i])

    if not intervalles:
        return 0.0
    intervalles.sort()
    debut_courant, fin_courante = intervalles[0]
    total_mois = 0
    for debut, fin in intervalles[1:]:
        if debut <= fin_courante:  # chevauchement : on fusionne pour ne pas compter deux fois
            fin_courante = max(fin_courante, fin)
        else:
            total_mois += fin_courante - debut_courant
            debut_courant, fin_courante = debut, fin
    total_mois += fin_courante - debut_courant
    return round(total_mois / 12, 1)


def calculer_score(texte_cv: str, aujourdhui: date | None = None) -> dict[str, object]:
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
    annees = _annees_experience_rh(sections["experience"], aujourdhui)
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
        "Expérience": {"score": round(points_experience, 2), "maximum": 25, "détail": f"{annees:g} an(s) d'expérience RH détecté(s), 4 requis"},
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
