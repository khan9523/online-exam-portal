# Online Exam Portal

Simple Flask-based online exam system with admin and student workflows.

## Run Locally

1. Install dependencies:
	pip install -r requirements.txt
2. Start the app:
	python app.py
3. Open:
	http://127.0.0.1:10000/login

## Production Start Command (Render)

Use this start command in Render:

gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120

This same command is included in Procfile.

## Health Endpoint

The app exposes:

- /health -> returns {"status": "ok"}

## Automated Keep-Alive

This repository includes a GitHub Actions workflow at:

- .github/workflows/keep-alive.yml

It pings the Render health endpoint every 10 minutes to reduce cold starts.

To enable it:

1. Push the repository to GitHub.
2. Open the GitHub repository Actions tab.
3. Enable workflows if prompted.
4. Run Keep Render Service Awake once manually from workflow_dispatch.

## Manual Health Check Script

You can also test health manually:

python scripts/health_check.py