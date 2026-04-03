# Operations Documentation

## Failure Modes

| Component | Failure | Impact | Detection | Recovery |
|-----------|---------|--------|-----------|----------|
| Flask container crashes | One of 3 instances goes down | Nginx routes to remaining 2; slight latency increase | `docker compose ps` shows unhealthy | `restart: unless-stopped` auto-restarts within seconds |
| PostgreSQL down | All reads/writes fail | 500 errors on all data endpoints; `/health` still returns 200 | Error rate spike on `/metrics`; `docker compose logs db` | Postgres container auto-restarts; data persists on `pgdata` volume |
| Redis down | Cache misses, all requests hit DB | Higher latency but no errors — cache degrades gracefully | `redis-cli ping` fails; response times increase | Redis container auto-restarts; cache rebuilds on next requests |
| Nginx down | No traffic reaches the app | Complete outage on port 80 | `curl http://localhost/health` fails | `docker compose restart nginx` |
| Database full | Inserts fail | POST /urls returns 500 | Disk usage alerts; error logs | Increase volume size or clean old data |
| Short code collision | Rare — 62^6 = 56B combinations | Retry loop handles it (5 attempts) | Logged as IntegrityError | Automatic — retries with new code |

## Decision Log

| Decision | Choice | Why |
|----------|--------|-----|
| Web framework | Flask | Lightweight, well-documented, provided in template |
| ORM | Peewee | Simple, provided in template, good Postgres support |
| Database | PostgreSQL | ACID-compliant, handles concurrent writes, provided in template |
| Cache | Redis | In-memory key-value store, sub-ms reads, perfect for caching URL lookups |
| Load balancer | Nginx | Industry standard, simple config, handles keepalive connections |
| WSGI server | Gunicorn (gthread) | Production-grade, multi-worker + multi-thread for concurrency |
| Containerization | Docker Compose | Orchestrates all services, healthchecks, restart policies |
| CI | GitHub Actions | Free for public repos, runs pytest + coverage on every push |
| Testing | pytest + SQLite in-memory | Fast tests, no external dependencies, 95% coverage |

## Capacity Plan

### Current Setup
- 3 Flask containers × 8 workers × 4 threads = 96 concurrent handlers
- 1 PostgreSQL instance
- 1 Redis instance
- 1 Nginx load balancer

### Measured Performance (single machine)

| Users | p95 Latency | Error Rate | Requests Served |
|-------|-------------|------------|-----------------|
| 50    | 220ms       | 0%         | 1,061           |
| 200   | 1,500ms     | 0%         | 5,376           |
| 500   | 5,600ms     | 0.05%      | 6,490           |

### Bottleneck Analysis
The primary bottleneck at 500 users is **CPU contention** — all services (3 app containers, Postgres, Redis, Nginx) share one machine. Evidence:
- `/health` (no DB, no cache) has similar latency to DB-backed endpoints
- Redis-cached responses are not significantly faster than DB queries
- This confirms the bottleneck is not the database or cache, but the shared CPU

### Scaling Recommendations
1. **Separate hosts**: Move Postgres and Redis to dedicated machines — biggest win
2. **Add containers**: More web instances behind Nginx (just add to docker-compose + nginx.conf)
3. **Connection pooling**: Add PgBouncer between app and Postgres
4. **Read replicas**: Postgres read replicas for GET endpoints
5. **CDN**: Cache redirect responses at the edge

### Estimated Limits
- Current single-machine setup: ~200 concurrent users comfortably (<2s p95)
- With dedicated DB host: ~500-1000 concurrent users
- With read replicas + CDN: 5000+ concurrent users

## Runbook: Service Down

**Alert**: Health check failing / 502 errors

1. Check which service is down:
   ```bash
   docker compose ps
   ```

2. Check logs for the failing service:
   ```bash
   docker compose logs --tail=50 <service>
   ```

3. If a web container is down, it should auto-restart. If not:
   ```bash
   docker compose restart web1 web2 web3
   ```

4. If Postgres is down:
   ```bash
   docker compose restart db
   # Wait for healthcheck, then verify:
   docker compose exec web1 uv run python -c "from app import create_app; create_app()"
   ```

5. If Nginx is down:
   ```bash
   docker compose restart nginx
   curl http://localhost/health
   ```

## Runbook: High Error Rate

**Alert**: Error rate > 5% on `/metrics`

1. Check which endpoints are failing:
   ```bash
   curl http://localhost/metrics | python3 -m json.tool
   ```

2. Check application logs for stack traces:
   ```bash
   docker compose logs --tail=100 web1 web2 web3 | grep ERROR
   ```

3. Check database connectivity:
   ```bash
   docker compose exec db pg_isready -U postgres
   ```

4. Check Redis connectivity:
   ```bash
   docker compose exec redis redis-cli ping
   ```

5. If DB is overloaded, check active connections:
   ```bash
   docker compose exec db psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
   ```

6. If needed, restart all app containers:
   ```bash
   docker compose restart web1 web2 web3
   ```

## Runbook: High Latency

**Alert**: p95 response time > 3 seconds

1. Check if it's a cache issue:
   ```bash
   docker compose exec redis redis-cli info stats | grep hits
   ```

2. Check database slow queries:
   ```bash
   docker compose exec db psql -U postgres -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC LIMIT 5;"
   ```

3. Check container resource usage:
   ```bash
   docker stats --no-stream
   ```

4. If CPU is maxed, scale horizontally — add another web container to docker-compose.yml and nginx.conf upstream block.
