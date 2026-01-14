-- =====================================================
-- MIGRAÇÃO DO CRM PARA MULTI-TENANT COM RLS
-- Execute este script no banco de dados existente
-- =====================================================

-- =====================================================
-- PARTE 1: CRIAR FUNÇÃO PARA PEGAR TENANT_ID
-- =====================================================

CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS INTEGER AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_tenant', true), '')::INTEGER;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- PARTE 2: RENOMEAR usuario_crm_id PARA tenant_id
-- =====================================================

-- Já existe usuario_crm_id que funciona como tenant_id
-- Vamos apenas criar índices otimizados

-- Cliente
CREATE INDEX IF NOT EXISTS idx_cliente_tenant ON cliente(usuario_crm_id) WHERE usuario_crm_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_cliente_tenant_nome ON cliente(usuario_crm_id, nome);

-- MesaNegocio
ALTER TABLE mesa_negocio ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
UPDATE mesa_negocio SET usuario_crm_id = (SELECT usuario_crm_id FROM cliente WHERE cliente.id = mesa_negocio.cliente_id) WHERE usuario_crm_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_mesa_tenant ON mesa_negocio(usuario_crm_id);

-- Ocorrencia
ALTER TABLE ocorrencia ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
UPDATE ocorrencia SET usuario_crm_id = (SELECT usuario_crm_id FROM cliente WHERE cliente.id = ocorrencia.cliente_id) WHERE usuario_crm_id IS NULL;
CREATE INDEX IF NOT EXISTS idx_ocorrencia_tenant ON ocorrencia(usuario_crm_id);

-- WhatsAppMensagem
ALTER TABLE whatsapp_mensagem ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
CREATE INDEX IF NOT EXISTS idx_whatsapp_tenant ON whatsapp_mensagem(usuario_crm_id);

-- Produto
ALTER TABLE produto ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
CREATE INDEX IF NOT EXISTS idx_produto_tenant ON produto(usuario_crm_id);

-- PlannerEvento
ALTER TABLE planner_evento ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
CREATE INDEX IF NOT EXISTS idx_planner_tenant ON planner_evento(usuario_crm_id);

-- ChatbotRegra
ALTER TABLE chatbot_regra ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
CREATE INDEX IF NOT EXISTS idx_chatbot_tenant ON chatbot_regra(usuario_crm_id);

-- Movimentacao
ALTER TABLE movimentacao ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
CREATE INDEX IF NOT EXISTS idx_movimentacao_tenant ON movimentacao(usuario_crm_id);

-- =====================================================
-- PARTE 3: CRIAR ROLES DE APLICAÇÃO
-- =====================================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user LOGIN PASSWORD 'crm_app_user_2026!';
    END IF;
END
$$;

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_admin') THEN
        CREATE ROLE app_admin LOGIN PASSWORD 'crm_app_admin_2026!';
    END IF;
END
$$;

-- Permissões
GRANT CONNECT ON DATABASE crm TO app_user, app_admin;
GRANT USAGE ON SCHEMA public TO app_user, app_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user, app_admin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user, app_admin;

-- =====================================================
-- PARTE 4: ATIVAR RLS NAS TABELAS
-- =====================================================

-- Cliente
ALTER TABLE cliente ENABLE ROW LEVEL SECURITY;
ALTER TABLE cliente FORCE ROW LEVEL SECURITY;

-- MesaNegocio
ALTER TABLE mesa_negocio ENABLE ROW LEVEL SECURITY;
ALTER TABLE mesa_negocio FORCE ROW LEVEL SECURITY;

-- Ocorrencia
ALTER TABLE ocorrencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE ocorrencia FORCE ROW LEVEL SECURITY;

-- WhatsAppMensagem
ALTER TABLE whatsapp_mensagem ENABLE ROW LEVEL SECURITY;
ALTER TABLE whatsapp_mensagem FORCE ROW LEVEL SECURITY;

-- Produto
ALTER TABLE produto ENABLE ROW LEVEL SECURITY;
ALTER TABLE produto FORCE ROW LEVEL SECURITY;

-- PlannerEvento
ALTER TABLE planner_evento ENABLE ROW LEVEL SECURITY;
ALTER TABLE planner_evento FORCE ROW LEVEL SECURITY;

