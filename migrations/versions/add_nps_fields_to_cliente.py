"""add_nps_fields_to_cliente

Revision ID: add_nps_20260106
Revises: 0e8796ecb99d
Create Date: 2026-01-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_nps_20260106'
down_revision = '0e8796ecb99d'
branch_labels = None
depends_on = None


def upgrade():
    # Adicionar campos de NPS na tabela cliente
    op.add_column('cliente', sa.Column('nps_nota', sa.Integer(), nullable=True))
    op.add_column('cliente', sa.Column('nps_data', sa.DateTime(), nullable=True))
    op.add_column('cliente', sa.Column('nps_comentario', sa.Text(), nullable=True))
    op.add_column('cliente', sa.Column('aguardando_nps', sa.Boolean(), nullable=True))


def downgrade():
    # Remover campos de NPS
    op.drop_column('cliente', 'aguardando_nps')
    op.drop_column('cliente', 'nps_comentario')
    op.drop_column('cliente', 'nps_data')
    op.drop_column('cliente', 'nps_nota')
