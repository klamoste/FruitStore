# Fruit Store

A Django fruit store demo with product browsing, cart and checkout flows, user profiles, and an admin dashboard.

## Run locally

From the project root:

```bash
python -m pip install -r requirements.txt
cd fruit_store
python manage.py migrate
python manage.py create_sample_data
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Demo accounts

- Admin: `admin` / `admin123`
- Customer: `testuser` / `testuser123`

## Deployment notes

- Set `SECRET_KEY` in production.
- Set `DEBUG=False` in production.
- On Render, run `python manage.py create_sample_data` after `migrate` so a fresh deploy has catalog data immediately.
- For Vercel or any real deployment, prefer a hosted PostgreSQL database via `DATABASE_URL`.
- SQLite can work for local development and demo data, but it is not a good long-term production database for this app and is not suitable for Vercel's serverless filesystem.