-- ChatbotRegra
ALTER TABLE chatbot_regra ENABLE ROW LEVEL SECURITY;
ALTER TABLE chatbot_regra FORCE ROW LEVEL SECURITY;

-- Movimentacao
ALTER TABLE movimentacao ENABLE ROW LEVEL SECURITY;
ALTER TABLE movimentacao FORCE ROW LEVEL SECURITY;

-- =====================================================
-- PARTE 5: CRIAR POLÍTICAS RLS
-- =====================================================

-- ========== CLIENTE ==========
DROP POLICY IF EXISTS policy_cliente_select ON cliente;
CREATE POLICY policy_cliente_select ON cliente
    FOR SELECT
    USING (usuario_crm_id = current_tenant_id() OR usuario_crm_id IS NULL);

DROP POLICY IF EXISTS policy_cliente_insert ON cliente;
CREATE POLICY policy_cliente_insert ON cliente
    FOR INSERT
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_cliente_update ON cliente;
CREATE POLICY policy_cliente_update ON cliente
    FOR UPDATE
    USING (usuario_crm_id = current_tenant_id())
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_cliente_delete ON cliente;
CREATE POLICY policy_cliente_delete ON cliente
    FOR DELETE
    USING (usuario_crm_id = current_tenant_id());

-- ========== MESA_NEGOCIO ==========
DROP POLICY IF EXISTS policy_mesa_select ON mesa_negocio;
CREATE POLICY policy_mesa_select ON mesa_negocio
    FOR SELECT
    USING (usuario_crm_id = current_tenant_id() OR usuario_crm_id IS NULL);

DROP POLICY IF EXISTS policy_mesa_insert ON mesa_negocio;
CREATE POLICY policy_mesa_insert ON mesa_negocio
    FOR INSERT
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_mesa_update ON mesa_negocio;
CREATE POLICY policy_mesa_update ON mesa_negocio
    FOR UPDATE
    USING (usuario_crm_id = current_tenant_id())
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_mesa_delete ON mesa_negocio;
CREATE POLICY policy_mesa_delete ON mesa_negocio
    FOR DELETE
    USING (usuario_crm_id = current_tenant_id());

-- ========== OCORRENCIA ==========
DROP POLICY IF EXISTS policy_ocorrencia_select ON ocorrencia;
CREATE POLICY policy_ocorrencia_select ON ocorrencia
    FOR SELECT
    USING (usuario_crm_id = current_tenant_id() OR usuario_crm_id IS NULL);

DROP POLICY IF EXISTS policy_ocorrencia_insert ON ocorrencia;
CREATE POLICY policy_ocorrencia_insert ON ocorrencia
    FOR INSERT
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_ocorrencia_update ON ocorrencia;
CREATE POLICY policy_ocorrencia_update ON ocorrencia
    FOR UPDATE
    USING (usuario_crm_id = current_tenant_id())
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_ocorrencia_delete ON ocorrencia;
CREATE POLICY policy_ocorrencia_delete ON ocorrencia
    FOR DELETE
    USING (usuario_crm_id = current_tenant_id());

-- ========== WHATSAPP_MENSAGEM ==========
DROP POLICY IF EXISTS policy_whatsapp_select ON whatsapp_mensagem;
CREATE POLICY policy_whatsapp_select ON whatsapp_mensagem
    FOR SELECT
    USING (usuario_crm_id = current_tenant_id() OR usuario_crm_id IS NULL);

DROP POLICY IF EXISTS policy_whatsapp_insert ON whatsapp_mensagem;
CREATE POLICY policy_whatsapp_insert ON whatsapp_mensagem
    FOR INSERT
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_whatsapp_update ON whatsapp_mensagem;
CREATE POLICY policy_whatsapp_update ON whatsapp_mensagem
    FOR UPDATE
    USING (usuario_crm_id = current_tenant_id())
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_whatsapp_delete ON whatsapp_mensagem;
CREATE POLICY policy_whatsapp_delete ON whatsapp_mensagem
    FOR DELETE
    USING (usuario_crm_id = current_tenant_id());

