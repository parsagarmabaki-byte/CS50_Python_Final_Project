# final_project/web.py
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
from uuid import uuid4
import io
import csv

# Import build_services to reuse DI
from .cli import build_services
from .models import PriceRecord, WatchlistEntry

app = FastAPI(title="final_project API")

# --- Simple in-memory token store (demo only) ---
# token -> username
_token_store: dict[str, str] = {}

# --- Pydantic schemas ---
class RegisterIn(BaseModel):
    username: str
    password: str
    email: Optional[str] = None

class LoginIn(BaseModel):
    username: str
    password: str

class TokenOut(BaseModel):
    token: str

class AddSymbolIn(BaseModel):
    base: str
    quote: str

class WatchlistOut(BaseModel):
    symbol: str

class PriceOut(BaseModel):
    symbol: str
    price: float
    date: str
    source: str

# --- Dependency helpers ---
def get_services():
    """Return tuple (account_service, watch_service). Recreate per request for simplicity."""
    acc_svc, watch_svc = build_services()
    return {"account_service": acc_svc, "watch_service": watch_svc}

def auth_user(authorization: Optional[str] = Header(None), x_auth_token: Optional[str] = Header(None)):
    """Resolve token from Authorization: Bearer <token> or X-Auth-Token header."""
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
    return {"ok": True}

@app.post("/register")
def register(payload: RegisterIn, services=Depends(get_services)):
    acc_svc = services["account_service"]
    try:
        acc = acc_svc.register(payload.username, payload.password, payload.email)
        return {"username": acc.username, "created": acc.created}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/login", response_model=TokenOut)
def login(payload: LoginIn, services=Depends(get_services)):
    acc_svc = services["account_service"]
    if not acc_svc.authenticate(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = str(uuid4())
    _token_store[token] = payload.username
    return TokenOut(token=token)

@app.post("/logout")
def logout(username: str = Depends(auth_user)):
    # remove tokens for this user (invalidate all tokens for simplicity)
    tokens_to_remove = [t for t, u in _token_store.items() if u == username]
    for t in tokens_to_remove:
        _token_store.pop(t, None)
    return {"ok": True}

@app.get("/me/watchlist", response_model=List[WatchlistOut])
def get_watchlist(username: str = Depends(auth_user), services=Depends(get_services)):
    watch_svc = services["watch_service"]
    entries = watch_svc.list_watchlist(username)
    return [WatchlistOut(symbol=e.symbol) for e in entries]

@app.post("/me/watchlist", response_model=PriceOut)
def add_symbol(payload: AddSymbolIn, username: str = Depends(auth_user), services=Depends(get_services)):
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
    watch_svc = services["watch_service"]
    prs = watch_svc.get_latest_prices(username)
    return [PriceOut(symbol=p.symbol, price=p.price, date=p.date, source=p.source) for p in prs]

@app.post("/me/prices/update")
def update_all_prices(username: str = Depends(auth_user), services=Depends(get_services)):
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
