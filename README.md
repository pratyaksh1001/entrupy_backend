# Entrupy API (Backend)

REST API built with **FastAPI** over **SQLite**. It handles user authentication, product search and detail views, usage limits, and admin operations.

## Requirements

- Python 3.10+
- Dependencies: FastAPI, Uvicorn (ASGI server), `python-dotenv`, `bcrypt`, `PyJWT`, `cachetools`, and SQLite (stdlib).

Run the app (from this directory):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Ensure `db.sqlite3` exists and tables are created (see **Database schema**). The companion script `data_ingestion.py` can create tables and seed sample data when used as intended in this project.

## Environment variables

| Variable | Purpose |
|----------|---------|
| `FRONT_END` | Included in the CORS `allow_origins` list for the web client. Set in `.env` for local or staging; production may also list fixed origins in `main.py` (ensure `Origin` values match exactly—browsers do not send a trailing slash on origins). |

Load a `.env` file in the same directory as `main.py` (`python-dotenv` is used in `main.py`).

## Database schema

SQLite file: `db.sqlite3`. Tables are defined in `data_ingestion.py` (and created with `IF NOT EXISTS`).

| Table | Description |
|-------|-------------|
| **user** | `email` (PK), `password` (bcrypt hash), `user_name`, `age`, `user_created_at`, `request_limit` — per-user API quota. |
| **user_logs** | `email`, `used_at`, `api_tokens` — usage events (e.g. login, product search cost). |
| **product** | `pID` (PK), `product`, `price`, `last_updated`, `brand`, `category`, `url`. |
| **prod_img** | `pID`, `url` — image URLs per product. |
| **prod_price** | `pID`, `updated_price`, `updated_at`, `changed_by` — price history. |
| **admin** | `email` (PK), `password` (hash), `user_name`. |

## Design choices

- **SQLite** keeps deployment simple for a single-node API; file path is relative to the process working directory.
- **Passwords** are stored with **bcrypt**; not plain text.
- **Sessions** use **JWT** strings returned at login. Valid tokens are also kept in an in-memory **TTL cache** (`cachetools`) for quick validation and to attach per-request state (e.g. remaining token budget). Restarting the process clears this cache; clients must sign in again.
- **Usage limits**: `request_limit` on `user` is mirrored into the cache as `remaining_tokens`. Search and product-detail calls deduct tokens in application logic.
- **CORS** is enabled so a separate frontend origin (e.g. local dev or Vercel) can call the API; configure origins via environment variables.

## API endpoints

All paths below are relative to the server root. Unless noted, the body is **JSON** (`Content-Type: application/json`).

### Health / root

| Method | Path | Body | Response |
|--------|------|------|----------|
| `GET` | `/` | — | `{ "message": "Hello World" }` |

### User auth

| Method | Path | Body | Notes |
|--------|------|------|------|
| `POST` | `/register` | `email`, `password`, `name`, `age` | Creates a user; `request_limit` is set server-side. |
| `POST` | `/login` | `email`, `password` | Returns `token`, `user_name`, `success`, `message`. On success, writes a row to `user_logs`. |
| `POST` | `/auth` | `token` | Validates token against in-memory cache; returns cached user payload or `success: false`. |

### Products (authenticated)

| Method | Path | Body | Notes |
|--------|------|------|------|
| `POST` | `/product_list` | `query`, `token` | Search products by substring on `product`; costs tokens; returns a list of product summaries. |
| `POST` | `/product/{pID}` | `token` | Full product row, images, and price history; costs tokens. |

### Admin

| Method | Path | Body | Notes |
|--------|------|------|------|
| `POST` | `/admin_login` | `email`, `password` | Admin JWT + cache entry with `role: "admin"`. |
| `POST` | `/admin_auth` | `token` | Returns success if token is an admin session. |
| `GET` | `/tables` | — | Lists table names exposed for admin browsing. |
| `POST` | `/admin/search` | `token`, `query`, `column`, `table` | SQL `LIKE` search (admin). |
| `POST` | `/admin/update` | `token`, `table`, `column`, `value`, `pID` | Updates a row; if `column` is `price`, appends to `prod_price`. |

### Generic table read (authenticated)

| Method | Path | Body | Notes |
|--------|------|------|------|
| `POST` | `/{table}` | `token` | Returns up to 10 rows and column names for `{table}`. Intended for admin tooling; route is generic—use only with trusted clients. |

**Note:** Dynamic routes such as `POST /{table}` are ordered after fixed paths in `main.py` so names like `register` or `login` are not captured as table names.

## Error and success shapes

Responses are mostly ad hoc dictionaries: `success`, `message`, `data`, or `error` fields depending on the handler. Clients should check HTTP status and the JSON `success` flag where present.
