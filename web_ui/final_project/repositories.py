# final_project/repositories.py
"""Repository layer for data persistence operations.

This module provides abstract interfaces and CSV-based implementations
for managing accounts, watchlists, and price records.
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path
import csv
import shutil
from .models import Account, PriceRecord, WatchlistEntry
from .config import DATA_DIR, ACCOUNT_DIR


class RepositoryError(Exception):
    """Exception raised for repository-related errors."""
    pass


# --- Account repository interface ---
class AccountRepository(ABC):
    """Abstract base class defining the account repository interface."""

    @abstractmethod
    def list_accounts(self) -> List[Account]:
        """Retrieve all accounts from the repository.

        Returns:
            A list of all Account objects.
        """
        ...

    @abstractmethod
    def add_account(self, account: Account) -> None:
        """Add a new account to the repository.

        Args:
            account: The Account object to add.

        Raises:
            RepositoryError: If an account with the same username already exists.
        """
        ...

    @abstractmethod
    def find(self, username: str) -> Optional[Account]:
        """Find an account by username.

        Args:
            username: The username to search for.

        Returns:
            The Account object if found, None otherwise.
        """
        ...

    @abstractmethod
    def update(self, account: Account) -> None:
        """Update an existing account.

        Args:
            account: The Account object with updated data.

        Raises:
            RepositoryError: If the account does not exist.
        """
        ...

    @abstractmethod
    def delete(self, username: str) -> None:
        """Delete an account by username.

        Args:
            username: The username of the account to delete.
        """
        ...


# --- CSV implementation for AccountRepository ---
class CSVAccountRepository(AccountRepository):
    """CSV-based implementation of the AccountRepository interface."""

    def __init__(self, path: Path = DATA_DIR / "Accounts.csv"):
        """Initialize the CSV account repository.

        Args:
            path: Path to the CSV file storing account data.
                  Defaults to DATA_DIR/Accounts.csv.
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["username","password","email","date"])
                writer.writeheader()

    def list_accounts(self) -> List[Account]:
        """Retrieve all accounts from the CSV file.

        Returns:
            A list of all Account objects.
        """
        accounts=[]
        with open(self.path, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                accounts.append(Account(r["username"], r["password"], r.get("email") or None, r.get("date") or None))
        return accounts

    def add_account(self, account: Account) -> None:
        """Add a new account to the CSV file.

        Args:
            account: The Account object to add.

        Raises:
            RepositoryError: If an account with the same username already exists.
        """
        if self.find(account.username):
            raise RepositoryError("username exists")
        with open(self.path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["username","password","email","date"])
            writer.writerow({"username": account.username, "password": account.password, "email": account.email or "", "date": account.created or ""})

    def find(self, username: str) -> Optional[Account]:
        """Find an account by username.

        Args:
            username: The username to search for.

        Returns:
            The Account object if found, None otherwise.
        """
        for a in self.list_accounts():
            if a.username == username:
                return a
        return None

    def update(self, account: Account) -> None:
        """Update an existing account in the CSV file.

        Args:
            account: The Account object with updated data.

        Raises:
            RepositoryError: If the account does not exist.
        """
        accounts = self.list_accounts()
        for i, a in enumerate(accounts):
            if a.username == account.username:
                accounts[i] = account
                break
        else:
            raise RepositoryError("Account not found")
        with open(self.path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["username","password","email","date"])
            writer.writeheader()
            for acc in accounts:
                writer.writerow({"username": acc.username, "password": acc.password, "email": acc.email or "", "date": acc.created or ""})

    def delete(self, username: str) -> None:
        """Delete an account by username from the CSV file and remove user data files.

        Args:
            username: The username of the account to delete.
        
        Raises:
            RepositoryError: If unable to delete user directory.
        """
        accounts = [a for a in self.list_accounts() if a.username != username]
        with open(self.path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["username","password","email","date"])
            writer.writeheader()
            for acc in accounts:
                writer.writerow({"username": acc.username, "password": acc.password, "email": acc.email or "", "date": acc.created or ""})

        # Also delete user-specific CSV files from shared account_directory
        user_dir = ACCOUNT_DIR / username
        if user_dir.exists():
            try:
                shutil.rmtree(user_dir)
            except (PermissionError, OSError) as e:
                raise RepositoryError(f"Failed to delete user directory: {e}")

# --- Watchlist repository (simple CSV per user) ---
class WatchlistRepository(ABC):
    """Abstract base class defining the watchlist repository interface."""

    @abstractmethod
    def list(self, username: str) -> List[WatchlistEntry]:
        """Retrieve all watchlist entries for a user.

        Args:
            username: The username whose watchlist to retrieve.

        Returns:
            A list of WatchlistEntry objects.
        """
        ...

    @abstractmethod
    def add(self, username: str, entry: WatchlistEntry) -> None:
        """Add a new entry to a user's watchlist.

        Args:
            username: The username whose watchlist to update.
            entry: The WatchlistEntry to add.
        """
        ...

    @abstractmethod
    def remove(self, username: str, symbol: str) -> None:
        """Remove an entry from a user's watchlist by symbol.

        Args:
            username: The username whose watchlist to update.
            symbol: The symbol of the entry to remove.
        """
        ...


class CSVWatchlistRepository(WatchlistRepository):
    """CSV-based implementation of the WatchlistRepository interface.

    Each user has their own watchlist CSV file in ACCOUNT_DIR/username/Watchlist.csv
    matching the terminal UI structure.
    """

    def __init__(self, base_dir: Path = ACCOUNT_DIR):
        """Initialize the CSV watchlist repository.

        Args:
            base_dir: The base directory where user account directories are stored.
                      Defaults to ACCOUNT_DIR.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _user_dir(self, username: str) -> Path:
        """Get the path to a user's account directory.

        Args:
            username: The username whose directory path to generate.

        Returns:
            The Path to the user's account directory.
        """
        return self.base_dir / username

    def _path(self, username: str) -> Path:
        """Get the path to a user's watchlist CSV file.

        Args:
            username: The username whose watchlist path to generate.

        Returns:
            The Path to the user's watchlist CSV file.
        """
        return self._user_dir(username) / "Watchlist.csv"

    def list(self, username: str) -> List[WatchlistEntry]:
        """Retrieve all watchlist entries for a user.

        Args:
            username: The username whose watchlist to retrieve.

        Returns:
            A list of WatchlistEntry objects. Returns an empty list
            if the user's watchlist file does not exist.
        """
        p = self._path(username)
        if not p.exists():
            return []
        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            return [WatchlistEntry(r["symbol"]) for r in reader]

    def add(self, username: str, entry: WatchlistEntry) -> None:
        """Add a new entry to a user's watchlist.

        Args:
            username: The username whose watchlist to update.
            entry: The WatchlistEntry to add.
        """
        p = self._path(username)
        # Ensure user directory exists
        p.parent.mkdir(parents=True, exist_ok=True)
        # Check if file exists to determine if we need headers
        needs_header = not p.exists() or p.stat().st_size == 0
        with open(p, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol"])
            if needs_header:
                writer.writeheader()
            writer.writerow({"symbol": entry.symbol})

    def remove(self, username: str, symbol: str) -> None:
        """Remove an entry from a user's watchlist by symbol.

        Args:
            username: The username whose watchlist to update.
            symbol: The symbol of the entry to remove.
        """
        p = self._path(username)
        if not p.exists():
            return
        rows = []
        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
        remaining = [r for r in rows if r.get("symbol") != symbol]
        with open(p, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol"])
            writer.writeheader()
            for r in remaining:
                writer.writerow({"symbol": r["symbol"]})

# --- Prices repository ---
class PricesRepository(ABC):
    """Abstract base class defining the prices repository interface."""

    @abstractmethod
    def append(self, username: str, record: PriceRecord) -> None:
        """Append a price record to the user's price history.

        Args:
            username: The username whose price history to update.
            record: The PriceRecord to append.
        """
        ...

    @abstractmethod
    def list_latest(self, username: str) -> List[PriceRecord]:
        """Retrieve the latest price records for a user.

        Args:
            username: The username whose price records to retrieve.

        Returns:
            A list of PriceRecord objects, with the latest record
            for each symbol.
        """
        ...

    @abstractmethod
    def remove(self, username: str, symbol: str) -> None:
        """Remove price records for a specific symbol.

        Args:
            username: The username whose price records to update.
            symbol: The symbol to remove.
        """
        ...


class CSVPricesRepository(PricesRepository):
    """CSV-based implementation of the PricesRepository interface.

    Each user has their own prices CSV file in ACCOUNT_DIR/username/Prices.csv
    matching the terminal UI structure.
    """

    def __init__(self, base_dir: Path = ACCOUNT_DIR):
        """Initialize the CSV prices repository.

        Args:
            base_dir: The directory where user account directories are stored.
                      Defaults to ACCOUNT_DIR.
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _user_dir(self, username: str) -> Path:
        """Get the path to a user's account directory.

        Args:
            username: The username whose directory path to generate.

        Returns:
            The Path to the user's account directory.
        """
        return self.base_dir / username

    def _path(self, username: str) -> Path:
        """Get the path to a user's prices CSV file.

        Args:
            username: The username whose prices path to generate.

        Returns:
            The Path to the user's prices CSV file.
        """
        return self._user_dir(username) / "Prices.csv"

    def append(self, username: str, record: PriceRecord) -> None:
        """Append a price record to the user's price history.

        Args:
            username: The username whose price history to update.
            record: The PriceRecord to append.
        """
        p = self._path(username)
        # Ensure user directory exists
        p.parent.mkdir(parents=True, exist_ok=True)
        # Check if file exists to determine if we need headers
        needs_header = not p.exists() or p.stat().st_size == 0
        with open(p, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol","price","date","source"])
            if needs_header:
                writer.writeheader()
            writer.writerow({"symbol": record.symbol, "price": record.price, "date": record.date, "source": record.source})

    def list_latest(self, username: str) -> List[PriceRecord]:
        """Retrieve the latest price records for a user.

        Reads all records and returns the most recent entry for each symbol.

        Args:
            username: The username whose price records to retrieve.

        Returns:
            A list of PriceRecord objects, with the latest record for each symbol.
            Returns an empty list if the user's prices file does not exist.
        """
        p = self._path(username)
        if not p.exists():
            return []
        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            # return last record per symbol (simple strategy: read all, keep last)
            records = list(reader)
        out = {}
        for r in records:
            out[r["symbol"]] = PriceRecord(r["symbol"], float(r["price"]), r["date"], r["source"])
        return list(out.values())

    def remove(self, username: str, symbol: str) -> None:
        """Remove price records for a specific symbol from the user's prices file.

        Args:
            username: The username whose price records to update.
            symbol: The symbol to remove.
        """
        p = self._path(username)
        if not p.exists():
            return
        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            records = list(r for r in reader if r["symbol"] != symbol)
        with open(p, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol", "price", "date", "source"])
            writer.writeheader()
            for r in records:
                writer.writerow({"symbol": r["symbol"], "price": r["price"], "date": r["date"], "source": r["source"]})
