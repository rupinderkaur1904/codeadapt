"""skill-map snapshot per content version

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-17 09:00:00.000000

Existing rows stay NULL here; Catalogue.sync fills in every version still in the
catalogue. Versions no longer in the catalogue keep NULL and contribute no skill
evidence (ADR-023, D4).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('problem_versions') as batch_op:
        batch_op.add_column(sa.Column('skill_map', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('problem_versions') as batch_op:
        batch_op.drop_column('skill_map')
