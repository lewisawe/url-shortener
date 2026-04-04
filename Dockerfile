FROM python:3.13-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml .python-version ./
RUN uv sync

COPY . .

EXPOSE 5000

CMD ["uv", "run", "gunicorn", "-w", "8", "--threads", "4", "-b", "0.0.0.0:5000", "run:app"]
