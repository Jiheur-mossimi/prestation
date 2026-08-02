# Liste des Utilisateurs - Système de Gestion des Prestations

## Comptes de Connexion

Tous les utilisateurs ont le mot de passe par défaut : **demo123**

### Comptes Principaux

| Rôle | Username | Mot de passe | Description |
|------|----------|--------------|-------------|
| 👑 Admin | `admin` | `demo123` | Administrateur système (superuser) |
| 📋 Secrétaire | `secretaire` | `demo123` | Secrétaire de direction |
| ⚖️ Préfet | `prefet` | `demo123` | Préfet de discipline (Agent) |
| 📚 Enseignant | `enseignant` | `demo123` | Enseignant de test |

### Utilisateurs Générés Automatiquement

Lorsqu'un agent est créé dans le système, un utilisateur est automatiquement généré avec :
- **Username** : matricule de l'agent (en minuscules)
  - Ex: `ENS001`, `ADM001`, etc.
- **Mot de passe** : `demo123`
- **Rôle** : déterminé par le type d'agent
  - `ENSEIGNANT` → Rôle ENSEIGNANT
  - `ADMINISTRATIF` → Rôle SECRETAIRE
  - `DISCIPLINE` → Rôle AGENT

## Rôles et Permissions

### ADMIN (Administrateur)
- Accès complet à toutes les fonctionnalités
- Peut gérer les utilisateurs, agents, services, classes, cours, fonctions, mois
- Peut ouvrir et clôturer des sessions de prestation
- Voit tous les messages et notifications
- Accès au dashboard global

### SECRETAIRE (Secrétaire)
- Accès aux fonctionnalités de gestion
- Peut gérer les agents, services, classes, cours
- Peut ouvrir et clôturer des sessions de prestation
- Voit tous ses messages et notifications
- Accès au dashboard

### AGENT (Agent administratif / Préfet)
- Peut pointer son arrivée et départ
- Accès à ses propres prestations
- Voit uniquement les messages/notifications envoyés par l'admin
- Accès à son historique personnel
- Dashboard personnalisé

### ENSEIGNANT
- Peut pointer son arrivée et départ
- Accès à ses propres prestations
- Peut créer des prestations enseignants (cours + classes)
- Voit uniquement les messages/notifications envoyés par l'admin
- Accès à son historique personnel
- Dashboard personnalisé avec ses cours

## Accès aux Messages et Notifications

### Admin et Secrétaire
- Voient **tous** leurs messages (envoyés et reçus)
- Voient **toutes** leurs notifications

### Agents et Enseignants
- Ne voient **que** les messages envoyés par un administrateur
- Ne voient **que** les notifications envoyées par un administrateur

## Procédure de Première Connexion

1. Se connecter avec le username et le mot de passe par défaut
2. Le système demande de changer le mot de passe (must_change_password = True)
3. L'utilisateur définit un nouveau mot de passe personnel
4. Le mot de passe temporaire est effacé

## Script de Génération de Données

Pour générer des données de démonstration :

```bash
python manage.py demo_data
```

Ce script crée :
- 8 services
- 22 classes
- 10 fonctions
- 12 mois
- 15 cours
- 50 agents (40 enseignants + 10 administratifs)
- 4 utilisateurs principaux (admin, secretaire, prefet, enseignant)
- 30 sessions de prestation
- Des centaines de prestations
- Des messages et notifications

## Notes Importantes

- Tous les mots de passe temporaires sont définis sur `demo123` pour faciliter les tests
- Le mot de passe admin123 a été remplacé par demo123 pour l'uniformité
- Les agents créés manuellement ou via le script ont tous le même mot de passe par défaut
- Il est recommandé de changer les mots de passe en environnement de production