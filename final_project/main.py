#!/usr/bin/env python3
# main.py — Interactive launcher that provides the "full app" menu-driven CLI
from __future__ import annotations
import sys
import logging
from pathlib import Path
from typing import Optional

LOG = logging.getLogger("final_project.main")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

# Lazy imports to keep startup light
def _get_services():
    """
    Returns (account_service, watch_service, prices_repo) tuple.
    Delegates creation to final_project.cli:build_services for consistent DI.
    """
    try:
        from final_project.cli import build_services
    except Exception as e:
        LOG.exception("Cannot import build_services from final_project.cli: %s", e)
        raise
    return build_services()


class Session:
    """
    Simple in-memory session holding logged-in username.
    """
    def __init__(self):
        self.username: Optional[str] = None

    def login(self, username: str):
        self.username = username

    def logout(self):
        self.username = None

    @property
    def is_authenticated(self) -> bool:
        return self.username is not None


# ---------- UI helpers ----------
def clear_screen():
    """Cross-platform console clear."""
    import os
    os.system("cls" if os.name == "nt" else "clear")


def pause(msg: str = "Press Enter to continue..."):
    try:
        input(msg)
    except KeyboardInterrupt:
        print()


def read_nonempty(prompt: str) -> str:
    while True:
        v = input(prompt).strip()
        if v:
            return v
        print("Value required.")


def show_header(title: str):
    clear_screen()
    print("=" * 60)
    print(f"{title}")
    print("=" * 60)


# ---------- Application flows ----------
def flow_register(account_service):
    show_header("Register new user")
    username = read_nonempty("Username: ")
    password = read_nonempty("Password: ")
    email = input("Email (optional): ").strip() or None
    try:
        acc = account_service.register(username, password, email)
        print(f"Registered user: {acc.username} created={acc.created}")
    except Exception as e:
        print(f"Error: {e}")
    pause()


def flow_login(account_service, session: Session):
    show_header("Login")
    username = read_nonempty("Username: ")
    password = read_nonempty("Password: ")
    ok = account_service.authenticate(username, password)
    if ok:
        session.login(username)
        print(f"Logged in as {username}")
    else:
        print("Invalid username or password.")
    pause()


def flow_logout(session: Session):
    if session.is_authenticated:
        print(f"Logging out {session.username}")
        session.logout()
    else:
        print("Not logged in.")
    pause()


def flow_view_watchlist(watch_service, session: Session):
    if not session.is_authenticated:
        print("You must be logged in.")
        pause()
        return
    show_header(f"{session.username} — Watchlist")
    entries = watch_service.list_watchlist(session.username)
    if not entries:
        print("Watchlist empty.")
    else:
        for i, e in enumerate(entries, 1):
            print(f"{i}. {e.symbol}")
    pause()


def flow_add_symbol(watch_service, session: Session):
    if not session.is_authenticated:
        print("You must be logged in.")
        pause()
        return
    show_header("Add symbol to watchlist")
    base = read_nonempty("Base currency (e.g. USD): ").upper()
    quote = read_nonempty("Quote currency (e.g. SEK): ").upper()
    try:
        pr = watch_service.add_symbol(session.username, base, quote)
        print(f"Added {pr.symbol} — price {pr.price} (date {pr.date})")
    except Exception as e:
        print(f"Error adding symbol: {e}")
    pause()


def flow_view_latest_prices(watch_service, session: Session):
    if not session.is_authenticated:
        print("You must be logged in.")
        pause()
        return
    show_header("Latest recorded prices")
    prs = watch_service.get_latest_prices(session.username)
    if not prs:
        print("No price records.")
    else:
        for p in prs:
            print(f"{p.symbol:12} {p.price:12} {p.date:12} {p.source}")
    pause()


def flow_update_all_prices(watch_service, session: Session):
    if not session.is_authenticated:
        print("You must be logged in.")
        pause()
        return
    show_header("Update prices for all watchlist entries")
    try:
        # update_all_prices may be expensive — call it and report
        # It was implemented in the service skeleton; if not, we emulate:
        if hasattr(watch_service, "update_all_prices"):
            watch_service.update_all_prices(session.username)
            print("Prices updated.")
        else:
            # fallback: iterate entries and call add_symbol-like fetch
            entries = watch_service.list_watchlist(session.username)
            for e in entries:
                import re
                m = re.fullmatch(r"FX:([A-Z]{3})([A-Z]{3})", e.symbol)
                if m:
                    base, quote = m.groups()
                    watch_service.add_symbol(session.username, base, quote)
            print("Prices updated (fallback).")
    except Exception as exc:
        print("Failed to update prices:", exc)
    pause()


def flow_remove_symbol(watch_service, session: Session):
    # Removing is repository-specific; our CSVWatchlistRepository doesn't have delete.
    # Implement a simple remove by rewriting the watchlist CSV: we'll try to call repo directly.
    if not session.is_authenticated:
        print("You must be logged in.")
        pause()
        return
    try:
        repo = watch_service.watchlist_repo
    except Exception:
        repo = None

    if repo is None or not hasattr(repo, "list") or not hasattr(repo, "add"):
        print("Remove operation not supported by repository implementation.")
        pause()
        return

    entries = repo.list(session.username)
    if not entries:
        print("Watchlist empty.")
        pause()
        return
    show_header("Remove symbol — select index to remove")
    for i, e in enumerate(entries, 1):
        print(f"{i}. {e.symbol}")
    choice = read_nonempty("Index to remove (or blank to cancel): ")
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(entries):
            raise ValueError("index out of range")
        # rewrite: remove chosen symbol and rewrite CSV via repo internal API (CSVWatchlistRepository)
        # Try to detect CSVWatchlistRepository path and rewrite file.
        # Best effort: call repo._path and rewrite file contents.
        if hasattr(repo, "_path"):
            p = repo._path(session.username)
            remaining = [e for j, e in enumerate(entries) if j != idx]
            import csv
            with open(p, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["symbol"])
                writer.writeheader()
                for r in remaining:
                    writer.writerow({"symbol": r.symbol})
            print("Removed.")
        else:
            print("Repository does not support removal via this launcher.")
    except Exception as e:
        print("Failed to remove:", e)
    pause()


