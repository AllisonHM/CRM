"""Adiciona índices para performance

Revision ID: 20260425_add_performance_indexes
Revises: 20260207_add_data_fechamento_and_tarefa
Create Date: 2026-04-25

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260425_add_performance_indexes'
down_revision = '20260207_add_data_fechamento_and_tarefa'
branch_labels = None
depends_on = None


def upgrade():
    """Adiciona índices em colunas mais consultadas"""
    
    # ===== CLIENTE =====
    # Índice em telefone (buscas frequentes)
    op.create_index('idx_cliente_telefone', 'cliente', ['telefone'])
    
    # Índice em email (buscas frequentes)
    op.create_index('idx_cliente_email', 'cliente', ['email'])
    
    # Índice em usuario_crm_id (filtro de tenant)
    op.create_index('idx_cliente_usuario_crm_id', 'cliente', ['usuario_crm_id'])
    
    # Índice em tipo_pessoa (filtros)
    op.create_index('idx_cliente_tipo_pessoa', 'cliente', ['tipo_pessoa'])
    
    # Índice composto para buscas comuns
    op.create_index(
        'idx_cliente_usuario_tipo',
        'cliente',
        ['usuario_crm_id', 'tipo_pessoa']
    )
    
    # ===== MESA_NEGOCIO =====
    # Índice em cliente_id (join frequente)
    op.create_index('idx_mesa_cliente_id', 'mesa_negocio', ['cliente_id'])
    
    # Índice em usuario_crm_id (filtro de tenant)
    op.create_index('idx_mesa_usuario_crm_id', 'mesa_negocio', ['usuario_crm_id'])
    
    # Índice em situacao (filtros e agregações)
    op.create_index('idx_mesa_situacao', 'mesa_negocio', ['situacao'])
    
    # Índice em data_registro (ordenação e filtros de período)
    op.create_index('idx_mesa_data_registro', 'mesa_negocio', ['data_registro'])
    
    # Índice composto para queries de dashboard
    op.create_index(
        'idx_mesa_usuario_situacao',
        'mesa_negocio',
        ['usuario_crm_id', 'situacao']
    )
    
    # Índice composto para relatórios por período
    op.create_index(
        'idx_mesa_usuario_data',
        'mesa_negocio',
        ['usuario_crm_id', 'data_registro']
    )
    
    # ===== OCORRENCIA =====
    # Índice em cliente_id
    op.create_index('idx_ocorrencia_cliente_id', 'ocorrencia', ['cliente_id'])
    
    # Índice em usuario_crm_id
    op.create_index('idx_ocorrencia_usuario_crm_id', 'ocorrencia', ['usuario_crm_id'])
    
    # Índice em status
    op.create_index('idx_ocorrencia_status', 'ocorrencia', ['status'])
    
    # Índice em data_registro
    op.create_index('idx_ocorrencia_data_registro', 'ocorrencia', ['data_registro'])
    
    # ===== WHATSAPP_MENSAGEM =====
    # Índice em numero (buscas de conversas)
    op.create_index('idx_wpp_numero', 'whatsapp_mensagem', ['numero'])
    
    # Índice em usuario_crm_id
    op.create_index('idx_wpp_usuario_crm_id', 'whatsapp_mensagem', ['usuario_crm_id'])
    
    # Índice em recebido_em (ordenação cronológica)
    op.create_index('idx_wpp_recebido_em', 'whatsapp_mensagem', ['recebido_em'])
    
    # Índice em remetente (filtro de mensagens pendentes)
    op.create_index('idx_wpp_remetente', 'whatsapp_mensagem', ['remetente'])
    
    # Índice composto para última mensagem de cada conversa
    op.create_index(
        'idx_wpp_usuario_numero_data',
        'whatsapp_mensagem',
        ['usuario_crm_id', 'numero', 'recebido_em']
    )
    
    # ===== PRODUTO =====
    # Índice em usuario_crm_id
    op.create_index('idx_produto_usuario_crm_id', 'produto', ['usuario_crm_id'])
    
    # Índice em nome (buscas)
    op.create_index('idx_produto_nome', 'produto', ['nome'])
    
    # ===== PLANNER_EVENTO =====
    # Índice em usuario_crm_id
    op.create_index('idx_planner_usuario_crm_id', 'planner_evento', ['usuario_crm_id'])
    
    # Índice em data (ordenação e filtros)
    op.create_index('idx_planner_data', 'planner_evento', ['data'])
    
    # Índice em data_hora (notificações)
    op.create_index('idx_planner_data_hora', 'planner_evento', ['data_hora'])
    
    # ===== TAREFA =====
    # Índice em usuario_crm_id
    op.create_index('idx_tarefa_usuario_crm_id', 'tarefa', ['usuario_crm_id'])
    
    # Índice em cliente_id
    op.create_index('idx_tarefa_cliente_id', 'tarefa', ['cliente_id'])
    
    # Índice em status
    op.create_index('idx_tarefa_status', 'tarefa', ['status'])
    
    # Índice em data_vencimento
    op.create_index('idx_tarefa_data_vencimento', 'tarefa', ['data_vencimento'])
    
    # Índice em lembrete_em (jobs de notificação)
    op.create_index('idx_tarefa_lembrete_em', 'tarefa', ['lembrete_em'])
    
    # Índice composto para tarefas pendentes com lembrete
    op.create_index(
        'idx_tarefa_lembrete_pendente',
        'tarefa',
        ['lembrete_em', 'lembrete_enviado', 'status']
    )
    
    # ===== USUARIO_CRM =====
    # Índice em email (login)
    op.create_index('idx_usuario_email', 'usuario_crm', ['email'])
    
    # Índice em tipo_usuario (filtros de permissão)
    op.create_index('idx_usuario_tipo', 'usuario_crm', ['tipo_usuario'])
    
    # Índice em usuario_pai_id (hierarquia)
    op.create_index('idx_usuario_pai_id', 'usuario_crm', ['usuario_pai_id'])
    
    # Índice em ativo (filtro de usuários ativos)
    op.create_index('idx_usuario_ativo', 'usuario_crm', ['ativo'])
    
    # Índice em reset_token (recuperação de senha)
    op.create_index('idx_usuario_reset_token', 'usuario_crm', ['reset_token'])
    
    # ===== DISPARO_WPP =====
    # Índice em usuario_crm_id
    op.create_index('idx_disparo_usuario_crm_id', 'disparo_wpp', ['usuario_crm_id'])
    
    # Índice em status (filtros)
    op.create_index('idx_disparo_status', 'disparo_wpp', ['status'])
    
    # Índice em criado_em (ordenação)
    op.create_index('idx_disparo_criado_em', 'disparo_wpp', ['criado_em'])
    
    # ===== CONVERSATION (Meta) =====
    # Índice em page_id
    op.create_index('idx_conversation_page_id', 'conversation', ['page_id'])
    
    # Índice em sender_id
    op.create_index('idx_conversation_sender_id', 'conversation', ['sender_id'])
    
    # Índice em updated_time
    op.create_index('idx_conversation_updated_time', 'conversation', ['updated_time'])
    
    print("✅ Índices de performance criados com sucesso!")


def downgrade():
    """Remove índices"""
    
    # CLIENTE
    op.drop_index('idx_cliente_telefone')
    op.drop_index('idx_cliente_email')
    op.drop_index('idx_cliente_usuario_crm_id')
    op.drop_index('idx_cliente_tipo_pessoa')
    op.drop_index('idx_cliente_usuario_tipo')
    
    # MESA_NEGOCIO
    op.drop_index('idx_mesa_cliente_id')
    op.drop_index('idx_mesa_usuario_crm_id')
    op.drop_index('idx_mesa_situacao')
    op.drop_index('idx_mesa_data_registro')
    op.drop_index('idx_mesa_usuario_situacao')
    op.drop_index('idx_mesa_usuario_data')
    
    # OCORRENCIA
    op.drop_index('idx_ocorrencia_cliente_id')
    op.drop_index('idx_ocorrencia_usuario_crm_id')
    op.drop_index('idx_ocorrencia_status')
    op.drop_index('idx_ocorrencia_data_registro')
    
    # WHATSAPP_MENSAGEM
    op.drop_index('idx_wpp_numero')
    op.drop_index('idx_wpp_usuario_crm_id')
    op.drop_index('idx_wpp_recebido_em')
    op.drop_index('idx_wpp_remetente')
    op.drop_index('idx_wpp_usuario_numero_data')
    
    # PRODUTO
    op.drop_index('idx_produto_usuario_crm_id')
    op.drop_index('idx_produto_nome')
    
    # PLANNER_EVENTO
    op.drop_index('idx_planner_usuario_crm_id')
    op.drop_index('idx_planner_data')
    op.drop_index('idx_planner_data_hora')
    
    # TAREFA
    op.drop_index('idx_tarefa_usuario_crm_id')
    op.drop_index('idx_tarefa_cliente_id')
    op.drop_index('idx_tarefa_status')
    op.drop_index('idx_tarefa_data_vencimento')
    op.drop_index('idx_tarefa_lembrete_em')
    op.drop_index('idx_tarefa_lembrete_pendente')
    
    # USUARIO_CRM
    op.drop_index('idx_usuario_email')
    op.drop_index('idx_usuario_tipo')
    op.drop_index('idx_usuario_pai_id')
    op.drop_index('idx_usuario_ativo')
    op.drop_index('idx_usuario_reset_token')
    
    # DISPARO_WPP
    op.drop_index('idx_disparo_usuario_crm_id')
    op.drop_index('idx_disparo_status')
    op.drop_index('idx_disparo_criado_em')
    
    # CONVERSATION
    op.drop_index('idx_conversation_page_id')
    op.drop_index('idx_conversation_sender_id')
    op.drop_index('idx_conversation_updated_time')
    
    print("✅ Índices removidos com sucesso!")
