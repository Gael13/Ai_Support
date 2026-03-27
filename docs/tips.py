
source .venv/bin/activate
uvicorn app.main:app --app-dir src --reload

Pour éviter les jobs automatiques pendant les tests :
dans .env

ENABLE_SCHEDULER=false

Pour analyser un vrai ticket Jira en dry run :

curl -X POST "http://127.0.0.1:8000/analyze/HELP-4000?dry_run=true" | jq


Pour lister des tickets récents Jira :

curl "http://127.0.0.1:8000/sync/recent?project_key=HELP&max_results=10" | jq
Pour tester sans Jira avec les faux tickets :

curl "http://127.0.0.1:8000/analyze/demo" | jq
curl -X POST "http://127.0.0.1:8000/analyze/demo/thehive-oom-16gb" | jq
Pour voir un rapport lisible en texte :

curl "http://127.0.0.1:8000/analyze/demo/thehive-oom-16gb/report" | jq -r '.report.rendered_text'

