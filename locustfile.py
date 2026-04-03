"""
Locust load test for the URL Shortener.

Usage:
  # Bronze: 50 concurrent users
  uv run locust -f locustfile.py --headless -u 50 -r 10 -t 30s --host http://localhost

  # Silver: 200 concurrent users
  uv run locust -f locustfile.py --headless -u 200 -r 20 -t 60s --host http://localhost

  # Gold: 500 concurrent users
  uv run locust -f locustfile.py --headless -u 500 -r 50 -t 60s --host http://localhost

  # With web UI (opens http://localhost:8089)
  uv run locust -f locustfile.py --host http://localhost
"""

from locust import HttpUser, between, task


class URLShortenerUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(5)
    def health(self):
        self.client.get("/health")

    @task(10)
    def list_urls(self):
        self.client.get("/urls?page=1&per_page=20")

    @task(5)
    def list_users(self):
        self.client.get("/users?page=1&per_page=20")

    @task(3)
    def list_events(self):
        self.client.get("/events?page=1&per_page=20")

    @task(3)
    def get_single_url(self):
        self.client.get("/urls/1")

    @task(3)
    def get_single_user(self):
        self.client.get("/users/1")

    @task(2)
    def create_url(self):
        self.client.post("/urls", json={
            "user_id": 1,
            "original_url": "https://example.com/load-test",
            "title": "Load Test",
        })
