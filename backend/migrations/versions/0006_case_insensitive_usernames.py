"""case-insensitive usernames

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-06 18:00:00.000000

ADR-041: a unique index on lower(username), so names that differ only in case cannot
coexist. No row is changed. If existing names already collide, the upgrade stops and lists
them; an operator resolves them (rename or disable and rename) and runs it again.
Downgrade drops the index. SQLite (3.9+) and PostgreSQL both support expression indexes.

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: Union[str, Sequence[str], None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    clashes = (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT lower(username) AS name, count(*) AS n FROM users "
                "GROUP BY lower(username) HAVING count(*) > 1 ORDER BY lower(username)"
            )
        )
        .fetchall()
    )
    if clashes:
        listed = ", ".join(f"{name!r} ({n} accounts)" for name, n in clashes)
        raise RuntimeError(
            "cannot make usernames case-insensitive: these names collide ignoring case: "
            f"{listed}. Rename all but one of each (codeadapt-admin), then upgrade again."
        )
    op.create_index("ux_users_username_lower", "users", [sa.text("lower(username)")], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ux_users_username_lower", table_name="users")
