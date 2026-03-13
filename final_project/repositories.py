# final_project/repositories.py
from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path
import csv
from .models import Account, PriceRecord, WatchlistEntry
from .config import DATA_DIR

class RepositoryError(Exception):
    pass

# --- Account repository interface ---
class AccountRepository(ABC):
    @abstractmethod
    def list_accounts(self) -> List[Account]: ...
    @abstractmethod
    def add_account(self, account: Account) -> None: ...
    @abstractmethod
    def find(self, username: str) -> Optional[Account]: ...
    @abstractmethod
    def update(self, account: Account) -> None: ...
    @abstractmethod
    def delete(self, username: str) -> None: ...

# --- CSV implementation for AccountRepository ---
class CSVAccountRepository(AccountRepository):
    def __init__(self, path: Path = DATA_DIR / "Accounts.csv"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            with open(self.path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["username","password","email","date"])
                writer.writeheader()

    def list_accounts(self):
        accounts=[]
        with open(self.path, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                accounts.append(Account(r["username"], r["password"], r.get("email") or None, r.get("date") or None))
        return accounts

    def add_account(self, account: Account):
        if self.find(account.username):
            raise RepositoryError("username exists")
        with open(self.path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["username","password","email","date"])
            writer.writerow({"username": account.username, "password": account.password, "email": account.email or "", "date": account.created or ""})

    def find(self, username):
        for a in self.list_accounts():
            if a.username == username:
                return a
        return None

    def update(self, account: Account):
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

    def delete(self, username):
        accounts = [a for a in self.list_accounts() if a.username != username]
        with open(self.path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["username","password","email","date"])
            writer.writeheader()
            for acc in accounts:
                writer.writerow({"username": acc.username, "password": acc.password, "email": acc.email or "", "date": acc.created or ""})

# --- Watchlist repository (simple CSV per user) ---
class WatchlistRepository(ABC):
    @abstractmethod
    def list(self, username: str) -> List[WatchlistEntry]: ...
    @abstractmethod
    def add(self, username: str, entry: WatchlistEntry) -> None: ...

class CSVWatchlistRepository(WatchlistRepository):
    def __init__(self, base_dir: Path = DATA_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, username: str) -> Path:
        return self.base_dir / f"{username}_watchlist.csv"

    def list(self, username: str):
        p = self._path(username)
        if not p.exists():
            return []
        with open(p, newline="") as f:
            reader = csv.DictReader(f)
            return [WatchlistEntry(r["symbol"]) for r in reader]

    def add(self, username: str, entry: WatchlistEntry):
        p = self._path(username)
        exists = p.exists()
        with open(p, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol"])
            if not exists:
                writer.writeheader()
            writer.writerow({"symbol": entry.symbol})

# --- Prices repository ---
class PricesRepository(ABC):
    @abstractmethod
    def append(self, username: str, record: PriceRecord) -> None: ...
    @abstractmethod
    def list_latest(self, username: str) -> List[PriceRecord]: ...

class CSVPricesRepository(PricesRepository):
    def __init__(self, base_dir: Path = DATA_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, username: str) -> Path:
        return self.base_dir / f"{username}_prices.csv"

    def append(self, username: str, record: PriceRecord):
        p = self._path(username)
        exists = p.exists()
        with open(p, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol","price","date","source"])
            if not exists:
                writer.writeheader()
            writer.writerow({"symbol": record.symbol, "price": record.price, "date": record.date, "source": record.source})

    def list_latest(self, username: str):
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
