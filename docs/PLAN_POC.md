# Plan POC Support IA TheHive

## 1. But du POC

Le POC doit reduire le temps de premiere analyse d'un ticket support TheHive sans envoyer de donnees hors de l'environnement interne.

Sortie attendue pour chaque ticket cible:

- une analyse structuree
- une liste de tickets similaires
- une proposition de reponse dans le style de l'agent assigne
- une note interne publiee dans Jira

Le POC ne doit pas envoyer automatiquement de reponse au client.

## 2. Perimetre V1

Inclus:

- synchronisation Jira par polling
- recherche JQL sur tickets recents et mis a jour
- stockage local tickets et commentaires
- reconstruction conversation client/support
- ranking simple de tickets proches
- generation LLM locale avec JSON strict
- publication d'une note interne Jira

Exclus du premier sprint:

- webhooks Jira
- embeddings et pgvector
- UI dediee
- auto-reponse publique
- fine-tuning du style

## 3. Architecture cible du POC

Flux:

`Jira -> sync -> Postgres -> retrieval -> LLM interne -> suggestion -> commentaire interne Jira`

Composants:

- `api`: expose les endpoints de controle et de test
- `jira_sync`: recupere issues et commentaires
- `storage`: persiste tickets, messages, suggestions, profils agent
- `retrieval`: rapproche le ticket courant de l'historique
- `analyzer`: produit une analyse structuree
- `publisher`: envoie une note interne dans Jira
- `scheduler`: declenche sync et analyse regulieres

## 4. Hypotheses techniques

- Jira est accessible via API REST et token technique
- le modele de generation est deploye en interne
- la base locale peut tourner sur Postgres
- le POC peut etre execute sur une machine interne ou une VM privee

## 5. Contraintes securite

Obligatoire des le debut:

- aucun appel a un fournisseur LLM externe
- secrets dans variables d'environnement ou gestionnaire de secrets
- journaux applicatifs sans dump integral des tickets
- note Jira interne uniquement
- trace de chaque suggestion: modele, prompt_version, sources utilisees, score

Recommande:

- redaction des emails et IP dans les logs
- acces restreint au serveur LLM
- segmentation reseau si deploiement AWS

## 6. Mode de deploiement recommande

### Option la plus rapide

Machine interne ou VM Linux:

- app Python
- Postgres
- serveur LLM local
- scheduler integre

### Option industrialisable

AWS prive:

- ECS pour l'application
- RDS PostgreSQL
- service LLM sur EC2 privee ou conteneur GPU prive
- Secrets Manager
- subnets prives et security groups fermes

## 7. Plan de mise en place rapide

### Phase 0 - cadrage technique (0.5 jour)

Livrables:

- compte technique Jira pour API
- choix du projet Jira cible
- choix de l'environnement de test
- choix du modele interne pour le POC

Checklist:

- valider l'authentification Jira
- lister les champs utiles
- definir les agents support cibles
- confirmer la politique securite sur les tickets

### Phase 1 - boucle minimale bout en bout (2 jours)

Objectif:

analyser un ticket a la demande et publier une note interne Jira.

Travaux:

- initialiser le repo Python
- creer configuration et logging
- implementer client Jira
- recuperer issue + commentaires
- normaliser les messages
- brancher le client LLM interne
- generer un JSON simple
- poster une note Jira

Critere de sortie:

`POST /analyze/{jira_key}` fonctionne sur un ticket reel.

### Phase 2 - synchronisation et historique local (2 jours)

Objectif:

alimenter une base locale pour pouvoir relier les tickets entre eux.

Travaux:

- creer le schema Postgres
- implementer `POST /sync`
- synchroniser les tickets recents avec JQL
- persister tickets et commentaires
- detecter les tickets a reanalyser

Critere de sortie:

historique local exploitable sur plusieurs jours.

### Phase 3 - tickets similaires utiles (2 jours)

Objectif:

remonter 3 a 5 tickets proches avec raisons lisibles.

Travaux:

- indexer summary, description et commentaires nettoyes
- extraire quelques signaux: produit, version, composant, erreurs
- ajouter un score hybride lexical + bonus metiers
- sauvegarder les liens IA

Critere de sortie:

les tickets lies sont juges pertinents par un agent support.

### Phase 4 - style agent et qualite du draft (2 jours)

Objectif:

produire un brouillon plus proche des habitudes de reponse des agents.

