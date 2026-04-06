# MarketWatch — Currency Watchlist Manager

A Python application for tracking currency exchange rates using the [Frankfurter API](https://www.frankfurter.app/). Features a **Terminal UI (CLI)**, a **Modern FastAPI Web Backend**, and a **React + TypeScript SPA Frontend**.

## Features

- 🔐 **Bcrypt Password Hashing** — Secure password storage for both Terminal and Web UI
- 📁 **Shared Data Structure** — Both UIs use the same account files and user directories
- 💻 **Terminal UI** — Classic CLI interface with interactive menus
- 🌐 **Web API** — RESTful FastAPI backend with token authentication
- ⚛️ **React Frontend** — Modern SPA with TypeScript and Tailwind CSS
- 📊 **Currency Tracking** — Watchlist management and price history
- 🧪 **Testable Architecture** — Repository pattern with dependency injection

## Demo Videos

- `Watchlist_Terminal_Demo.mp4` — Terminal UI walkthrough
- `Watchlist_WebUI_Demo.mp4` — Web UI (React SPA + FastAPI) walkthrough

## Project Structure

```
final_project/
├── terminal_ui/              # Terminal/CLI application
│   ├── main.py               # CLI entry point
│   ├── login_management.py   # Authentication & account management
│   ├── user_menu.py          # User dashboard menu
│   ├── API_management.py     # Currency API functions
│   ├── argparse_management.py # CLI argument parsing
│   ├── test_API_management.py # Tests for API module
│   ├── test_login_management.py # Tests for login module
│   └── test_usermenu.py      # Tests for user menu
├── web_ui/                   # Web application
│   ├── final_project/        # Backend Python package
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration & paths
│   │   ├── models.py         # Data classes
│   │   ├── repositories.py   # CSV data access layer
│   │   ├── services.py       # Business logic with bcrypt
│   │   ├── api_clients.py    # Frankfurter API client
│   │   ├── cli.py            # CLI adapter with demo flags
│   │   ├── main.py           # Interactive menu-driven CLI launcher
│   │   └── web.py            # FastAPI web adapter
│   ├── tests/                # Web backend tests
│   ├── web-client/           # React + TypeScript SPA
│   │   ├── src/
│   │   ├── public/
│   │   ├── index.html
│   │   ├── vite.config.ts
│   │   ├── tailwind.config.cjs
│   │   ├── tsconfig.json
│   │   ├── Dockerfile / Dockerfile.dev
│   │   ├── nginx.conf
│   │   └── ... (standard React tooling)
│   ├── Dockerfile            # Backend Docker image
│   ├── docker-compose.yml    # Production Docker compose
│   ├── docker-compose.dev.yml # Development Docker compose
│   ├── .env.docker           # Docker environment template
│   ├── DEPLOYMENT_OPTIONS.md # Deployment comparison guide
│   ├── DOCKER_COMPOSE_DEPLOYMENT.md # Docker deployment guide
│   └── UBUNTU_SERVER_CONFIG.md # Manual Ubuntu deployment guide
├── csv_files/                # Shared data persistence
│   ├── Accounts.csv          # User credentials (bcrypt hashed)
│   └── account_directory/    # User-specific data
│       ├── username/
│       │   ├── Watchlist.csv
│       │   └── Prices.csv
│       └── ...
├── Watchlist_Terminal_Demo.mp4  # Terminal UI demo video
├── Watchlist_WebUI_Demo.mp4     # Web UI demo video
├── tests.py                  # Unit tests
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
└── README.md
```

## Architecture

The application uses **dependency injection** and the **Repository pattern** for clean separation of concerns:

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Terminal / Web  │────▶│   Services   │────▶│  Repositories   │
│   Interfaces    │     │ (Business    │     │ (CSV Access)    │
│                 │     │   Logic)     │     │                 │
└─────────────────┘     └──────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────┐
                        │ API Clients  │
                        │ (Frankfurter)│
                        └──────────────┘
```

### Key Design Principles

- **No prints/input** in core modules (models, repositories, services, api_clients)
- **Dependency injection**: Services accept repository and client objects
- **Bcrypt password hashing**: Secure password storage in both UIs
- **Shared CSV schema**: `username,password,email,date` (password is bcrypt hash)
- **Testable**: Repositories hide CSV access behind interfaces
- **Cross-UI compatibility**: Terminal and Web UI share the same data files

## Installation

### Requirements

- Python 3.10+
- Node.js 18+ (for React frontend)

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies include:**
- `requests` — HTTP client for Frankfurter API
- `bcrypt` — Password hashing
- `email-validator` — Email validation
- `fastapi` + `uvicorn` — Web API
- `pydantic` — Data validation
- `pytest` — Testing

### Install via pyproject.toml (Recommended)

The project defines optional dev dependencies for linting and type checking:

```bash
pip install -e ".[dev]"
```

This installs all runtime dependencies plus `black`, `isort`, and `mypy` for development.

### CLI Entry Points

After installing via `pyproject.toml`, two CLI entry points are available:

```bash
marketwatch-cli    # Launches terminal_ui/main.py
marketwatch-web    # FastAPI web app (use with uvicorn: uvicorn marketwatch-web:app)
```

## Running the Terminal UI (CLI)

### Interactive Mode

Run the full interactive dashboard:

```bash
cd terminal_ui
python main.py
```

The Terminal UI provides:
- 🔐 Login/Register with bcrypt password security
- 📋 Watchlist management (add/remove/view symbols)
- 💹 Price updates from Frankfurter API
- ⚙️ Account management (change email, password, delete account)

### Command-Line Arguments

Login with username (password prompted securely via hidden input):

```bash
python terminal_ui/main.py -u username
```

**Note:** The password is always entered via secure hidden input (not visible on screen), similar to standard Unix login prompts. There is no `-p/--password` flag — this is intentional to prevent passwords from appearing in shell history.

### Terminal UI Features

- 🔐 **Bcrypt Password Hashing** — Secure password storage
- 🔒 **Secure Input** — Passwords entered via hidden input (`getpass`)
- ✅ **Input Validation**:
  - Username: 3-24 characters (alphanumeric, underscore, space)
  - Password: 3-24 characters
  - Email: Validated using `email_validator` library
- 📁 **Auto Account Setup** — Automatic creation of user directories and CSV files
- 📊 **Watchlist Management** — Add/remove/view currency symbols
  - View entire watchlist
  - Add individual symbols
  - Remove symbols from watchlist
- 💹 **Live Prices** — Fetch exchange rates from Frankfurter API
  - Update all watchlist symbols at once
  - Update individual symbols
  - View prices for date ranges
  - Show all watchlist prices
- ⚙️ **Account Management** — Change email, password, or delete account
  - Show account info
  - Change email
  - Change password
  - Delete account
- 🌐 **Web Server Launch** — Start the FastAPI web server directly from the terminal menu

## Running the Web API (FastAPI)

Start the web server:

```bash
cd web_ui
uvicorn final_project.web:app --reload --port 8000
```

### Authentication

The web API uses simple token-based authentication:

1. **Login** to get a token:
   ```bash
   curl -X POST http://127.0.0.1:8000/login \
     -H "Content-Type: application/json" \
     -d '{"username":"testuser","password":"secret"}'
   ```
   Response: `{"token": "uuid-here"}`

2. **Use the token** in subsequent requests:
   ```bash
   curl -X GET http://127.0.0.1:8000/me/watchlist \
     -H "Authorization: Bearer <your-token>"
   ```
   Or use the `X-Auth-Token` header as an alternative.

### API Endpoints

| Method | Endpoint                  | Auth  | Description                    |
|--------|---------------------------|-------|--------------------------------|
| GET    | `/health`                 | No    | Health check                   |
| POST   | `/register`               | No    | Register a new user            |
| POST   | `/login`                  | No    | Login → returns auth token     |
| POST   | `/logout`                 | Yes   | Logout (invalidate token)      |
| GET    | `/me/watchlist`           | Yes   | List user's watchlist          |
| POST   | `/me/watchlist`           | Yes   | Add currency symbol            |
| DELETE | `/me/watchlist/{symbol}`  | Yes   | Remove symbol from watchlist   |
| GET    | `/me/prices`              | Yes   | Get latest prices              |
| POST   | `/me/prices/update`       | Yes   | Refresh all watchlist prices   |
| GET    | `/me/prices/export`       | Yes   | Download prices as CSV         |
| POST   | `/me/prices/historical`   | Yes   | Fetch historical exchange rates |
| DELETE | `/me/account`             | Yes   | Delete account (password + confirmation) |

**Interactive API docs:** FastAPI provides auto-generated Swagger UI at `http://127.0.0.1:8000/docs` and ReDoc at `http://127.0.0.1:8000/redoc`.

### Example Requests

**Register a user:**
```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"secret","email":"test@example.com"}'
```

**Add a currency symbol:**
```bash
curl -X POST http://127.0.0.1:8000/me/watchlist \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"base":"USD","quote":"SEK"}'
```
Response: `{"symbol":"FX:USDSEK","price":10.5,"date":"2026-03-13","source":"Frankfurter"}`

**Export prices as CSV:**
```bash
curl -X GET http://127.0.0.1:8000/me/prices/export \
  -H "Authorization: Bearer <your-token>" \
  -o prices.csv
```

**Fetch historical prices:**
```bash
curl -X POST http://127.0.0.1:8000/me/prices/historical \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"base":"USD","quote":"SEK","start_date":"2026-01-01","end_date":"2026-03-30"}'
```
Response: `[{"date":"2026-01-01","price":10.45},{"date":"2026-01-02","price":10.48},...]`

**Delete account:**
```bash
curl -X DELETE http://127.0.0.1:8000/me/account \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{"password":"secret","confirmation":"DELETE"}'
```
Response: `{"ok": true}`

## Running the Interactive CLI Launcher

The `web_ui/final_project/main.py` module provides a full interactive menu-driven CLI with 12 options:

```bash
cd web_ui
python -m final_project.main
```

**Menu options include:**
1. Register new user
2. Login / Logout
3. View / Add / Remove watchlist symbols
4. View latest prices
5. Update all prices
6. Export prices to CSV
7. Start web server (uvicorn)
8. Health check
9. Quit

### CLI Demo Flags

For scripting/testing, the launcher supports demo flags:

```bash
# Register a demo user
python -m final_project.main --demo-register testuser password123 test@example.com

# Add a symbol for an existing user
python -m final_project.main --demo-add-symbol testuser USD SEK

# Run demo flags without entering interactive menu
python -m final_project.main --demo-register testuser password123 test@example.com --no-menu
```

## Running the Legacy CLI

The original interactive CLI is still available:

```bash
python main.py
```

This runs the full dashboard with:
- Watchlist management (add/remove/view symbols)
- Price updates from Frankfurter API
- Account management (change email, password, delete account)

## React Frontend (SPA)

A modern single-page application built with React, TypeScript, and Tailwind CSS.

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
cd web_ui/web-client
npm install
```

### Configuration

Create `.env` file in `web_ui/web-client/`:

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

### Development

```bash
cd web_ui/web-client
npm run dev
```

The app will be available at `http://localhost:5173`.

### Features

- **Register/Login** — Token-based authentication
- **Dashboard** — View and manage watchlist
- **Add/Remove Symbols** — Track currency pairs (e.g., USD/SEK)
- **Update Prices** — Fetch latest rates from Frankfurter API
- **Export CSV** — Download price data

### Build for Production

```bash
npm run build
```

Output is in `web_ui/web-client/dist/`. Deploy to any static host or serve from FastAPI.

See `web_ui/web-client/README.md` for full documentation.

## Docker Deployment

The project includes Docker configuration for production and development deployment:

```bash
cd web_ui

# Production deployment
docker-compose up -d

# Development deployment (with hot reload)
docker-compose -f docker-compose.dev.yml up -d
```

**Deployment guides:**
- `DOCKER_COMPOSE_DEPLOYMENT.md` — Full Docker Compose setup guide
- `DEPLOYMENT_OPTIONS.md` — Comparison of deployment strategies
- `UBUNTU_SERVER_CONFIG.md` — Manual Ubuntu server setup with systemd + Nginx

**Environment variables:** Copy `.env.docker` to `.env` and configure `SERVER_IP`, `FRONTEND_PORT`, and `BACKEND_PORT`.

**CORS configuration:** The web API in `web.py` includes CORS origins for localhost and example private IPs. Update the `allow_origins` list with your server's IP or domain when deploying.

## Testing

### Run All Tests

```bash
pytest -v
```

Or run the simple test runner:

```bash
python tests.py
```

### Test Files

| File                      | Description                          |
|---------------------------|--------------------------------------|
| `tests.py`                | Unit tests for core functionality    |
| `web_ui/tests/test_repositories.py` | CSV repository CRUD operations    |
| `web_ui/tests/test_services.py`     | Service layer with mocked API     |
| `web_ui/tests/test_web.py`          | Web API integration tests         |

**Web tests cover:**
- Full register → login → add symbol → watchlist → prices → export → logout flow
- Symbol removal from watchlist
- Authentication errors (missing/invalid tokens)
- Invalid input validation (bad currency codes)

### Test Example

The tests use `tmp_path` fixture for isolated CSV file testing:

```python
def test_csv_account_repo(tmp_path: Path):
    p = tmp_path / "Accounts.csv"
    repo = CSVAccountRepository(p)
    assert repo.list_accounts() == []
    acc = Account("alice", "pw", "a@x.com", "2025-01-01")
    repo.add_account(acc)
    found = repo.find("alice")
    assert found is not None and found.username == "alice"
```

## CSV File Schema

### Accounts.csv

Located at `csv_files/Accounts.csv` (shared by both UIs):

```csv
username,password,email,date
alice,$2b$12$KIXx...hashed...,alice@example.com,2026-03-30
```

**Note:** The `password` field contains a bcrypt hash, not plain text. The `date` field format differs between UIs: the Terminal UI writes locale-dependent short dates (e.g., `04/04/26` via `%x`), while the Web UI writes ISO format (`YYYY-MM-DD`). This is a known inconsistency.

### Per-User Watchlist (`csv_files/account_directory/username/Watchlist.csv`)

```csv
symbol
FX:USDSEK
FX:EURGBP
```

**Note:** The Terminal UI uses `Stocks` as the column header in Watchlist.csv, while the Web UI uses `symbol`. Both UIs can read each other's files, but this schema difference is a known inconsistency.

### Per-User Prices (`csv_files/account_directory/username/Prices.csv`)

```csv
symbol,price,date,source
FX:USDSEK,10.5,2026-03-30,Frankfurter
```

### Shared Data Structure

Both Terminal UI and Web UI share the same data files:

```
csv_files/
├── Accounts.csv              # Shared account credentials
└── account_directory/
    ├── alice/
    │   ├── Watchlist.csv     # Shared watchlist
    │   └── Prices.csv        # Shared price records
    └── bob/
        ├── Watchlist.csv
        └── Prices.csv
```

This means:
- ✅ Register a user in Terminal UI → Login in Web UI
- ✅ Add symbol in Web UI → View in Terminal UI
- ✅ Passwords are securely hashed with bcrypt in both UIs

## Development

### Code Style

The project uses standard Python formatting:

```bash
# Format code
black terminal_ui/ web_ui/final_project/ tests/

# Sort imports
isort terminal_ui/ web_ui/final_project/ tests/

# Type checking (optional)
mypy web_ui/final_project/
```

### Pre-commit Hooks (Recommended)

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.0.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
```

## API Reference

### FrankfurterClient

```python
from web_ui.final_project.api_clients import FrankfurterClient

client = FrankfurterClient()

# Get latest exchange rate
response = client.latest("USD", "SEK")
# Returns: {"base": "USD", "date": "2026-03-30", "rates": {"SEK": 10.5}}

# Get historical rates
response = client.range("2026-01-01", "2026-03-30", "USD", "SEK")
```

### Services (Web UI)

```python
from web_ui.final_project.services import AccountService, WatchlistService
from web_ui.final_project.repositories import (
    CSVAccountRepository,
    CSVWatchlistRepository,
    CSVPricesRepository
)
from web_ui.final_project.api_clients import FrankfurterClient

# Setup
account_repo = CSVAccountRepository()
watchlist_repo = CSVWatchlistRepository()
prices_repo = CSVPricesRepository()
api_client = FrankfurterClient()

account_service = AccountService(account_repo)
watchlist_service = WatchlistService(watchlist_repo, prices_repo, api_client)

# Register user (password will be hashed with bcrypt)
account = account_service.register("alice", "password123", "alice@example.com")

# Authenticate user
is_valid = account_service.authenticate("alice", "password123")

# Add currency symbol
price_record = watchlist_service.add_symbol("alice", "USD", "SEK")
```

### Terminal UI Modules

```python
from terminal_ui.login_management import (
    hash_password,
    check_user_password,
    Account,
    accounts_path,
    account_files_path
)

# Hash a password
hashed = hash_password("mypassword")

# Verify password
is_valid = check_user_password(hashed, "mypassword")

# Create account directory
acc = Account("username", hashed, "email@example.com")

# Get path to user's files
user_dir = account_files_path("username")
# Returns: Path to csv_files/account_directory/username/
```

### Web API Pydantic Schemas

**Request/Response models:**

```python
# POST /register
class RegisterIn(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

# POST /login
class LoginIn(BaseModel):
    username: str
    password: str

# POST /login response
class TokenOut(BaseModel):
    token: str

# POST /me/watchlist
class AddSymbolIn(BaseModel):
    base: str    # e.g., "USD"
    quote: str   # e.g., "SEK"

# GET /me/watchlist response
class WatchlistOut(BaseModel):
    symbol: str  # e.g., "FX:USDSEK"

# GET /me/prices response
class PriceOut(BaseModel):
    symbol: str
    price: float
    date: str
    source: str
```

## License

MIT License

---

## Quick Start Summary

### Terminal UI
```bash
cd terminal_ui
python main.py  # Interactive menu
# or
python main.py -u username  # Login (password prompted securely)
```

### Web API
```bash
cd web_ui
uvicorn final_project.web:app --reload --port 8000
```

### React Frontend
```bash
cd web_ui/web-client
npm install
npm run dev
```

### Shared Data
Both UIs share the same data files in `csv_files/`:
- `Accounts.csv` - User credentials (bcrypt hashed)
- `account_directory/username/` - User-specific watchlists and prices
