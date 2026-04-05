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

Use profile-specific env files:

```powershell
# Development
Copy-Item .env.dev .env

# Production
Copy-Item .env.prod .env
```

`.env` stays untracked and is your active runtime file.
`.env.dev` and `.env.prod` are tracked templates for each environment.
`.env.example` is a neutral baseline template.

Update values in `.env` as needed, especially:

- DJANGO_SECRET_KEY
- DATABASE_URL
- AWS_STORAGE_BUCKET_NAME
- AWS_S3_REGION_NAME
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND

If AWS storage values are left blank, uploaded resumes are stored locally in the `resume/` folder.

## Resume Upload Security Flow (Pre-signed URL)

1. Frontend calls `POST /api/v1/resumes/upload-url` with filename and content type.
2. Backend signs a temporary S3 upload URL using IAM keys.
3. Frontend uploads the file directly to S3 using the pre-signed URL.
4. Frontend calls `POST /api/v1/resumes/register-upload` with `reference_no` and `s3_key`.
5. Backend stores the `s3_key` in DB and parsing can start with `POST /api/v1/resumes/{reference_no}/parse`.

If S3 is not configured, frontend automatically falls back to direct `POST /api/v1/resumes/upload` and files are saved under `resume/`.

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

## AI-Powered Candidate Evaluation (Google Gemini)

GetHired integrates Google's Gemini API for intelligent candidate assessment, deep resume analysis, and personalized career recommendations.

### Setup

1. Get your free Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add to `.env`:
   ```env
   GEMINI_API_KEY=YOUR_API_KEY_HERE
   GEMINI_ENABLED=True
   ```

### AI Endpoints

- `GET /api/v1/ai/status` - Check if Gemini is enabled
- `POST /api/v1/candidates/{reference_no}/ai-evaluation` - Score candidate for job role
- `GET /api/v1/candidates/{reference_no}/ai-analysis` - Deep resume analysis
- `POST /api/v1/candidates/{reference_no}/career-recommendations` - Learning path recommendations

See [GEMINI_SETUP.md](GEMINI_SETUP.md) for complete API documentation and examples.

## Frontend (Vercel) API Configuration

When deploying the frontend on Vercel, set this env var in the Vercel project:

- `VITE_API_URL=http://<YOUR_ORACLE_PUBLIC_IP>:8000`

The frontend auto-builds API paths under `/api/v1`, so only host and port are needed.

Important:

- If frontend runs on HTTPS and backend is HTTP, browsers block requests (mixed content).
- For production, expose backend over HTTPS (for example behind Cloudflare or a reverse proxy with TLS), then set:
   - `VITE_API_URL=https://api.yourdomain.com`

## Quick Health Checks

- Django server: open http://127.0.0.1:8000/admin/
- Redis reachable: worker starts without broker connection errors
- DB reachable: migrations complete without connection errors
- Gemini AI: run `curl http://127.0.0.1:8000/api/v1/ai/status`

## Common Issues

- Error: connection to server at localhost (127.0.0.1), port 5432 failed
	- PostgreSQL is not running, or DB credentials in .env are wrong.

- Error: Cannot connect to redis://localhost:6379/0
	- Redis is not running, or CELERY_BROKER_URL is wrong.

- Celery import/app error
	- Verify project path and that command is run from repository root.

