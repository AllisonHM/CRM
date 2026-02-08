"""add data_fechamento and tarefa

Revision ID: 20260207_add_data_fechamento_and_tarefa
Revises: config_param_2026_adicionar_config_param
Create Date: 2026-02-07
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260207_add_data_fechamento_and_tarefa'
down_revision = 'config_param_2026_adicionar_config_param'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('mesa_negocio', sa.Column('data_fechamento', sa.Date(), nullable=True))

    op.create_table(
        'tarefa',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('usuario_crm_id', sa.Integer(), sa.ForeignKey('usuario_crm.id'), nullable=True),
        sa.Column('cliente_id', sa.Integer(), sa.ForeignKey('cliente.id'), nullable=True),
        sa.Column('mesa_negocio_id', sa.Integer(), sa.ForeignKey('mesa_negocio.id'), nullable=True),
        sa.Column('titulo', sa.String(length=200), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('prioridade', sa.String(length=20), nullable=False, server_default='Normal'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='Pendente'),
        sa.Column('data_vencimento', sa.Date(), nullable=True),
        sa.Column('hora_vencimento', sa.Time(), nullable=True),
        sa.Column('lembrete_em', sa.DateTime(), nullable=True),
        sa.Column('lembrete_enviado', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('concluido_em', sa.DateTime(), nullable=True)
    )


def downgrade():
    op.drop_table('tarefa')
    op.drop_column('mesa_negocio', 'data_fechamento')
