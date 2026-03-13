# MarketWatch — Currency Watchlist Manager

A Python application for tracking currency exchange rates using the [Frankfurter API](https://www.frankfurter.app/). Features both a legacy CLI interface and a new decoupled architecture with web API support.

## Project Structure

```
final_project/
├── final_project/          # New refactored package
│   ├── __init__.py
│   ├── config.py           # Configuration & paths
│   ├── models.py           # Data classes (Account, PriceRecord, WatchlistEntry)
│   ├── repositories.py     # CSV data access layer (Repository pattern)
│   ├── services.py         # Business logic (AccountService, WatchlistService)
│   ├── api_clients.py      # External API client (FrankfurterClient)
│   ├── cli.py              # CLI adapter
│   └── web.py              # FastAPI web adapter
├── tests/                  # Pytest tests for new architecture
│   ├── test_repositories.py
│   ├── test_services.py
│   └── test_web.py         # Web API integration tests
├── csv_files/              # Data persistence (CSV files)
├── login_management.py     # Legacy auth module
├── user_menu.py            # Legacy CLI dashboard
├── API_management.py       # Legacy API functions
├── requirements.txt        # Python dependencies
├── pyproject.toml          # Project configuration
└── README.md
```

## Architecture

The refactored code uses **dependency injection** and the **Repository pattern**:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   CLI/Web   │────▶│   Services   │────▶│  Repositories   │
│  Adapters   │     │ (Business    │     │ (CSV Access)    │
│             │     │   Logic)     │     │                 │
└─────────────┘     └──────────────┘     └─────────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ API Clients  │
                    │ (Frankfurter)│
                    └──────────────┘
```

### Key Design Principles

- **No prints/input** in core modules (`models.py`, `repositories.py`, `services.py`, `api_clients.py`)
- **Dependency injection**: Services accept repository and client objects
- **CSV schema backward-compatible**: Header `username,password,email,date`
- **Testable**: Repositories hide CSV access behind interfaces

## Installation

### Requirements

- Python 3.10+

### Install Dependencies

```bash
pip install -r requirements.txt
```

Dependencies include:
- `requests` — HTTP client for Frankfurter API
- `fastapi` + `uvicorn` — Web API
- `pydantic` — Data validation
- `pytest` — Testing

## Running the New Refactored Code

### CLI (Command Line Interface)

The new CLI supports demo commands for non-interactive usage:

```bash
# Register a new user
python -m final_project.cli --demo-register alice password123 alice@example.com

# Add a currency symbol (requires network for Frankfurter API)
python -m final_project.cli --demo-add-symbol alice USD SEK
```

### Web API (FastAPI)

Start the web server:

```bash
uvicorn final_project.web:app --reload --port 8000
```

#### Authentication

The web API uses simple token-based authentication (demo purposes):

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

#### API Endpoints

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

#### Example Requests

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

## Testing

### Run All Tests

```bash
pytest -v
```

### Test Files

| File                      | Description                          |
|---------------------------|--------------------------------------|
| `tests/test_repositories.py` | CSV repository CRUD operations    |
| `tests/test_services.py`     | Service layer with mocked API     |
| `tests/test_web.py`          | Web API integration tests         |

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

```csv
username,password,email,date
alice,password123,alice@example.com,2026-03-13
```

### Per-User Watchlist (`{username}_watchlist.csv`)

```csv
symbol
FX:USDSEK
FX:EURGBP
```

### Per-User Prices (`{username}_prices.csv`)

```csv
symbol,price,date,source
FX:USDSEK,10.5,2026-03-13,Frankfurter
```

## Development

### Code Style

The project uses standard Python formatting:

```bash
# Format code
black final_project/ tests/

# Sort imports
isort final_project/ tests/

# Type checking (optional)
mypy final_project/
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
from final_project.api_clients import FrankfurterClient

client = FrankfurterClient()

# Get latest exchange rate
response = client.latest("USD", "SEK")
# Returns: {"base": "USD", "date": "2026-03-13", "rates": {"SEK": 10.5}}

# Get historical rates
response = client.range("2026-01-01", "2026-03-13", "USD", "SEK")
```

### Services

```python
from final_project.services import AccountService, WatchlistService
from final_project.repositories import CSVAccountRepository, CSVWatchlistRepository, CSVPricesRepository
from final_project.api_clients import FrankfurterClient

# Setup
account_repo = CSVAccountRepository()
watchlist_repo = CSVWatchlistRepository()
prices_repo = CSVPricesRepository()
api_client = FrankfurterClient()

account_service = AccountService(account_repo)
watchlist_service = WatchlistService(watchlist_repo, prices_repo, api_client)

# Register user
account = account_service.register("alice", "password123", "alice@example.com")

# Add currency symbol
price_record = watchlist_service.add_symbol("alice", "USD", "SEK")
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
