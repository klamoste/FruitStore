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

The project also reads local settings from `fruit_store/.env` automatically. A local `.env` file is already ignored by git.

## Demo accounts

- Admin: `admin` / `admin123`
- Customer: `testuser` / `testuser123`

## Deployment notes

- Set `SECRET_KEY` in production.
- Set `DEBUG=False` in production.
- On Render, run `python manage.py create_sample_data` after `migrate` so a fresh deploy has catalog data immediately.
- For Vercel or any real deployment, prefer a hosted PostgreSQL database via `DATABASE_URL`.
- SQLite can work for local development and demo data, but it is not a good long-term production database for this app and is not suitable for Vercel's serverless filesystem.

## Vercel + Postgres

If you deploy this project on Vercel, do not rely on `db.sqlite3` for admin or order data.

1. Create a hosted PostgreSQL database.
2. In Vercel project settings, add these environment variables:
   - `SECRET_KEY`
   - `DEBUG=False`
   - `DATABASE_URL`
   - `ALLOWED_HOSTS=.vercel.app`
3. Redeploy the app.
4. Run migrations against the production database:

```bash
python fruit_store/manage.py migrate
python fruit_store/manage.py create_sample_data
```

If you want the admin dashboard to work on Vercel, `DATABASE_URL` must point to a writable PostgreSQL database.
