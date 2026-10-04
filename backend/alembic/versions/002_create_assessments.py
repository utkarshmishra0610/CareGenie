"""create assessments table

Revision ID: 002_create_assessments
Revises: 001_initial_users
Create Date: 2026-09-20 20:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_create_assessments'
down_revision: Union[str, None] = '001_initial_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'assessments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('assessment_date', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('symptoms', sa.JSON(), nullable=False),
        sa.Column('duration', sa.String(length=100), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=True),
        sa.Column('predicted_condition', sa.String(length=200), nullable=True),
        sa.Column('risk_level', sa.String(length=50), nullable=False, server_default='Preliminary'),
        sa.Column('ai_summary', sa.Text(), nullable=True),
        sa.Column('suggested_specialty', sa.String(length=150), nullable=True),
        sa.Column('healthcare_searches', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessments_id'), 'assessments', ['id'], unique=False)
    op.create_index(op.f('ix_assessments_user_id'), 'assessments', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_assessments_user_id'), table_name='assessments')
    op.drop_index(op.f('ix_assessments_id'), table_name='assessments')
    op.drop_table('assessments')
