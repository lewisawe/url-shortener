"""Load CSV data into the database. Run: uv run load_data.py"""

import csv

from peewee import chunked

from app import create_app
from app.database import db
from app.models import Event, Url, User

app = create_app()

with app.app_context():
    db.create_tables([User, Url, Event])

    # Users
    with open("users.csv", newline="") as f:
        users = list(csv.DictReader(f))
    with db.atomic():
        for batch in chunked(users, 100):
            User.insert_many(batch).execute()
    print(f"Loaded {len(users)} users")

    # URLs
    with open("urls.csv", newline="") as f:
        urls = list(csv.DictReader(f))
    for row in urls:
        row["is_active"] = row["is_active"] == "True"
    with db.atomic():
        for batch in chunked(urls, 100):
            Url.insert_many(batch).execute()
    print(f"Loaded {len(urls)} urls")

    # Events
    with open("events.csv", newline="") as f:
        events = list(csv.DictReader(f))
    for row in events:
        row["url"] = row.pop("url_id")
        row["user"] = row.pop("user_id")
    with db.atomic():
        for batch in chunked(events, 100):
            Event.insert_many(batch).execute()
    print(f"Loaded {len(events)} events")

    # Fix Postgres sequences after bulk insert with explicit IDs
    for table in ["user", "url", "event"]:
        db.execute_sql(
            f"SELECT setval('{table}_id_seq', (SELECT MAX(id) FROM \"{table}\"))"
        )
    print("Sequences synced")
