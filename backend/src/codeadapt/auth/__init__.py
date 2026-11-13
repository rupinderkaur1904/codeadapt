"""Accounts, login sessions and the audit log (ADR-029, security.md §4).

Passwords are hashed with Argon2id. A login creates a server-side session: the browser
holds a random token in an HTTP-only cookie and the database holds only its SHA-256, so a
database leak does not reveal live session tokens. Each session also carries a CSRF token
that state-changing requests must echo in a header. An operator creates accounts with
`codeadapt-admin`; when the deployment turns it on (ADR-044), a person holding a
researcher-issued invite code may also create a student account of data class `dev`.
"""

from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from codeadapt.db.models import AuditEvent, AuthSession, InviteCode, User, utcnow
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
    PASSWORD_CHANGED = "password_changed"  # noqa: S105 - self-service change (ADR-041)
    PASSWORD_CHANGE_FAILED = "password_change_failed"  # noqa: S105 - wrong current password
    ACCOUNT_DISABLED = "account_disabled"
    ACCOUNT_ERASED = "account_erased"  # participant withdrawal; the name is not kept
    # ADR-044: self-service sign-up with an invite code.
    SIGNUP = "signup"
    SIGNUP_FAILED = "signup_failed"  # wrong, expired, used-up or revoked invite code
    SIGNUP_THROTTLED = "signup_throttled"
    INVITE_CREATED = "invite_created"
    INVITE_REVOKED = "invite_revoked"


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


def find_user(session: Session, username: str) -> User | None:
    """The account for ``username``, ignoring case (ADR-041). The database compares with its
    own ``lower()``, the same function its unique index uses, so lookup and uniqueness agree."""
    return session.scalar(select(User).where(func.lower(User.username) == func.lower(username)))


def authenticate(session: Session, username: str, password: str) -> User | None:
    user = find_user(session, username)
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


def revoke_token(session: Session, token: str | None) -> None:
    """End the session behind a cookie token, if it is live (rotation at login, ADR-041)."""
    if not token:
        return
    row = session.get(AuthSession, _digest(token))
    if row is not None and row.revoked_at is None:
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
    """Failed logins and failed password changes for this username (ignoring case, so a
    change of case does not reset the count) or from this client, since ``since``."""
    return (
        session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.kind.in_((AuditKind.LOGIN_FAILED, AuditKind.PASSWORD_CHANGE_FAILED)),
                AuditEvent.at >= since,
                (func.lower(AuditEvent.username) == func.lower(username[:64]))
                | (AuditEvent.client == client[:64]),
            )
        )
        or 0
    )


# ---------------------------------------------------------------- invite codes (ADR-044)

# No 0/O, 1/I/L: codes are read aloud and copied from a slide. 31 symbols, 12 of them
# give about 59 bits; with the sign-up throttle that is far beyond guessing.
_CODE_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
_CODE_LENGTH = 12
MAX_INVITE_USES = 500
MAX_INVITE_DAYS = 90
# Sign-up usernames: 3-32 letters, digits, dot, dash, underscore, starting with a letter or
# digit. Operator-created names (codeadapt-admin) keep the wider 64-character rule.
_SIGNUP_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{2,31}")
# The development stub's fixed accounts (api/app.py) and names a person could mistake for
# staff are never available through sign-up.
_RESERVED_PREFIXES = ("dev-",)
_RESERVED_NAMES = frozenset({"admin", "administrator", "root", "researcher", "codeadapt"})


def normalise_invite_code(code: str) -> str:
    return "".join(ch for ch in code.upper() if ch not in " -")


def format_invite_code(code: str) -> str:
    return "-".join(code[i : i + 4] for i in range(0, len(code), 4))


def create_invite(
    session: Session, label: str, max_uses: int, valid_for: timedelta
) -> tuple[str, InviteCode]:
    """A new code; returns it formatted for people (shown once, never stored) and the row."""
    if not 1 <= max_uses <= MAX_INVITE_USES:
        raise ValueError(f"max uses must be between 1 and {MAX_INVITE_USES}")
    if not timedelta(0) < valid_for <= timedelta(days=MAX_INVITE_DAYS):
        raise ValueError(f"an invite code may be valid for at most {MAX_INVITE_DAYS} days")
    label = label.strip()
    if not label or len(label) > 64:
        raise ValueError("label must have 1-64 characters")
    code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
    row = InviteCode(
        code_hash=_digest(code),
        label=label,
        expires_at=utcnow() + valid_for,
        max_uses=max_uses,
        uses=0,
    )
    session.add(row)
    return format_invite_code(code), row


def consume_invite(session: Session, code: str) -> InviteCode | None:
    """Spend one use of a live code, atomically: the conditional UPDATE means two sign-ups
    racing for a code's last use cannot both win. The use is returned if the caller's
    transaction rolls back. Returns the code's row, or None for a wrong, expired, used-up or
    revoked code (the caller cannot tell which, and neither can the person signing up)."""
    digest = _digest(normalise_invite_code(code))
    now = utcnow()
    result = session.execute(
        update(InviteCode)
        .where(
            InviteCode.code_hash == digest,
            InviteCode.revoked_at.is_(None),
            InviteCode.expires_at > now,
            InviteCode.uses < InviteCode.max_uses,
        )
        .values(uses=InviteCode.uses + 1)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:  # type: ignore[attr-defined]
        return None
    return session.scalar(select(InviteCode).where(InviteCode.code_hash == digest))


def signup_username_problem(username: str) -> str | None:
    """Why ``username`` cannot be chosen at sign-up, or None if it can."""
    if not _SIGNUP_NAME.fullmatch(username):
        return (
            "Use 3-32 letters, digits, dots, dashes or underscores, starting with a letter or digit"
        )
    lowered = username.lower()
    if lowered in _RESERVED_NAMES or lowered.startswith(_RESERVED_PREFIXES):
        return "This username is reserved"
    return None


def recent_client_events(
    session: Session, kinds: tuple[str, ...], client: str, since: datetime
) -> int:
    """Audit events of ``kinds`` from one client address since ``since`` (sign-up limits)."""
    return (
        session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(
                AuditEvent.kind.in_(kinds),
                AuditEvent.at >= since,
                AuditEvent.client == client[:64],
            )
        )
        or 0
    )


def recent_events(session: Session, kinds: tuple[str, ...], since: datetime) -> int:
    """Audit events of ``kinds`` from every client since ``since`` (the daily sign-up cap)."""
    return (
        session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.kind.in_(kinds), AuditEvent.at >= since)
        )
        or 0
    )
