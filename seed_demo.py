"""Calcule les scores des CV de démonstration et crée data/candidats.csv."""

import csv
from datetime import date
from pathlib import Path

from pypdf import PdfReader

from make_test_cvs import CANDIDATS, DOSSIER_SORTIE, main as generer_cvs
from scoring import calculer_score


FICHIER_SORTIE = Path(__file__).parent / "data" / "candidats.csv"


def main() -> None:
    """Extrait le texte de chaque CV, le score et écrit les lignes du CSV."""
    # Les PDF sont aussi créés si la seed est déclenchée au tout premier lancement.
    generer_cvs()
    FICHIER_SORTIE.parent.mkdir(parents=True, exist_ok=True)
    date_candidature = date.today().isoformat()

    with FICHIER_SORTIE.open("w", newline="", encoding="utf-8-sig") as fichier_csv:
        colonnes = ["nom", "email", "score", "statut", "date", "decision", "cv_path"]
        redacteur = csv.DictWriter(fichier_csv, fieldnames=colonnes)
        redacteur.writeheader()

        for candidat in CANDIDATS:
            chemin_cv = DOSSIER_SORTIE / str(candidat["fichier"])
            lecteur = PdfReader(str(chemin_cv))
            texte_cv = "\n".join(page.extract_text() or "" for page in lecteur.pages)
            resultat = calculer_score(texte_cv)
            redacteur.writerow({
                "nom": candidat["nom"],
                "email": candidat["email"],
                "score": resultat["score"],
                "statut": resultat["statut"],
                "date": date_candidature,
                "decision": "À décider",
                "cv_path": str(chemin_cv.relative_to(Path(__file__).parent)),
            })
            print(f"{candidat['nom']} : {resultat['score']}/100 — {resultat['statut']}")

    print(f"CSV créé : {FICHIER_SORTIE.relative_to(Path(__file__).parent)}")


if __name__ == "__main__":
    main()
