# Ai Support

POC Python pour analyser des tickets Jira TheHive, retrouver des cas similaires, proposer un brouillon de réponse et publier une note interne dans Jira.

## Objectif

Construire rapidement une boucle de travail privée:

1. synchroniser les tickets Jira récents ou mis à jour
2. stocker l'historique localement
3. rechercher des tickets similaires
4. générer une analyse structurée avec un LLM interne
5. publier une note interne Jira pour l'agent

## Contraintes prises en compte

- aucune donnée ticket ne sort vers un SaaS LLM
- modèle hébergé en interne uniquement
- publication limitée à une note interne Jira pour le POC
- architecture simple pour démarrer sur une machine interne ou AWS privé

## Stack de depart

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL
- APScheduler
- Jira REST API
- serveur LLM local compatible HTTP

## Structure

- `docs/PLAN_POC.md`: plan détaillé, architecture, roadmap 10 jours
- `src/app/main.py`: API FastAPI minimale
- `src/app/core/config.py`: configuration centralisée
- `src/app/api/routes_*.py`: endpoints internes
- `src/app/services/analyze_ticket.py`: workflow d'analyse
- `src/app/jira/client.py`: client Jira
- `src/app/llm/client.py`: client LLM interne
- `src/app/retrieval/ranker.py`: ranking de tickets similaires
- `src/app/workers/scheduler.py`: jobs périodiques

## Lancement rapide

1. Copier `.env.example` vers `.env`
2. Renseigner les accès Jira et la base
3. Installer les dépendances
4. Lancer l'API

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app.main:app --app-dir src --reload
```

## Configuration locale recommandee

Pour travailler avec un modele local, garde une configuration centree sur Ollama:

```env
LLM_PROVIDER=local
LLM_LOCAL_BACKEND=ollama
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=qwen2.5:14b-instruct
LLM_TIMEOUT_SECONDS=120
ENABLE_SCHEDULER=false
```

Et cote Ollama:

```bash
ollama serve
ollama pull qwen2.5:14b-instruct
curl http://localhost:11434/api/tags
```

Le code est pret pour d'autres providers plus tard. Pour l'instant:

- `local` utilise le backend local configure, aujourd'hui `ollama`
- `groq` reste disponible si tu veux revenir a une API distante

## Test en dry run

Le mode `dry_run` genere l'analyse et la note Jira preview sans rien enregistrer en base et sans rien publier dans Jira.

Pour tester uniquement les endpoints manuels sans jobs de fond:

```env
ENABLE_SCHEDULER=false
```

```bash
curl -X POST "http://127.0.0.1:8000/analyze/SUPPORT-123?dry_run=true"
```

Pour declencher l'analyse depuis un webhook entrant:

```bash
curl -X POST "http://127.0.0.1:8000/analyze/webhook/jira?dry_run=true" \
  -H "Content-Type: application/json" \
  -d '{"issue":{"key":"HELP-4000"}}'
```

Formats de payload supportes:

- `{"issue":{"key":"HELP-4000"}}`
- `{"issueKey":"HELP-4000"}`
- `{"jira_key":"HELP-4000"}`
- `{"ticket":{"key":"HELP-4000"}}`

Protection optionnelle:

```env
WEBHOOK_TOKEN=ton-secret
```

Puis:

```bash
curl -X POST "http://127.0.0.1:8000/analyze/webhook/jira?dry_run=true" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Token: ton-secret" \
  -d '{"issue":{"key":"HELP-4000"}}'
```

Pour lister rapidement des tickets Jira recents du projet configure et recuperer une vraie cle:

```bash
curl "http://127.0.0.1:8000/sync/recent?max_results=10"
```

Ou pour un projet explicite:

```bash
curl "http://127.0.0.1:8000/sync/recent?project_key=HELP&max_results=10"
```

Le retour contient notamment:

- `result`: le JSON du modele
- `internal_note`: le commentaire Jira qui serait envoye
- `published_to_jira`: toujours `false` en dry run

Si Jira ou le LLM local ne sont pas disponibles, l'API retourne maintenant une erreur JSON lisible avec `message` et `details`.

Pour activer le flux avec persistance locale:

```bash
curl -X POST "http://127.0.0.1:8000/analyze/SUPPORT-123?dry_run=false"
```

## Utiliser Groq a la place d'Ollama

Le client LLM supporte maintenant `ollama` et `groq`.

Configuration minimale:

```env
LLM_PROVIDER=groq
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_API_KEY=ta-cle-groq
LLM_MODEL=llama-3.3-70b-versatile
ENABLE_SCHEDULER=false
DEMO_AGENT_NAME=Gael
DEMO_AGENT_STYLE=Professional, calm, concise. Acknowledge the issue, explain the likely direction, ask only the missing data that matters, and give concrete next steps.
```

Test:

```bash
curl -X POST "http://127.0.0.1:8000/analyze/HELP-123?dry_run=true"
```

## Mode demo sans Jira

Pour montrer une analyse IA sans appel Jira, utilise les scenarios locaux.

Lister les scenarios:

```bash
curl "http://127.0.0.1:8000/analyze/demo"
```

Analyser le scenario TheHive OOM sur machine 16 GB:

```bash
curl -X POST "http://127.0.0.1:8000/analyze/demo/thehive-oom-16gb"
```

Vue presentation lisible:

```bash
curl "http://127.0.0.1:8000/analyze/demo/thehive-oom-16gb/report" | jq -r '.report.rendered_text'
```

Vue locale simple dans le navigateur:

```text
http://127.0.0.1:8000/demo-ui/
```

La reponse contient:

- `result.analysis.first_impression`
- `result.related_docs`
- `result.suggested_reply_fr`
- `result.suggested_reply_en`
- `internal_note`
- `logs`

## Charger l'historique Jira et reconstruire les styles agent

Backfill de l'historique local:

```bash
python scripts/backfill_jira_history.py --project HELP
```

Exemples utiles:

```bash
python scripts/backfill_jira_history.py --project HELP --max-issues 200
python scripts/backfill_jira_history.py --jql 'project = HELP AND created >= -180d ORDER BY created ASC'
```

Reconstruction des profils de style:

```bash
python scripts/rebuild_style_profiles.py
```

Ou pour une personne precise:

```bash
python scripts/rebuild_style_profiles.py --agent-name "Gael Rivaud" --min-messages 12
```

Verification recommandee:

1. lancer le backfill Jira
2. lancer le rebuild des profils
3. verifier les profils generes dans la sortie JSON du script
4. analyser un ticket assigne a cette personne pour confirmer que le ton et la structure evoluent dans le bon sens

Consultation des profils:

```bash
curl "http://127.0.0.1:8000/analyze/profiles" | jq
```

Vue locale:

```text
http://127.0.0.1:8000/demo-ui/profiles
```

## Priorite immediate

- brancher Jira search et issue details
- persister tickets et commentaires
- exposer `POST /sync` et `POST /analyze/{jira_key}`
- brancher un LLM local en JSON strict
- publier une note interne Jira
