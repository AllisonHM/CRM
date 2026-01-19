"""Adicionar tabelas ConfiguracaoUsuario e Parametrizacao

Revision ID: config_param_2026
Revises: 334998351db0
Create Date: 2026-01-18 15:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'config_param_2026'
down_revision = '334998351db0'
branch_labels = None
depends_on = None


def upgrade():
    # Criar tabela configuracao_usuario
    op.create_table('configuracao_usuario',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_crm_id', sa.Integer(), nullable=False),
        sa.Column('tema', sa.String(length=20), nullable=True),
        sa.Column('idioma', sa.String(length=10), nullable=True),
        sa.Column('notificacoes_email', sa.Boolean(), nullable=True),
        sa.Column('notificacoes_sistema', sa.Boolean(), nullable=True),
        sa.Column('data_atualizacao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_crm_id'], ['usuario_crm.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('usuario_crm_id')
    )
    
    # Criar tabela parametrizacao
    op.create_table('parametrizacao',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_crm_id', sa.Integer(), nullable=False),
        sa.Column('mensagem_boas_vindas', sa.Text(), nullable=True),
        sa.Column('mensagem_ausencia', sa.Text(), nullable=True),
        sa.Column('mensagem_encerramento', sa.Text(), nullable=True),
        sa.Column('mensagem_nps', sa.Text(), nullable=True),
        sa.Column('horario_atendimento_inicio', sa.Time(), nullable=True),
        sa.Column('horario_atendimento_fim', sa.Time(), nullable=True),
        sa.Column('resposta_automatica_ativa', sa.Boolean(), nullable=True),
        sa.Column('data_atualizacao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_crm_id'], ['usuario_crm.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('parametrizacao')
    op.drop_table('configuracao_usuario')
