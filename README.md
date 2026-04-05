# GetHired Backend

Backend service for the AI Talent and Career Ecosystem, built with Django, DRF, PostgreSQL, Redis, and Celery.

## Prerequisites

- Python 3.14+ (matches current project config)
- uv installed
- PostgreSQL running locally
- Redis running locally

## 1. Install Dependencies (uv)

From the project root:

```powershell
uv sync
```

If you prefer pip for local testing:

```powershell
pip install -r requirements.txt
```

## 2. Configure Environment Variables

Create your local environment file from the example:

```powershell
Copy-Item .env.example .env
```

Update values in .env as needed, especially:

- DJANGO_SECRET_KEY
- DB_NAME
- DB_USER
- DB_PASSWORD
- DB_HOST
- DB_PORT
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND

## 3. Start PostgreSQL and Redis

Make sure both services are running before starting Django/Celery.

Example with Docker (optional):

```powershell
docker run -d --name gethired-postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=gethired -p 5432:5432 postgres:16
docker run -d --name gethired-redis -p 6379:6379 redis:7
```

## 4. Run Database Migrations

```powershell
py .\manage.py makemigrations
py .\manage.py migrate
```

If using pgvector, enable extension in PostgreSQL:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## 5. Run Django Development Server

```powershell
py .\manage.py runserver
```

Server default URL:

- http://127.0.0.1:8000/

## 6. Run Celery Worker

Open a second terminal in the project root and run:

```powershell
celery -A GetHired worker -l info
```

Optional: run Celery Beat in a third terminal if scheduled tasks are needed:

```powershell
celery -A GetHired beat -l info
```

## Recommended Startup Order

1. PostgreSQL
2. Redis
3. Django migrations
4. Django runserver
5. Celery worker
6. Celery beat (optional)

## Quick Health Checks

- Django server: open http://127.0.0.1:8000/admin/
- Redis reachable: worker starts without broker connection errors
- DB reachable: migrations complete without connection errors

## Common Issues

- Error: connection to server at localhost (127.0.0.1), port 5432 failed
	- PostgreSQL is not running, or DB credentials in .env are wrong.

- Error: Cannot connect to redis://localhost:6379/0
	- Redis is not running, or CELERY_BROKER_URL is wrong.

- Celery import/app error
	- Verify project path and that command is run from repository root.

