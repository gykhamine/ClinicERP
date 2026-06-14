
## Modules Hôpital (ajoutés)

### 🛏️ Hospitalisation
- **Carte des lits** temps réel — couleurs par statut (libre/occupé/nettoyage)
- **3 bâtiments, 7 services** : Médecine, Pédiatrie, Cardiologie, Chirurgie, Maternité, Réanimation, Urgences
- **73 lits** configurés avec chambres
- Admission, suivi quotidien (constantes vitales + note clinique), transfert inter-services, sortie
- Compte-rendu de sortie avec diagnostic final

### 🚨 Urgences
- Tableau de bord temps réel (auto-refresh 30s) trié par priorité
- **Triage infirmier Manchester** (P1 rouge → P5 blanc) avec constantes vitales + score Glasgow
- Notification automatique médecins pour P1/P2
- Prise en charge médicale, actes tracés en timeline
- Sortie : domicile / hospitalisation / transfert / décès / parti sans soins
- Chronomètre temps de passage

### 🏥 Bloc opératoire
- **Planning journalier** par salle avec statut en temps réel
- Programmation avec équipe (chirurgien + anesthésiste), salle, niveau d'urgence
- **Checklist préopératoire OMS** (12 points, score %) — validation avec % affiché
- Compte-rendu opératoire complet (technique, incidents, pertes sanguines, prescriptions post-op)
- 4 salles opératoires + 8 types d'intervention préconfigurés
- Gestion statut salles (disponible / en cours / nettoyage)

## Structure données démo hôpital

- 3 bâtiments, 7 services, 73 lits (70 libres, 3 occupés)
- 3 hospitalisations actives
- 2 passages urgences actifs (dont 1 P1)
- 1 opération programmée (Appendicectomie)
- 4 salles opératoires, 8 types d'intervention
