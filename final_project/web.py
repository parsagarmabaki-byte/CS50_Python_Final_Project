# final_project/web.py
"""FastAPI web application for the final project.

This module provides a REST API for user authentication, watchlist management,
and price record operations using FastAPI.
"""
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4
import io
import csv

# Import build_services to reuse DI
from .cli import build_services
from .models import PriceRecord, WatchlistEntry

app = FastAPI(title="final_project API")

# --- CORS Middleware ---
# Allow frontend to connect (dev: localhost:5173, production: configure as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Simple in-memory token store (demo only) ---
# token -> username
_token_store: dict[str, str] = {}

# --- Pydantic schemas ---
class RegisterIn(BaseModel):
    """Request schema for user registration."""
    username: str
    password: str
    email: Optional[str] = None


class LoginIn(BaseModel):
    """Request schema for user login."""
    username: str
    password: str


class TokenOut(BaseModel):
    """Response schema containing an authentication token."""
    token: str


class AddSymbolIn(BaseModel):
    """Request schema for adding a currency symbol to watchlist."""
    base: str
    quote: str


class WatchlistOut(BaseModel):
    """Response schema for a watchlist entry."""
    symbol: str


class PriceOut(BaseModel):
    """Response schema for a price record."""
    symbol: str
    price: float
    date: str
    source: str


# --- Dependency helpers ---
def get_services():
    """Build and return service instances for dependency injection.

    Returns:
        A dictionary containing 'account_service' and 'watch_service' instances.
    """
    acc_svc, watch_svc = build_services()
    return {"account_service": acc_svc, "watch_service": watch_svc}


