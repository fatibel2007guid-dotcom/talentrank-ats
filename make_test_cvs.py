"""Génère trois CV fictifs pour un poste de chargé de recrutement RH."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


DOSSIER_SORTIE = Path(__file__).parent / "data" / "test_cv"

# Données entièrement fictives, avec des niveaux d'adéquation différents.
CANDIDATS = [
    {
        "fichier": "candidat_fort.pdf",
        "nom": "Camille Martin",
        "email": "camille.martin@example.test",
        "titre": "Chargée de recrutement RH senior",
        "sections": [
            ("Profil", "Chargée de recrutement RH avec 8 ans d'expérience en recrutement de profils variés, du cadrage du besoin à l'intégration."),
            ("Compétences", "Recrutement de bout en bout, sourcing multicanal, conduite d'entretiens structurés, ATS (TalentSoft et Workday), Excel avancé, rédaction d'annonces attractives, gestion de la paie et droit du travail."),
            ("Expérience professionnelle", "2020-2026 — Chargée de recrutement RH senior chez Exemple Conseil : recrutement de profils cadres, sourcing, entretiens structurés, gestion des candidatures dans un ATS, tableaux de suivi Excel et rédaction d'annonces.\n2018-2020 — Consultante recrutement chez Atelier Talents : définition des besoins avec les managers et pilotage des recrutements."),
            ("Formation", "Master Ressources humaines — Université de Lyon, 2018."),
            ("Langues", "Français : langue maternelle. Anglais : courant, niveau C1."),
            ("Qualités", "Communication, travail en équipe, autonomie, organisation et résolution de problèmes."),
        ],
    },
    {
        "fichier": "candidat_moyen.pdf",
        "nom": "Alex Bernard",
        "email": "alex.bernard@example.test",
        "titre": "Assistant recrutement",
        "sections": [
            ("Profil", "Professionnel RH avec 2 ans d'expérience en assistance au recrutement et suivi des candidatures."),
            ("Compétences", "Sourcing sur les réseaux professionnels, présélection de CV, participation aux entretiens, utilisation d'Excel et d'un ATS en formation."),
            ("Expérience professionnelle", "2024-2026 — Assistant recrutement chez Démo RH : sourcing de candidats, présélection des candidatures et participation aux entretiens avec les recruteurs."),
            ("Formation", "Licence Gestion des ressources humaines — Université de Nantes, 2023."),
            ("Langues", "Français : courant. Anglais : intermédiaire, niveau B1."),
            ("Qualités", "Organisation et goût pour le travail en équipe."),
        ],
    },
    {
        "fichier": "candidat_faible.pdf",
        "nom": "Samira Petit",
        "email": "samira.petit@example.test",
        "titre": "Assistante administrative",
        "sections": [
            ("Profil", "Assistante administrative souhaitant évoluer vers les ressources humaines. Pas d'expérience en recrutement."),
            ("Compétences", "Accueil téléphonique, classement de documents, traitement de texte et saisie de données."),
            ("Expérience professionnelle", "2022-2026 — Assistante administrative chez Bureau Exemple : accueil, classement de documents et gestion de planning."),
            ("Formation", "Baccalauréat général — Lycée des Acacias, 2021. Initiation courte aux ressources humaines."),
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
