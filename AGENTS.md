# Projet: ATS (Applicant Tracking System)

## Identification
- Nom du projet: TalentRank ATS
- Équipe: [smiyetkom]
- Date: 20/11/2026
- Client: [entreprise / service RH]

## Contexte et problématique
Les recruteurs reçoivent beaucoup de CV. Le tri manuel est lent et subjectif.
Comment automatiser l'analyse et le classement des candidatures de façon objective ?

## Objectif mesurable
- Réduire le temps de tri de 70%
- Classer automatiquement 100% des candidatures
- Même critères pour tous les candidats

## Périmètre
- Inclus: dépôt des CV (PDF), extraction du texte, score, classement, fiche candidat
- Exclus: paiement, entretien vidéo, contrat
- Rôle: aide à la décision, le recruteur décide à la fin

## Utilisateurs
- Recruteur, Candidat, Administrateur

## Règles de gestion
- RG1: chaque candidature = CV PDF + email
- RG2: fichier non PDF ou vide = rejeté
- RG3: score calculé selon les critères de l'offre
- RG4: score < 50 = "Refusé"
- RG5: score >= 70 = "À contacter"
- RG6: décision finale = recruteur

## Score et pondération (/100)
- Compétences techniques: 40
- Expérience: 25
- Formation: 20
- Langues: 10
- Mots-clés / soft skills: 5

## Stack technique
- Python + Streamlit
- Code simple, commenté, en français8