Travaux:

- collecter des reponses passees par agent
- construire un profil de style JSON
- injecter ce profil dans le prompt
- distinguer faits, hypotheses, manques, prochaines actions

Critere de sortie:

les drafts sont reutilisables apres edition legere.

### Phase 5 - stabilisation POC (1 a 2 jours)

Objectif:

rendre le systeme presentable et pilotable.

Travaux:

- scheduler de sync toutes les 5 minutes
- endpoint health
- traces et erreurs propres
- documentation de deploiement
- jeu de tests minimal

Critere de sortie:

POC executable de facon stable en interne.

## 8. Roadmap 10 jours

### Jours 1-2

- repo et environnement
- client Jira
- endpoint `POST /analyze/{jira_key}`
- client LLM interne
- publication note Jira

### Jours 3-4

- schema DB
- persistance tickets et commentaires
- endpoint `POST /sync`
- sync JQL recents

### Jours 5-6

- ranking tickets similaires
- stockage suggestions et liens
- format de note interne lisible

### Jours 7-8

- profils de style agent
- prompt plus strict
- score de confiance

### Jours 9-10

- scheduler
- logs et tests
- mini demo utilisateur

## 9. Requetes Jira a prevoir

JQL de depart:

```text
project = SUPPORT AND updated >= -30m ORDER BY updated DESC
project = SUPPORT AND created >= -1d ORDER BY created DESC
project = SUPPORT AND statusCategory != Done AND updated >= -1d ORDER BY updated DESC
project = SUPPORT AND assignee is not EMPTY AND updated >= -1d ORDER BY updated DESC
```

API utiles:

- search issues
- get issue details
- get comments
- add comment

## 10. Donnees a stocker

Tables minimales:

- `tickets`
- `ticket_messages`
- `ticket_suggestions`
- `ticket_links_ai`
- `agent_profiles`

Champs indispensables:

- cle Jira, statut, assignee, summary, description
- commentaires avec auteur et role
- timestamps Jira
- suggestion generee et confiance
- tickets relies et raison du rapprochement

## 11. Strategie de recherche de tickets similaires

Version POC:

- overlap lexical sur summary et description
- bonus si meme produit
- bonus si meme version
- bonus si meme composant
- bonus si meme motif d'erreur

Version 2:

- embeddings locaux
- pgvector
- doc interne en plus des tickets

## 12. Strategie style agent

Le style est derive de l'historique, pas d'un fine-tuning.

Pour chaque agent cible:

- recuperer 30 a 100 reponses
- mesurer longueur moyenne
- extraire formulations d'ouverture
- extraire formulations de cloture
- extraire formulations de demande d'information
- stocker un profil JSON

Exemple:

```json
{
  "tone": "professional, calm, precise",
  "structure": [
    "acknowledge issue",
    "state current understanding",
    "ask precise follow-up questions",
    "propose next step"
  ],
  "preferred_phrases": [
    "From what I can see",
    "Could you please confirm"
  ],
  "avoid": [
    "unsupported certainty",
    "long vague paragraphs"
  ]
}
```

## 13. Format de sortie LLM

Le modele doit rendre du JSON strict:

```json
{
  "analysis": {
    "issue_type": "",
    "observations": [],
    "hypotheses": [],
    "missing_information": [],
    "risk_level": "low"
  },
  "related_tickets": [
    {
      "key": "SUP-123",
      "score": 0.91,
      "reason": "same_version, lexical_overlap"
    }
  ],
  "suggested_reply": "",
  "internal_note": "",
  "confidence": 0.0
}
```

## 14. Risques a surveiller

- mauvaise classification client/support/systeme
- retrieval trompeur sur tickets seulement vaguement proches
- prompt trop libre
- absence de trace sur les sources utilisees
- confusion entre note interne et reponse publique

## 15. Definition de succes du POC

Le POC est reussi si:

- l'agent obtient une note interne pertinente en moins de quelques minutes
- les tickets relies sont majoritairement utiles
- le brouillon de reponse est exploitable sans reecriture complete
- aucune donnee ticket ne sort d'un perimetre interne

## 16. Prochaine etape concrete

Ordre recommande:

1. brancher Jira et le modele interne
2. valider `POST /analyze/{jira_key}` sur un ticket reel
3. ajouter la base et le `sync`
4. ameliorer la recherche historique
5. ajouter les profils de style