def flow_export_prices(watch_service, session: Session):
    if not session.is_authenticated:
        print("You must be logged in.")
        pause()
        return
    out = input("Export path (file) — default: export_prices.csv: ").strip() or "export_prices.csv"
    try:
        prs = watch_service.get_latest_prices(session.username)
        import csv
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["symbol", "price", "date", "source"])
            writer.writeheader()
            for p in prs:
                writer.writerow({"symbol": p.symbol, "price": p.price, "date": p.date, "source": p.source})
        print(f"Exported {len(prs)} records to {out}")
    except Exception as e:
        print("Export failed:", e)
    pause()


def flow_start_web_server():
    show_header("Start web server")
    host = input("Host (default 127.0.0.1): ").strip() or "127.0.0.1"
    port_s = input("Port (default 8000): ").strip() or "8000"
    try:
        port = int(port_s)
    except Exception:
        print("Invalid port.")
        pause()
        return
    reload = input("Reload? (y/N): ").strip().lower().startswith("y")
    try:
        import uvicorn
    except Exception:
        print("uvicorn not installed. Install with: pip install uvicorn[standard]")
        pause()
        return
    print(f"Starting uvicorn on {host}:{port} (reload={reload}). Use Ctrl-C to stop.")
    try:
        from final_project.web import app
    except Exception as e:
        print("Failed to import web app:", e)
        pause()
        return
    try:
        uvicorn.run(app, host=host, port=port, reload=reload)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    pause()


def flow_health_check():
    try:
        from final_project.web import health  # type: ignore
        res = health()
        print("Health:", res)
    except Exception:
        # fallback to import checks
        import importlib
        try:
            importlib.import_module("final_project.services")
            importlib.import_module("final_project.repositories")
            print("Core modules import OK.")
        except Exception as e:
            print("Health check failed:", e)
    pause()


# ---------- Main menu ----------
def main_menu_loop():
    try:
        account_service, watch_service = _get_services()
    except Exception:
        print("Failed to initialize services. See logs.")
        return 1

    session = Session()

    MENU = [
        ("Register new user", lambda: flow_register(account_service)),
        ("Login", lambda: flow_login(account_service, session)),
        ("Logout", lambda: flow_logout(session)),
        ("View my watchlist", lambda: flow_view_watchlist(watch_service, session)),
        ("Add symbol to watchlist", lambda: flow_add_symbol(watch_service, session)),
        ("Remove symbol from watchlist", lambda: flow_remove_symbol(watch_service, session)),
        ("View latest recorded prices", lambda: flow_view_latest_prices(watch_service, session)),
        ("Update prices for all watchlist entries", lambda: flow_update_all_prices(watch_service, session)),
        ("Export latest prices to CSV", lambda: flow_export_prices(watch_service, session)),
        ("Start web server (uvicorn)", flow_start_web_server),
        ("Health check", flow_health_check),
        ("Quit", None),
    ]

    while True:
        show_header("Final Project — Main Menu")
        print(f"Logged in: {session.username if session.is_authenticated else '(not logged in)'}")
        print()
        for i, (label, _) in enumerate(MENU, 1):
            print(f"{i}. {label}")
        print()
        choice = input("Choose an option (number): ").strip()
        if not choice:
            continue
        try:
            idx = int(choice) - 1
            if idx < 0 or idx >= len(MENU):
                print("Invalid choice")
                pause()
                continue
        except ValueError:
            print("Enter a number.")
            pause()
            continue

        label, handler = MENU[idx]
        if label == "Quit":
            print("Bye.")
            return 0
        try:
            if handler:
                handler()
        except KeyboardInterrupt:
            print("\nInterrupted; returning to menu.")
            pause()
        except Exception as exc:
            LOG.exception("Error during menu action: %s", exc)
            print("Action failed:", exc)
            pause()


# ---------- CLI entrypoint ----------
def build_arg_parser():
    import argparse
    p = argparse.ArgumentParser(prog="main", description="Interactive launcher for final_project")
    p.add_argument("--demo-register", nargs=3, metavar=("username","password","email"), help="Register a demo user")
    p.add_argument("--demo-add-symbol", nargs=3, metavar=("username","base","quote"), help="Add symbol for demo user (requires user exists)")
    p.add_argument("--no-menu", action="store_true", help="Run demo flags but do not enter interactive menu")
    return p


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    parser = build_arg_parser()
    ns = parser.parse_args(argv)

    # initialize services
    try:
        account_service, watch_service = _get_services()
    except Exception as e:
        LOG.exception("Failed to initialize services: %s", e)
        print("Startup failed. See logs.")
        return 2

    # demo register
    if ns.demo_register:
        username, password, email = ns.demo_register
        try:
            acc = account_service.register(username, password, email)
            print(f"Registered demo user {acc.username}")
        except Exception as e:
            print("Demo register failed:", e)

    if ns.demo_add_symbol:
        username, base, quote = ns.demo_add_symbol
        try:
            pr = watch_service.add_symbol(username, base, quote)
            print(f"Added demo symbol {pr.symbol} price={pr.price}")
        except Exception as e:
            print("Demo add symbol failed:", e)

    if ns.no_menu:
        return 0

    return main_menu_loop()


if __name__ == "__main__":
    raise SystemExit(main())