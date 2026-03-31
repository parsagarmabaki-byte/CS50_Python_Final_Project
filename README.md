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

## Project Structure

```
final_project/
├── terminal_ui/              # Terminal/CLI application
│   ├── main.py               # CLI entry point
│   ├── login_management.py   # Authentication & account management
│   ├── user_menu.py          # User dashboard menu
│   ├── API_management.py     # Currency API functions
│   └── argparse_management.py # CLI argument parsing
├── web_ui/                   # Web application
│   ├── final_project/        # Backend Python package
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration & paths
│   │   ├── models.py         # Data classes
│   │   ├── repositories.py   # CSV data access layer
│   │   ├── services.py       # Business logic with bcrypt
│   │   ├── api_clients.py    # Frankfurter API client
│   │   ├── cli.py            # CLI adapter
│   │   └── web.py            # FastAPI web adapter
│   ├── tests/                # Web backend tests
│   └── web-client/           # React + TypeScript SPA
│       ├── src/
│       ├── package.json
│       └── README.md
├── csv_files/                # Shared data persistence
│   ├── Accounts.csv          # User credentials (bcrypt hashed)
│   └── account_directory/    # User-specific data
│       ├── username1/
│       │   ├── Watchlist.csv
│       │   └── Prices.csv
│       └── username2/
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

**Note:** The password is always entered via secure hidden input (not visible on screen), similar to standard Unix login prompts.

### Terminal UI Features

- 🔐 **Bcrypt Password Hashing** — Secure password storage
- 🔒 **Secure Input** — Passwords entered via hidden input (`getpass`)
- ✅ **Input Validation**:
  - Username: 3-24 characters (alphanumeric, underscore, space)
  - Password: 3-24 characters
  - Email: Validated using `email_validator` library
- 📁 **Auto Account Setup** — Automatic creation of user directories and CSV files
- 📊 **Watchlist Management** — Add/remove/view currency symbols
- 💹 **Live Prices** — Fetch exchange rates from Frankfurter API
- ⚙️ **Account Management** — Change email, password, or delete account

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

**Note:** The `password` field contains a bcrypt hash, not plain text.

### Per-User Watchlist (`csv_files/account_directory/username/Watchlist.csv`)

```csv
symbol
FX:USDSEK
FX:EURGBP
```

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
python main.py -u username -p password  # Direct login
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
