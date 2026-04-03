# 🔗 URL Shortener Service

A production-ready URL shortener built for the MLH Production Engineering Hackathon.

**Stack:** Flask · Peewee ORM · PostgreSQL · Nginx · Docker · GitHub Actions

## Architecture

```
                         ┌──────────┐
                         │  Nginx   │ :80
                         │  (LB)    │
                         └────┬─────┘
                        ┌─────┴─────┐
                   ┌────▼───┐  ┌────▼───┐
                   │  web1  │  │  web2  │  Flask :5000
                   └────┬───┘  └────┬───┘
                        └─────┬─────┘
                         ┌────▼─────┐
                         │PostgreSQL│ :5432
                         └──────────┘
```

Nginx load-balances across 2 Flask containers. All services orchestrated via Docker Compose.

## Quick Start

```bash
# 1. Clone & enter
git clone <repo-url> && cd <repo-name>

# 2. Start everything (Nginx + 2 app instances + Postgres)
docker compose up --build

# 3. Load CSV seed data
docker compose exec web1 uv run load_data.py

# 4. Verify (through Nginx on port 80)
curl http://localhost/health
# → {"status":"ok"}
```

### Running without Docker

```bash
uv sync
cp .env.example .env        # edit DB credentials if needed
createdb hackathon_db
uv run load_data.py
uv run run.py               # runs on port 5000
```

## API Endpoints

### Health

| Method | Endpoint  | Description          |
|--------|-----------|----------------------|
| GET    | `/health` | Returns `{"status":"ok"}` |

### Users

| Method | Endpoint        | Description                     |
|--------|-----------------|---------------------------------|
| GET    | `/users`        | List users (paginated)          |
| GET    | `/users/<id>`   | Get a single user               |

### URLs

| Method | Endpoint        | Description                     |
|--------|-----------------|---------------------------------|
| GET    | `/urls`         | List URLs (paginated)           |
| GET    | `/urls/<id>`    | Get a single URL                |
| POST   | `/urls`         | Create a short URL              |
| PUT    | `/urls/<id>`    | Update a URL                    |
| DELETE | `/urls/<id>`    | Delete a URL                    |
| GET    | `/<short_code>` | Redirect to original URL        |

#### POST /urls — Request Body

```json
{
  "user_id": 1,
  "original_url": "https://example.com/long-page",
  "title": "My Link"
}
```

#### PUT /urls/:id — Request Body (all fields optional)

```json
{
  "title": "New Title",
  "original_url": "https://example.com/updated",
  "is_active": false
}
```

### Events

| Method | Endpoint   | Description                     |
|--------|------------|---------------------------------|
| GET    | `/events`  | List events (paginated)         |

### Pagination

All list endpoints support `?page=1&per_page=20` (max 100 per page).

### Input Validation

- `original_url` must be a valid `http` or `https` URL
- `user_id` must reference an existing user
- Pagination params are clamped to safe bounds (page ≥ 1, 1 ≤ per_page ≤ 100)
- Malformed JSON bodies return 400

### Error Responses

All errors return JSON — never HTML stack traces:

```json
{"error": "User not found"}
```

| Status | Meaning                          |
|--------|----------------------------------|
| 400    | Bad request / validation error   |
| 404    | Resource not found               |
| 405    | Method not allowed               |
| 410    | URL is inactive (on redirect)    |
| 500    | Internal server error            |

## Environment Variables

| Variable          | Default        | Description          |
|-------------------|----------------|----------------------|
| `DATABASE_NAME`   | `hackathon_db` | PostgreSQL database  |
| `DATABASE_HOST`   | `localhost`    | Database host        |
| `DATABASE_PORT`   | `5432`         | Database port        |
| `DATABASE_USER`   | `postgres`     | Database user        |
| `DATABASE_PASSWORD`| `postgres`    | Database password    |
| `FLASK_DEBUG`     | `true`         | Debug mode           |

## Project Structure

```
├── app/
│   ├── __init__.py          # App factory, error handlers
│   ├── database.py          # DB proxy, BaseModel, connection hooks
│   ├── models/
│   │   ├── user.py          # User model
│   │   ├── url.py           # Url model
│   │   └── event.py         # Event model
│   └── routes/
│       ├── users.py         # /users endpoints
│       ├── urls.py          # /urls + /<short_code> endpoints
│       └── events.py        # /events endpoint
├── nginx/
│   └── nginx.conf           # Load balancer config
├── tests/                   # pytest test suite
├── .github/workflows/ci.yml # CI pipeline
├── Dockerfile
├── docker-compose.yml
├── load_data.py             # CSV seed data loader
└── run.py                   # Entry point
```

## Running Tests

```bash
uv run pytest -v                # run all tests
uv run pytest --cov=app -v      # with coverage report
```

Tests use an in-memory SQLite database — no Postgres required.

## CI/CD

GitHub Actions runs on every push and PR to `main`:
1. Installs dependencies with `uv sync`
2. Runs `pytest` — build fails if any test fails
3. Checks coverage threshold (≥50%) — build fails if below

See `.github/workflows/ci.yml`.

## Deployment Guide

### Deploy

```bash
# Build and start all services
docker compose up --build -d

# Load seed data (first deploy only)
docker compose exec web1 uv run load_data.py

# Verify
curl http://localhost/health
```

### Rollback

```bash
# Stop current deployment
docker compose down

# Checkout previous working commit
git checkout <previous-commit-sha>

# Rebuild and restart
docker compose up --build -d
```

### Scaling

The app runs 2 instances behind Nginx by default. To add more, duplicate the `web` service in `docker-compose.yml` and add it to `nginx/nginx.conf` upstream block.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` on port 5432 | Postgres isn't ready yet. Docker Compose healthcheck should handle this — wait a few seconds and retry. |
| `Connection refused` on port 80 | Nginx hasn't started. Check `docker compose logs nginx`. |
| `no such table` in tests | Tests use SQLite in-memory. Make sure conftest.py `setup_db` fixture is running. |
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| CSV load fails with duplicate key | Data already loaded. Drop and recreate: `docker compose exec web1 uv run -c "from app import create_app; from app.database import db; from app.models import *; app=create_app(); db.drop_tables([Event,Url,User]); db.create_tables([User,Url,Event])"` then re-run `load_data.py`. |
| App returns HTML errors instead of JSON | All error handlers return JSON. If you see HTML, check that the error handler in `app/__init__.py` is registered. |
