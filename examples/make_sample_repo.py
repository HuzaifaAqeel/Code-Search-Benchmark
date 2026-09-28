#!/usr/bin/env python3
"""Build a tiny sample Git repository with realistic commit history.

Used for the offline demo: `benchmark generate` mines ground-truth test cases
from this repo's commit history, and `benchmark evaluate` scores the keyword
retrieval agent against them. Idempotent — rebuilds from scratch each run.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_repo")


def sh(cmd, cwd=ROOT):
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


FILES = {
    "app.py": 'from auth import login\n\nprint("app started")\n',
    "README.md": "# Sample App\n\nA tiny demo project.\n",
}


def write(name, content):
    path = os.path.join(ROOT, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(content)


COMMITS = [
    ("Initial commit", ["app.py", "README.md"], {}),
    (
        "Add user authentication module",
        ["auth.py", "app.py", "tests/test_auth.py"],
        {
            "auth.py": 'TOKEN_TTL = 3600\n\n\ndef login(user, password):\n    """Authenticate a user and return a session token."""\n    return f"token-{user}"\n\n\ndef logout(token):\n    """Invalidate a session token."""\n    return True\n',
            "app.py": 'from auth import login, logout\n\nprint("app started")\n',
            "tests/test_auth.py": 'from auth import login\n\n\ndef test_login():\n    assert login("ali", "pw").startswith("token-")\n',
        },
    ),
    (
        "Fix login token expiry bug",
        ["auth.py", "config.py"],
        {
            "auth.py": '\n\ndef refresh_token(token):\n    """Refresh an expiring session token."""\n    return token + "-refreshed"\n',
            "config.py": 'TOKEN_TTL = 7200  # bumped after expiry bug\n',
        },
    ),
    (
        "Add payment processing",
        ["payments.py", "app.py", "tests/test_payments.py"],
        {
            "payments.py": 'def charge(card, amount):\n    """Charge a credit card."""\n    return {"status": "ok", "amount": amount}\n\n\ndef refund(txn_id):\n    """Refund a transaction."""\n    return {"status": "refunded", "txn": txn_id}\n',
            "app.py": '\nfrom payments import charge\n',
            "tests/test_payments.py": 'from payments import charge\n\n\ndef test_charge():\n    assert charge("4242", 100)["status"] == "ok"\n',
        },
    ),
    (
        "Refactor database connection pooling",
        ["db.py", "app.py", "config.py"],
        {
            "db.py": 'POOL_SIZE = 10\n\n\ndef get_connection():\n    """Get a pooled database connection."""\n    return f"conn-pool-{POOL_SIZE}"\n',
            "app.py": '\nfrom db import get_connection\n',
            "config.py": '\nDB_URL = "sqlite:///app.db"\n',
        },
    ),
    (
        "Add rate limiting middleware",
        ["middleware.py", "app.py"],
        {
            "middleware.py": 'RATE_LIMIT = 100\n\n\ndef rate_limit(request):\n    """Reject requests over the per-minute rate limit."""\n    return request.get("count", 0) < RATE_LIMIT\n',
            "app.py": '\nfrom middleware import rate_limit\n',
        },
    ),
    (
        "Fix null pointer in user profile",
        ["profile.py", "app.py"],
        {
            "profile.py": 'def get_display_name(user):\n    """Return display name, safe when user is None."""\n    if user is None:\n        return "Guest"\n    return user.get("name", "Guest")\n',
            "app.py": '\nfrom profile import get_display_name\n',
        },
    ),
    (
        "Add email notifications",
        ["notify.py", "app.py", "tests/test_notify.py"],
        {
            "notify.py": 'def send_email(to, subject, body):\n    """Send a notification email."""\n    return {"to": to, "subject": subject, "sent": True}\n',
            "app.py": '\nfrom notify import send_email\n',
            "tests/test_notify.py": 'from notify import send_email\n\n\ndef test_send_email():\n    assert send_email("a@b.c", "hi", "yo")["sent"]\n',
        },
    ),
]


def main():
    if os.path.exists(ROOT):
        shutil.rmtree(ROOT)
    os.makedirs(ROOT)
    sh(["git", "init", "-q"])
    sh(["git", "config", "user.email", "demo@example.com"])
    sh(["git", "config", "user.name", "Demo"])
    for name, content in FILES.items():
        path = os.path.join(ROOT, name)
        with open(path, "w") as f:
            f.write(content)
    sh(["git", "add", "-A"])
    sh(["git", "commit", "-q", "-m", "Initial commit"])
    for message, touched, additions in COMMITS[1:]:
        for fname, content in additions.items():
            write(fname, content)
        sh(["git", "add", "-A"])
        sh(["git", "commit", "-q", "-m", message])
    n = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"], cwd=ROOT, capture_output=True, text=True
    ).stdout.strip()
    print(f"Sample repo built at {ROOT} ({n} commits)")


if __name__ == "__main__":
    sys.exit(main())
