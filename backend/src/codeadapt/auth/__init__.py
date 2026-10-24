"""Accounts, login sessions and the audit log (ADR-029, security.md §4).

Passwords are hashed with Argon2id. A login creates a server-side session: the browser
holds a random token in an HTTP-only cookie and the database holds only its SHA-256, so a
database leak does not reveal live session tokens. Each session also carries a CSRF token
that state-changing requests must echo in a header. There is no self-registration: an
operator creates accounts with `codeadapt-admin`.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from codeadapt.db.models import AuditEvent, AuthSession, User, utcnow
from codeadapt.db.session import as_utc

# argon2-cffi's defaults are Argon2id with RFC 9106's low-memory profile.
_HASHER = PasswordHasher()
# Verified against when the username is unknown, so a miss costs the same time as a hit.
_DUMMY_HASH = _HASHER.hash(secrets.token_hex(16))
MIN_PASSWORD_LENGTH = 12


class AuditKind:
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    LOGIN_THROTTLED = "login_throttled"
    LOGOUT = "logout"
    RESEARCH_ACCESS = "research_access"
    STAFF_VIEW_SUBMISSION = "staff_view_submission"
    ACCOUNT_CREATED = "account_created"
    PASSWORD_SET = "password_set"  # noqa: S105 - an event name, not a password
    ACCOUNT_DISABLED = "account_disabled"


def hash_password(password: str) -> str:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"password must have at least {MIN_PASSWORD_LENGTH} characters")
    return _HASHER.hash(password)


def verify_password(stored: str | None, password: str) -> bool:
    try:
        return _HASHER.verify(stored or _DUMMY_HASH, password) and stored is not None
    except (VerificationError, InvalidHashError):
        return False


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def authenticate(session: Session, username: str, password: str) -> User | None:
    user = session.scalar(select(User).where(User.username == username))
    ok = verify_password(user.password_hash if user else None, password)
    if user is None or not ok or user.disabled:
        return None
    if user.password_hash and _HASHER.check_needs_rehash(user.password_hash):
        user.password_hash = _HASHER.hash(password)
    return user


def start_session(session: Session, user: User, ttl: timedelta) -> tuple[str, AuthSession]:
    """Create a session; returns the cookie token (shown once, never stored) and the row."""
    token = secrets.token_urlsafe(32)
    row = AuthSession(
        token_hash=_digest(token),
        user_id=user.id,
        csrf_token=secrets.token_urlsafe(32),
        expires_at=utcnow() + ttl,
    )
    session.add(row)
    return token, row


def resolve_session(session: Session, token: str) -> tuple[AuthSession, User] | None:
    row = session.get(AuthSession, _digest(token))
    if row is None or row.revoked_at is not None or as_utc(row.expires_at) <= utcnow():
        return None
    user = session.get(User, row.user_id)
    if user is None or user.disabled:
        return None
    return row, user


def revoke_session(row: AuthSession) -> None:
    row.revoked_at = utcnow()


def revoke_all(session: Session, user: User) -> None:
    for row in session.scalars(
        select(AuthSession).where(AuthSession.user_id == user.id, AuthSession.revoked_at.is_(None))
    ):
        row.revoked_at = utcnow()


def csrf_matches(row: AuthSession, header: str | None) -> bool:
    return header is not None and secrets.compare_digest(row.csrf_token, header)


def audit(
    session: Session,
    kind: str,
    *,
    username: str,
    client: str,
    user: User | None = None,
    target: str = "",
) -> None:
    session.add(
        AuditEvent(
            kind=kind,
            user_id=user.id if user else None,
            username=username[:64],
            client=client[:64],
            target=target[:255],
        )
    )


def recent_failures(session: Session, username: str, client: str, since: datetime) -> int:
    """Failed logins for this username, or from this client, since ``since``."""
    return (
        session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.kind == AuditKind.LOGIN_FAILED,
                AuditEvent.at >= since,
                (AuditEvent.username == username[:64]) | (AuditEvent.client == client[:64]),
            )
        )
        or 0
    )
