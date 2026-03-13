# final_project/services.py
"""Business logic services for the final project application.

This module provides service classes that encapsulate the core business logic
for account management and watchlist operations.
"""
import re
from datetime import datetime, timezone
from typing import List
from .models import Account, PriceRecord, WatchlistEntry
from .repositories import AccountRepository, WatchlistRepository, PricesRepository
from .api_clients import FrankfurterClient


class AccountService:
    """Service for managing user accounts.

    Provides methods for user registration and authentication.

    Attributes:
        repo: The account repository for data persistence.
    """

    def __init__(self, repo: AccountRepository):
        """Initialize the AccountService.

        Args:
            repo: The AccountRepository instance for data operations.
        """
        self.repo = repo

    def register(self, username: str, password: str, email: str | None = None) -> Account:
        """Register a new user account.

        Args:
            username: The desired username (must be unique).
            password: The user's password.
            email: The user's email address (optional).

        Returns:
            The created Account object.

        Raises:
            ValueError: If the username already exists.
        """
        if self.repo.find(username):
            raise ValueError("username exists")
        acc = Account(username=username, password=password, email=email, created=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        self.repo.add_account(acc)
        return acc

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate a user with username and password.

        Args:
            username: The username to authenticate.
            password: The password to verify.

        Returns:
            True if authentication succeeds, False otherwise.
        """
        acc = self.repo.find(username)
        return acc is not None and acc.password == password


class WatchlistService:
    """Service for managing user watchlists and price tracking.

    Provides methods for adding symbols to watchlists, retrieving watchlist
    entries, and fetching price data from external APIs.

    Attributes:
        watchlist_repo: The repository for watchlist data.
        prices_repo: The repository for price record data.
        api_client: The API client for fetching exchange rates.
    """

    SYMBOL_RE = re.compile(r"^([A-Z]{3})([A-Z]{3})$")

    def __init__(self, watchlist_repo: WatchlistRepository, prices_repo: PricesRepository, api_client: FrankfurterClient):
        """Initialize the WatchlistService.

        Args:
            watchlist_repo: The WatchlistRepository for watchlist operations.
            prices_repo: The PricesRepository for price record operations.
            api_client: The FrankfurterClient for API requests.
        """
        self.watchlist_repo = watchlist_repo
        self.prices_repo = prices_repo
        self.api_client = api_client

    def add_symbol(self, username: str, base: str, quote: str) -> PriceRecord:
        """Add a currency pair symbol to a user's watchlist and record its price.

        Validates the currency codes, creates a watchlist entry, fetches the
        current exchange rate from the API, and stores the price record.

        Args:
            username: The username whose watchlist to update.
            base: The base currency ISO code (e.g., "USD").
            quote: The quote currency ISO code (e.g., "SEK").

        Returns:
            The PriceRecord containing the fetched exchange rate.

        Raises:
            ValueError: If the currency codes are invalid.
        """
        base_up = base.upper()
        quote_up = quote.upper()
        if not self.SYMBOL_RE.match(base_up + quote_up):
            raise ValueError("invalid currency codes")
        symbol = f"FX:{base_up}{quote_up}"
        self.watchlist_repo.add(username, WatchlistEntry(symbol))
        resp = self.api_client.latest(base_up, quote_up)
        # Frankfurter returns { "amount":1.0, "base":"USD", "date":"2022-01-01", "rates": {"SEK": 10.0}}
        price = float(resp["rates"][quote_up])
        date = resp.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
        record = PriceRecord(symbol=symbol, price=price, date=date, source="Frankfurter")
        self.prices_repo.append(username, record)
        return record

    def list_watchlist(self, username: str) -> List[WatchlistEntry]:
        """Retrieve all watchlist entries for a user.

        Args:
            username: The username whose watchlist to retrieve.

        Returns:
            A list of WatchlistEntry objects.
        """
        return self.watchlist_repo.list(username)

    def get_latest_prices(self, username: str) -> List[PriceRecord]:
        """Retrieve the latest price records for a user.

        Args:
            username: The username whose price records to retrieve.

        Returns:
            A list of PriceRecord objects with the latest price for each symbol.
        """
        return self.prices_repo.list_latest(username)