def auth_user(authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Authenticate a user from request headers.

    Resolves the authentication token from either the Authorization header
    (Bearer scheme) or the X-Auth-Token header, and validates it against
    the in-memory token store.

    Args:
        authorization: The Authorization header value.
        x_auth_token: The X-Auth-Token header value.

    Returns:
        The username associated with the token.

    Raises:
        HTTPException: 401 if the token is missing or invalid.
    """
    token = None
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1]
    if token is None and x_auth_token:
        token = x_auth_token
    if not token:
        raise HTTPException(status_code=401, detail="Missing auth token")
    username = _token_store.get(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return username

# --- Routes ---
@app.get("/health")
def health():
    """Health check endpoint.

    Returns:
        A simple status object indicating the API is running.
    """
    return {"ok": True}


@app.post("/register")
def register(payload: RegisterIn, services=Depends(get_services)):
    """Register a new user account.

    Args:
        payload: The registration data containing username, password, and email.
        services: The injected service instances.

    Returns:
        The created user's username and creation date.

    Raises:
        HTTPException: 400 if registration fails (e.g., username exists).
    """
    acc_svc = services["account_service"]
    try:
        acc = acc_svc.register(payload.username, payload.password, payload.email)
        return {"username": acc.username, "created": acc.created}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/login", response_model=TokenOut)
def login(payload: LoginIn, services=Depends(get_services)):
    """Authenticate a user and return an authentication token.

    Args:
        payload: The login credentials containing username and password.
        services: The injected service instances.

    Returns:
        An authentication token.

    Raises:
        HTTPException: 401 if credentials are invalid.
    """
    acc_svc = services["account_service"]
    if not acc_svc.authenticate(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = str(uuid4())
    _token_store[token] = payload.username
    return TokenOut(token=token)


@app.post("/logout")
def logout(username: str = Depends(auth_user)):
    """Log out the current user by invalidating their authentication token.

    Args:
        username: The authenticated username (from dependency injection).

    Returns:
        A success status object.
    """
    # remove tokens for this user (invalidate all tokens for simplicity)
    tokens_to_remove = [t for t, u in _token_store.items() if u == username]
    for t in tokens_to_remove:
        _token_store.pop(t, None)
    return {"ok": True}


@app.get("/me/watchlist", response_model=List[WatchlistOut])
def get_watchlist(username: str = Depends(auth_user), services=Depends(get_services)):
    """Retrieve the authenticated user's watchlist.

    Args:
        username: The authenticated username (from dependency injection).
        services: The injected service instances.

    Returns:
        A list of watchlist entries.
    """
    watch_svc = services["watch_service"]
    entries = watch_svc.list_watchlist(username)
    return [WatchlistOut(symbol=e.symbol) for e in entries]


@app.post("/me/watchlist", response_model=PriceOut)
def add_symbol(payload: AddSymbolIn, username: str = Depends(auth_user), services=Depends(get_services)):
    """Add a currency pair symbol to the user's watchlist.

    Args:
        payload: The currency pair data containing base and quote currencies.
        username: The authenticated username (from dependency injection).
        services: The injected service instances.

    Returns:
        The price record for the newly added symbol.

    Raises:
        HTTPException: 400 if the currency codes are invalid or the operation fails.
    """
    watch_svc = services["watch_service"]
    try:
        pr = watch_svc.add_symbol(username, payload.base, payload.quote)
        return PriceOut(symbol=pr.symbol, price=pr.price, date=pr.date, source=pr.source)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/me/watchlist/{symbol}")
def remove_symbol(symbol: str, username: str = Depends(auth_user), services=Depends(get_services)):
    """Remove a symbol from the user's watchlist.

    Args:
        symbol: The symbol to remove from the watchlist.
        username: The authenticated username (from dependency injection).
        services: The injected service instances.

    Returns:
        A success status object.

    Raises:
        HTTPException: 400 if removal fails, 404 if watchlist not found,
                      or 500 if the repository doesn't support removal.
    """
    # best-effort removal: call repo if it supports remove, else rewrite CSV
    watch_svc = services["watch_service"]
    repo = getattr(watch_svc, "watchlist_repo", None)
    if repo is None:
        raise HTTPException(status_code=500, detail="Watchlist repository not available")
    # prefer remove() if implemented
    if hasattr(repo, "remove"):
        try:
            repo.remove(username, symbol)
            return {"ok": True}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    # fallback: rewrite CSV via _path if available
    if not hasattr(repo, "_path"):
        raise HTTPException(status_code=500, detail="Repository does not support removal")
    p = repo._path(username)
    if not p.exists():
        raise HTTPException(status_code=404, detail="Watchlist not found")
    # read entries, filter and rewrite
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
    return {"ok": True}


@app.get("/me/prices", response_model=List[PriceOut])
def get_latest_prices(username: str = Depends(auth_user), services=Depends(get_services)):
    """Retrieve the latest price records for the authenticated user.

    Args:
        username: The authenticated username (from dependency injection).
        services: The injected service instances.

    Returns:
        A list of price records with the latest price for each symbol.
    """
    watch_svc = services["watch_service"]
    prs = watch_svc.get_latest_prices(username)
    return [PriceOut(symbol=p.symbol, price=p.price, date=p.date, source=p.source) for p in prs]


@app.post("/me/prices/update")
def update_all_prices(username: str = Depends(auth_user), services=Depends(get_services)):
    """Update prices for all symbols in the user's watchlist.

    Fetches the latest exchange rates for all watched currency pairs.

    Args:
        username: The authenticated username (from dependency injection).
        services: The injected service instances.

    Returns:
        A success status object.

    Raises:
        HTTPException: 500 if the update fails.
    """
    watch_svc = services["watch_service"]
    try:
        if hasattr(watch_svc, "update_all_prices"):
            watch_svc.update_all_prices(username)
        else:
            # fallback: iterate watchlist entries
            import re
            for e in watch_svc.list_watchlist(username):
                m = re.fullmatch(r"FX:([A-Z]{3})([A-Z]{3})", e.symbol)
                if m:
                    base, quote = m.groups()
                    watch_svc.add_symbol(username, base, quote)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/me/prices/export")
def export_prices(username: str = Depends(auth_user), services=Depends(get_services)):
    """Export the user's latest price records as a CSV file.

    Args:
        username: The authenticated username (from dependency injection).
        services: The injected service instances.

    Returns:
        A streaming CSV file response containing all price records.
    """
    watch_svc = services["watch_service"]
    prs = watch_svc.get_latest_prices(username)
    # create CSV in memory and stream it
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["symbol", "price", "date", "source"])
    writer.writeheader()
    for p in prs:
        writer.writerow({"symbol": p.symbol, "price": p.price, "date": p.date, "source": p.source})
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=prices.csv"})
