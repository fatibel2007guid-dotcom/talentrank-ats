"""Génère des CV fictifs en PDF texte pour l'offre de recrutement RH."""

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


DOSSIER_SORTIE = Path(__file__).parent / "data" / "test_cv"

# CV fictifs utilisés pour les dix candidatures de démonstration.
CANDIDATS = [
    {
        "fichier": "kenza_el_amrani.pdf", "nom": "Kenza El Amrani", "email": "kenza.elamrani@example.test",
        "titre": "Chargée de recrutement RH senior",
        "sections": [
            ("Profil", "Professionnelle des ressources humaines avec 10 ans d'expérience en recrutement de bout en bout, accompagnement des managers et intégration."),
            ("Expériences", "2021-2026 — Chargée de recrutement senior chez Atlas Conseil : pilotage des recrutements cadres, sourcing, entretiens structurés, ATS, Excel et rédaction d'annonces.\n2016-2021 — Chargée de recrutement chez Horizon Maroc : recueil des besoins, sélection, entretiens et suivi d'intégration."),
            ("Formation", "Master Ressources humaines — Université Hassan II, Casablanca, 2016."),
            ("Compétences", "Recrutement, sourcing, entretiens structurés, ATS, Excel avancé, rédaction d'annonces, droit du travail, paie, communication, organisation, autonomie et travail en équipe."),
            ("Langues", "Arabe : langue maternelle. Français : courant. Anglais : niveau C1."),
        ],
    },
    {
        "fichier": "youssef_tazi.pdf", "nom": "Youssef Tazi", "email": "youssef.tazi@example.test",
        "titre": "Responsable recrutement",
        "sections": [
            ("Profil", "Responsable RH avec 7 ans d'expérience en recrutement et gestion des talents dans les services et l'industrie."),
            ("Expériences", "2022-2026 — Responsable recrutement chez Novacentre : définition des besoins, sourcing, entretiens, ATS et suivi des indicateurs.\n2019-2022 — Chargé de recrutement chez Recrutis Maroc : recrutement de profils opérationnels, rédaction d'annonces et intégration."),
            ("Formation", "Master Management des ressources humaines — Université Cadi Ayyad, Marrakech, 2019."),
            ("Compétences", "Recrutement, sourcing, entretiens structurés, ATS, Excel, rédaction d'annonces, droit du travail, communication et organisation."),
            ("Langues", "Arabe : langue maternelle. Français : courant. Anglais : niveau B2."),
        ],
    },
    {
        "fichier": "imane_alaoui.pdf", "nom": "Imane Alaoui", "email": "imane.alaoui@example.test",
        "titre": "Consultante en recrutement",
        "sections": [
            ("Profil", "Consultante en cabinet avec 6 ans d'expérience en recherche de talents, relation client et recrutement mult secteur."),
            ("Expériences", "2022-2026 — Consultante recrutement chez Cabinet Alizé : cadrage des postes, sourcing, présélection, entretiens et présentation des candidats.\n2020-2022 — Chargée de recherche chez Talentia Maroc : identification de profils, suivi de candidatures et coordination des entretiens."),
            ("Formation", "Licence professionnelle Gestion des ressources humaines — Université Ibn Zohr, Agadir, 2020."),
            ("Compétences", "Recrutement, sourcing, entretiens, ATS, Excel, rédaction d'annonces, communication, autonomie et organisation."),
            ("Langues", "Arabe : langue maternelle. Français : courant. Anglais : niveau B2."),
        ],
    },
    {
        "fichier": "omar_berrada.pdf", "nom": "Omar Berrada", "email": "omar.berrada@example.test",
        "titre": "RH généraliste",
        "sections": [
            ("Profil", "RH généraliste avec 5 ans d'expérience couvrant le recrutement, l'administration du personnel et l'accompagnement des équipes."),
            ("Expériences", "2023-2026 — RH généraliste chez Groupe Safa : recrutement, sourcing, entretiens, intégration et gestion des dossiers du personnel.\n2021-2023 — Assistant RH chez Maghreb Services : publication d'annonces, présélection et suivi des candidatures."),
            ("Formation", "Licence professionnelle Ressources humaines — École supérieure de gestion de Rabat, 2021."),
            ("Compétences", "Recrutement, sourcing, entretiens, ATS, Excel, rédaction d'annonces, paie, droit du travail, travail en équipe et organisation."),
            ("Langues", "Arabe : langue maternelle. Français : courant. Anglais : niveau B1."),
        ],
    },
    {
        "fichier": "salma_benjelloun.pdf", "nom": "Salma Benjelloun", "email": "salma.benjelloun@example.test",
        "titre": "Assistante RH",
        "sections": [
            ("Profil", "Assistante RH avec 2 ans d'expérience en administration du personnel et appui aux opérations de recrutement."),
            ("Expériences", "2024-2026 — Assistante RH chez Caravane Distribution : tri des CV, convocations aux entretiens, mise à jour de l'ATS et suivi administratif des nouvelles recrues."),
            ("Formation", "Licence Gestion des ressources humaines — Université Abdelmalek Essaâdi, Tanger, 2023."),
            ("Compétences", "Recrutement, sourcing, entretiens, ATS, Excel, rédaction d'annonces, communication, organisation et travail en équipe."),
            ("Langues", "Arabe : langue maternelle. Français : courant. Anglais : niveau B2."),
        ],
    },
    {
        "fichier": "nadia_chraibi.pdf", "nom": "Nadia Chraibi", "email": "nadia.chraibi@example.test",
        "titre": "Gestionnaire de paie",
        "sections": [
            ("Profil", "Gestionnaire de paie avec 11 ans d'expérience en administration du personnel, déclarations sociales et accompagnement RH."),
            ("Expériences", "2020-2026 — Gestionnaire de paie senior chez Fiduciaire Al Amal : préparation et contrôle de la paie, conseil social et gestion des dossiers du personnel.\n2015-2020 — Gestionnaire paie chez Services du Détroit : bulletins, absences, déclarations et réponses aux salariés."),
            ("Formation", "Licence Gestion — Université Hassan II, Casablanca, 2015."),
            ("Compétences", "Paie, droit du travail, administration du personnel, Excel, déclarations sociales, organisation, rigueur et communication."),
            ("Langues", "Arabe : langue maternelle. Français : courant. Anglais : niveau B1."),
        ],
    },
    {
        "fichier": "hamza_idrissi.pdf", "nom": "Hamza Idrissi", "email": "hamza.idrissi@example.test",
        "titre": "Assistant administratif",
        "sections": [
            ("Profil", "Assistant administratif rigoureux, avec une première expérience de soutien aux équipes et un intérêt pour les ressources humaines."),
            ("Expériences", "2023-2026 — Assistant administratif chez Bureau Al Wifaq : accueil, classement, gestion des plannings, saisie de données et appui ponctuel aux dossiers du personnel."),
            ("Formation", "Baccalauréat économie et gestion — Lycée Ibn Battouta, 2022."),
            ("Compétences", "Accueil, bureautique, Excel, classement, gestion de planning, saisie de données, organisation et travail en équipe."),
            ("Langues", "Arabe : langue maternelle. Français : intermédiaire. Anglais : niveau A2."),
        ],
    },
    {
        "fichier": "reda_lahlou.pdf", "nom": "Reda Lahlou", "email": "reda.lahlou@example.test",
        "titre": "Stagiaire RH",
        "sections": [
            ("Profil", "Jeune diplômé en ressources humaines à la recherche d'un stage pour développer ses compétences en recrutement."),
            ("Expériences", "2025-2026 — Stagiaire RH chez Initiative Emploi : aide au tri des CV, préparation des dossiers de candidature et participation à la planification des entretiens."),
            ("Formation", "Licence Ressources humaines — Université Moulay Ismaïl, Meknès, 2025."),
            ("Compétences", "Notions de recrutement, recherche documentaire, Excel, bureautique, communication, autonomie et esprit d'équipe."),
            ("Langues", "Arabe : langue maternelle. Français : courant. Anglais : niveau B1."),
        ],
    },
    {
        "fichier": "sara_mouline.pdf", "nom": "Sara Mouline", "email": "sara.mouline@example.test",
        "titre": "Community manager",
        "sections": [
            ("Profil", "Community manager créative, spécialisée dans l'animation de communautés et la production de contenus numériques."),
            ("Expériences", "2022-2026 — Community manager chez Studio Médina : calendrier éditorial, animation des réseaux sociaux, création de contenus et analyse des audiences."),
            ("Formation", "Licence Communication digitale — Institut supérieur de communication, Casablanca, 2022."),
            ("Compétences", "Réseaux sociaux, création de contenu, rédaction, outils graphiques, analyse d'audience, organisation et communication."),
            ("Langues", "Arabe : langue maternelle. Français : courant. Anglais : niveau B2."),
        ],
    },
    {
        "fichier": "anas_fassi.pdf", "nom": "Anas Fassi", "email": "anas.fassi@example.test",
        "titre": "Technicien informatique",
        "sections": [
            ("Profil", "Technicien informatique orienté support utilisateurs, maintenance de postes et résolution d'incidents."),
            ("Expériences", "2023-2026 — Technicien informatique chez Atlas Numérique : assistance aux utilisateurs, préparation des postes, inventaire du matériel et résolution des incidents."),
            ("Formation", "Diplôme de technicien spécialisé en systèmes informatiques — OFPPT, Rabat, 2023."),
            ("Compétences", "Support informatique, Windows, réseaux, maintenance, gestion des incidents, documentation et travail en équipe."),
            ("Langues", "Arabe : langue maternelle. Français : courant. Anglais : niveau B1."),
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
        elements.append(Paragraph(contenu_formate.replace("\n", "<br/>"), styles["BodyText"]))
        elements.append(Spacer(1, 0.25 * cm))

    chemin = DOSSIER_SORTIE / str(candidat["fichier"])
    document = SimpleDocTemplate(
        str(chemin), pagesize=A4, rightMargin=2 * cm, leftMargin=2 * cm,
        topMargin=1.7 * cm, bottomMargin=1.7 * cm,
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
