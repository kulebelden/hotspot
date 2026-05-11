# Hotspot Billing Backend

This project is a simple Flask backend for a WiFi hotspot billing system.
It connects to a MySQL database and provides basic user login, payment simulation, session checks, and admin earnings stats.

## Files

- `app.py` - main Flask application
- `db.py` - database connection and table creation helpers
- `routes/auth.py` - login, pay, and status API endpoints
- `routes/admin.py` - admin statistics endpoint
- `requirements.txt` - Python dependencies
- `.env.example` - example environment variables for MySQL

## Install dependencies

1. Create a Python virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:

On Windows:
```powershell
your_project_path\venv\Scripts\Activate.ps1
```

3. Install packages:

```bash
python -m pip install -r requirements.txt
```

## Configure MySQL

1. Install MySQL Server if you do not already have it.
2. Create a database named `hotspot_db` or update `DB_DATABASE` in `.env`.
3. Copy `.env.example` to `.env` and set your MySQL credentials:

```text
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_DATABASE=hotspot_db
```

## Run the server

```bash
python app.py
```

Open the portal in your browser at `http://127.0.0.1:5000`.

The server listens on `http://127.0.0.1:5000` by default.

## API endpoints

- `POST /login`
  - JSON body: `{ "phone_number": "..." }` or `{ "voucher_code": "..." }`
  - Checks if the user has an active package.

- `POST /pay`
  - JSON body: `{ "phone_number": "...", "package_id": 1 }`
  - Simulates a mobile-money payment and activates a package.

- `POST /search-voucher`
  - JSON body: `{ "transaction_id": "..." }`
  - Searches for an active voucher by transaction ID and activates it if found.

- `GET /status`
  - Query string: `?phone_number=...` or `?voucher_code=...`
  - Returns whether the user currently has an active package.

- `GET /admin/stats`
  - Returns total earnings for daily, weekly, and monthly intervals.

## Notes for beginners

- The backend uses simple SQL queries and avoids complex frameworks.
- Table creation is handled automatically on first run.
- Sample vouchers are created automatically for testing: `TXN123456`, `TXN789012` (active), `TXN345678` (inactive).
- Package durations are stored in minutes and used to set a session expiry time.
- The payment flow is simulated: no real mobile-money API is integrated yet.
