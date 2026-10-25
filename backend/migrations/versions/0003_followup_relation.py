"""follow-up relation

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-15 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('followup_evaluations') as batch_op:
        batch_op.add_column(sa.Column('relation', sa.String(length=32), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('followup_evaluations') as batch_op:
        batch_op.drop_column('relation')