-- ========== PRODUTO ==========
DROP POLICY IF EXISTS policy_produto_select ON produto;
CREATE POLICY policy_produto_select ON produto
    FOR SELECT
    USING (usuario_crm_id = current_tenant_id() OR usuario_crm_id IS NULL);

DROP POLICY IF EXISTS policy_produto_insert ON produto;
CREATE POLICY policy_produto_insert ON produto
    FOR INSERT
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_produto_update ON produto;
CREATE POLICY policy_produto_update ON produto
    FOR UPDATE
    USING (usuario_crm_id = current_tenant_id())
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_produto_delete ON produto;
CREATE POLICY policy_produto_delete ON produto
    FOR DELETE
    USING (usuario_crm_id = current_tenant_id());

-- ========== PLANNER_EVENTO ==========
DROP POLICY IF EXISTS policy_planner_select ON planner_evento;
CREATE POLICY policy_planner_select ON planner_evento
    FOR SELECT
    USING (usuario_crm_id = current_tenant_id() OR usuario_crm_id IS NULL);

DROP POLICY IF EXISTS policy_planner_insert ON planner_evento;
CREATE POLICY policy_planner_insert ON planner_evento
    FOR INSERT
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_planner_update ON planner_evento;
CREATE POLICY policy_planner_update ON planner_evento
    FOR UPDATE
    USING (usuario_crm_id = current_tenant_id())
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_planner_delete ON planner_evento;
CREATE POLICY policy_planner_delete ON planner_evento
    FOR DELETE
    USING (usuario_crm_id = current_tenant_id());

-- ========== CHATBOT_REGRA ==========
DROP POLICY IF EXISTS policy_chatbot_select ON chatbot_regra;
CREATE POLICY policy_chatbot_select ON chatbot_regra
    FOR SELECT
    USING (usuario_crm_id = current_tenant_id() OR usuario_crm_id IS NULL);

DROP POLICY IF EXISTS policy_chatbot_insert ON chatbot_regra;
CREATE POLICY policy_chatbot_insert ON chatbot_regra
    FOR INSERT
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_chatbot_update ON chatbot_regra;
CREATE POLICY policy_chatbot_update ON chatbot_regra
    FOR UPDATE
    USING (usuario_crm_id = current_tenant_id())
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_chatbot_delete ON chatbot_regra;
CREATE POLICY policy_chatbot_delete ON chatbot_regra
    FOR DELETE
    USING (usuario_crm_id = current_tenant_id());

-- ========== MOVIMENTACAO ==========
DROP POLICY IF EXISTS policy_movimentacao_select ON movimentacao;
CREATE POLICY policy_movimentacao_select ON movimentacao
    FOR SELECT
    USING (usuario_crm_id = current_tenant_id() OR usuario_crm_id IS NULL);

DROP POLICY IF EXISTS policy_movimentacao_insert ON movimentacao;
CREATE POLICY policy_movimentacao_insert ON movimentacao
    FOR INSERT
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_movimentacao_update ON movimentacao;
CREATE POLICY policy_movimentacao_update ON movimentacao
    FOR UPDATE
    USING (usuario_crm_id = current_tenant_id())
    WITH CHECK (usuario_crm_id = current_tenant_id());

DROP POLICY IF EXISTS policy_movimentacao_delete ON movimentacao;
CREATE POLICY policy_movimentacao_delete ON movimentacao
    FOR DELETE
    USING (usuario_crm_id = current_tenant_id());

-- =====================================================
-- PARTE 6: VERIFICAÇÃO
-- =====================================================

-- Verifica se RLS está ativo
SELECT 
    tablename, 
    rowsecurity as rls_ativo
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN (
        'cliente', 'mesa_negocio', 'ocorrencia', 
        'whatsapp_mensagem', 'produto', 'planner_evento',
        'chatbot_regra', 'movimentacao'
    )
ORDER BY tablename;

-- Lista todas as policies
SELECT 
    tablename,
    policyname,
    cmd
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- =====================================================
-- FIM DA MIGRAÇÃO
-- =====================================================

-- Para testar:
-- SET app.current_tenant = 1;
-- SELECT * FROM cliente;  -- Deve retornar apenas clientes do tenant 1
