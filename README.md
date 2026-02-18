# Miniatures.lk ERP Backend

FastAPI backend for Miniatures.lk ERP.

This README is intentionally minimal and matches the current files in this repository.

## Prerequisites

- Docker Desktop (or Docker Engine) installed and running

## Basic Docker Run (Recommended)

Run these commands from the project root.

1. Build the backend image
   ```bash
   docker build -t miniatures-erp-backend:local .
   ```

2. Create a Docker network (once)
   ```bash
   docker network create miniatures-basic-net
   ```

3. Start PostgreSQL
   ```bash
   docker run -d \
     --name miniatures-db-local \
     --network miniatures-basic-net \
     -e POSTGRES_DB=miniatures_erp \
     -e POSTGRES_USER=postgres \
     -e POSTGRES_PASSWORD=postgres \
     postgres:15
   ```

4. Start the backend API
   ```bash
   docker run -d \
     --name miniatures-api-local \
     --network miniatures-basic-net \
     -p 8000:8000 \
     -e DATABASE_URL=postgresql://postgres:postgres@miniatures-db-local:5432/miniatures_erp \
     miniatures-erp-backend:local
   ```

5. Verify it is running
   ```bash
   curl http://localhost:8000/health
   ```
   Expected response:
   ```json
   {"status":"healthy","database":"connected","version":"1.0.0"}
   ```

6. Open API docs
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## Stop / Cleanup

Stop containers:

```bash
docker stop miniatures-api-local miniatures-db-local
```

Remove containers:

```bash
docker rm miniatures-api-local miniatures-db-local
```

Remove network (optional):

```bash
docker network rm miniatures-basic-net
```

## Useful Debug Commands

Backend logs:

```bash
docker logs -f miniatures-api-local
```

Database logs:

```bash
docker logs -f miniatures-db-local
```

## Optional: Run Without Docker

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/miniatures_erp
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
