"""Génère trois CV fictifs de développeurs Python au format PDF."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


DOSSIER_SORTIE = Path(__file__).parent / "data" / "test_cv"

# Données entièrement fictives, avec des niveaux d'expérience différents.
CANDIDATS = [
    {
        "fichier": "candidat_fort.pdf",
        "nom": "Camille Martin",
        "email": "camille.martin@example.test",
        "titre": "Développeuse Python senior",
        "sections": [
            ("Profil", "Développeuse Python avec 7 ans d'expérience dans la conception et la mise en production d'applications web et de services de données."),
            ("Compétences techniques", "Python, Django, FastAPI, Flask, PostgreSQL, SQLAlchemy, Redis, Celery, REST, Docker, Kubernetes, Git, pytest, CI/CD, AWS."),
            ("Expérience professionnelle", "2021-2026 — Développeuse Python senior chez Exemple Logiciel : conception d'API FastAPI, optimisation PostgreSQL, revue de code et encadrement de 3 développeurs.\n2018-2021 — Développeuse backend chez Atelier Numérique : services Django, tests automatisés et intégration continue."),
            ("Formation", "Master Informatique, spécialité génie logiciel — Université de Lyon, 2018."),
            ("Langues", "Français : langue maternelle. Anglais : courant, niveau C1."),
            ("Qualités", "Résolution de problèmes, communication, travail en équipe, autonomie et mentorat."),
        ],
    },
    {
        "fichier": "candidat_moyen.pdf",
        "nom": "Alex Bernard",
        "email": "alex.bernard@example.test",
        "titre": "Développeur Python",
        "sections": [
            ("Profil", "Développeur logiciel avec 2 ans d'expérience, intéressé par le développement backend en Python."),
            ("Compétences techniques", "Python, Flask, bases de SQL, Git, HTML, CSS, notions de Django et de tests unitaires."),
            ("Expérience professionnelle", "2024-2026 — Développeur junior chez Démo Web : création de petites fonctionnalités Flask, maintenance d'une API et correction de bugs avec l'équipe."),
            ("Formation", "Licence Informatique — Université de Nantes, 2023."),
            ("Langues", "Français : courant. Anglais : intermédiaire, niveau B1."),
            ("Qualités", "Curiosité, organisation et goût pour l'apprentissage en équipe."),
        ],
    },
    {
        "fichier": "candidat_faible.pdf",
        "nom": "Samira Petit",
        "email": "samira.petit@example.test",
        "titre": "Assistante polyvalente en reconversion",
        "sections": [
            ("Profil", "Assistante administrative souhaitant découvrir les métiers du numérique. Aucune expérience professionnelle en développement."),
            ("Compétences", "Utilisation courante d'un ordinateur, traitement de texte et tableur. Quelques exercices d'initiation à la programmation suivis en ligne."),
            ("Expérience professionnelle", "2022-2026 — Assistante administrative chez Bureau Exemple : accueil, classement de documents et gestion de planning."),
            ("Formation", "Baccalauréat général — Lycée des Acacias, 2021."),
            ("Langues", "Français : langue maternelle. Anglais : notions, niveau A2."),
            ("Objectif", "Suivre une formation en programmation et acquérir une première expérience en développement Python."),
        ],
    },
]


def creer_cv(candidat: dict[str, object]) -> None:
    """Crée un PDF contenant du texte sélectionnable et extractible."""
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(str(candidat["nom"]), styles["Title"]),
        Paragraph(str(candidat["titre"]), styles["Heading2"]),
        Paragraph(str(candidat["email"]), styles["Normal"]),
        Spacer(1, 0.4 * cm),
    ]

    for titre, contenu in candidat["sections"]:  # type: ignore[index]
        elements.append(Paragraph(titre, styles["Heading3"]))
        # ReportLab interprète le contenu comme du balisage XML.
        contenu_formate = str(contenu).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        contenu_formate = contenu_formate.replace("\n", "<br/>")
        elements.append(Paragraph(contenu_formate, styles["BodyText"]))
        elements.append(Spacer(1, 0.25 * cm))

    chemin = DOSSIER_SORTIE / str(candidat["fichier"])
    document = SimpleDocTemplate(
        str(chemin),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.7 * cm,
        bottomMargin=1.7 * cm,
        title=f"CV fictif - {candidat['nom']}",
    )
    document.build(elements)
    print(f"CV créé : {chemin.relative_to(Path(__file__).parent)}")


def main() -> None:
    DOSSIER_SORTIE.mkdir(parents=True, exist_ok=True)
    for candidat in CANDIDATS:
        creer_cv(candidat)


if __name__ == "__main__":
    main()
