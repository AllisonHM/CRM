"""Adiciona UsuarioCRM e campos para multi-instância

Revision ID: add_usuario_crm_multitenancy
Revises: 
Create Date: 2026-01-08

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_usuario_crm_multitenancy'
down_revision = 'add_observacoes_cliente'  # Última migração
branch_labels = None
depends_on = None


def upgrade():
    # Criar tabela usuario_crm
    op.create_table(
        'usuario_crm',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=200), nullable=False),
        sa.Column('numero_whatsapp', sa.String(length=50), nullable=False),
        sa.Column('api_token', sa.String(length=255), nullable=True),
        sa.Column('dias_quarentena_nps', sa.Integer(), nullable=True, server_default='30'),
        sa.Column('ativo', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('data_cadastro', sa.DateTime(), nullable=True, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('numero_whatsapp')
    )
    
    # Adicionar coluna usuario_crm_id na tabela cliente
    op.add_column('cliente', sa.Column('usuario_crm_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_cliente_usuario_crm', 'cliente', 'usuario_crm', ['usuario_crm_id'], ['id'])
    
    # Adicionar coluna data_ultimo_nps_envio na tabela cliente
    op.add_column('cliente', sa.Column('data_ultimo_nps_envio', sa.DateTime(), nullable=True))
    
    # Adicionar coluna usuario_crm_id na tabela mesa_negocio
    op.add_column('mesa_negocio', sa.Column('usuario_crm_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_mesa_usuario_crm', 'mesa_negocio', 'usuario_crm', ['usuario_crm_id'], ['id'])
    
    # Adicionar coluna usuario_crm_id na tabela ocorrencia
    op.add_column('ocorrencia', sa.Column('usuario_crm_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_ocorrencia_usuario_crm', 'ocorrencia', 'usuario_crm', ['usuario_crm_id'], ['id'])
    
    # Adicionar coluna usuario_crm_id na tabela whatsapp_mensagem
    op.add_column('whatsapp_mensagem', sa.Column('usuario_crm_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_whatsapp_usuario_crm', 'whatsapp_mensagem', 'usuario_crm', ['usuario_crm_id'], ['id'])
    
    # Adicionar coluna usuario_crm_id na tabela produto
    op.add_column('produto', sa.Column('usuario_crm_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_produto_usuario_crm', 'produto', 'usuario_crm', ['usuario_crm_id'], ['id'])
    
    # Adicionar coluna usuario_crm_id na tabela planner_evento
    op.add_column('planner_evento', sa.Column('usuario_crm_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_planner_usuario_crm', 'planner_evento', 'usuario_crm', ['usuario_crm_id'], ['id'])


def downgrade():
    # Remover foreign keys e colunas na ordem inversa
    op.drop_constraint('fk_planner_usuario_crm', 'planner_evento', type_='foreignkey')
    op.drop_column('planner_evento', 'usuario_crm_id')
    
    op.drop_constraint('fk_produto_usuario_crm', 'produto', type_='foreignkey')
    op.drop_column('produto', 'usuario_crm_id')
    
    op.drop_constraint('fk_whatsapp_usuario_crm', 'whatsapp_mensagem', type_='foreignkey')
    op.drop_column('whatsapp_mensagem', 'usuario_crm_id')
    
    op.drop_constraint('fk_ocorrencia_usuario_crm', 'ocorrencia', type_='foreignkey')
    op.drop_column('ocorrencia', 'usuario_crm_id')
    
    op.drop_constraint('fk_mesa_usuario_crm', 'mesa_negocio', type_='foreignkey')
    op.drop_column('mesa_negocio', 'usuario_crm_id')
    
    op.drop_column('cliente', 'data_ultimo_nps_envio')
    
    op.drop_constraint('fk_cliente_usuario_crm', 'cliente', type_='foreignkey')
    op.drop_column('cliente', 'usuario_crm_id')
    
    op.drop_table('usuario_crm')
