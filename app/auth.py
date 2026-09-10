"""Authentication, password security, session management and Bearer token verification."""

import hashlib
import hmac
import os
import secrets
from typing import Optional, Tuple
from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.database import get_db_connection, get_setting

bearer_scheme = HTTPBearer(auto_error=False)


def generate_salt(length: int = 16) -> bytes:
    """Generate cryptographically secure random bytes for salting."""
    return os.urandom(length)


def hash_password(password: str, salt: Optional[bytes] = None) -> Tuple[bytes, bytes]:
    """Hash a password using PBKDF2 HMAC SHA-256 with 600,000 iterations."""
    if salt is None:
        salt = generate_salt()
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
    return pwd_hash, salt


def verify_password(password: str, salt: bytes, expected_hash: bytes) -> bool:
    """Safely verify a password against its salt and PBKDF2 hash."""
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
    return hmac.compare_digest(pwd_hash, expected_hash)


def is_authenticated(request: Request) -> bool:
    """Check if the current session has authenticated status."""
    return bool(request.session.get("authenticated"))


def login_required(request: Request) -> None:
    """FastAPI dependency to ensure the user is logged in."""
    if not is_authenticated(request):
        if request.url.path.startswith("/api/"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": f"/login?next={request.url.path}"},
        )


def admin_required(request: Request) -> None:
    """FastAPI dependency to ensure the current user has the 'admin' role."""
    login_required(request)
    if request.session.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )


def verify_bearer_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> str:
    """Verify that a Bearer token matches the active bridge_api_token in the database."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Bearer authentication header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expected_token = get_setting("bridge_api_token")
    if not expected_token:
        # Fallback to generating a default token if somehow unset
        expected_token = secrets.token_hex(24)
        from app.database import set_setting
        set_setting("bridge_api_token", expected_token)

    if not hmac.compare_digest(credentials.credentials, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Bearer API token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return credentials.credentials


def get_current_user(request: Request) -> Optional[dict]:
    """Retrieve the current logged-in user dict from the active session."""
    if not is_authenticated(request):
        return None
    username = request.session.get("username")
    if not username:
        return None
    from app.database import get_user_by_username
    row = get_user_by_username(username)
    return dict(row) if row else None

