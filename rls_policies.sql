-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- PostgreSQL 12+
-- =====================================================

-- ⚠️ IMPORTANTE: Execute este arquivo DEPOIS de criar o schema
-- Este arquivo configura as políticas de segurança RLS

-- =====================================================
-- PARTE 1: CRIAR ROLES DE APLICAÇÃO
-- =====================================================

-- Role para usuário normal da aplicação (isolamento por tenant)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
        CREATE ROLE app_user LOGIN PASSWORD 'senha_segura_aqui_12345!';
    END IF;
END
$$;

-- Role para admin da aplicação (acesso a todos os tenants)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_admin') THEN
        CREATE ROLE app_admin LOGIN PASSWORD 'senha_admin_segura_67890!';
    END IF;
END
$$;

-- Role para leitura apenas (analytics, relatórios)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_readonly') THEN
        CREATE ROLE app_readonly LOGIN PASSWORD 'senha_readonly_11111!';
    END IF;
END
$$;

-- =====================================================
-- PARTE 2: PERMISSÕES NAS TABELAS
-- =====================================================

-- Tabelas GLOBAIS (sem RLS) - acesso normal
GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO app_admin;
GRANT SELECT ON tenants TO app_user;

GRANT SELECT, INSERT, UPDATE ON subscriptions TO app_admin;
GRANT SELECT ON subscriptions TO app_user;

GRANT SELECT, INSERT ON audit_logs TO app_admin, app_user;
GRANT SELECT ON audit_logs TO app_readonly;

-- Tabelas COM RLS - acesso controlado
GRANT SELECT, INSERT, UPDATE, DELETE ON usuarios TO app_user, app_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON leads TO app_user, app_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON oportunidades TO app_user, app_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON atividades TO app_user, app_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON produtos TO app_user, app_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON oportunidades_produtos TO app_user, app_admin;
GRANT SELECT, INSERT, UPDATE, DELETE ON configuracoes TO app_user, app_admin;

-- Readonly - apenas SELECT
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

-- Permissão para sequences (IDs)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user, app_admin;

-- =====================================================
-- PARTE 3: ATIVAR RLS NAS TABELAS
-- =====================================================

-- ⚠️ CRITICAL: Ativar RLS em TODAS as tabelas com tenant_id
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE oportunidades ENABLE ROW LEVEL SECURITY;
ALTER TABLE atividades ENABLE ROW LEVEL SECURITY;
ALTER TABLE produtos ENABLE ROW LEVEL SECURITY;
ALTER TABLE oportunidades_produtos ENABLE ROW LEVEL SECURITY;
ALTER TABLE configuracoes ENABLE ROW LEVEL SECURITY;

-- Forçar RLS mesmo para o dono da tabela (importante!)
ALTER TABLE usuarios FORCE ROW LEVEL SECURITY;
ALTER TABLE leads FORCE ROW LEVEL SECURITY;
ALTER TABLE oportunidades FORCE ROW LEVEL SECURITY;
ALTER TABLE atividades FORCE ROW LEVEL SECURITY;
ALTER TABLE produtos FORCE ROW LEVEL SECURITY;
ALTER TABLE oportunidades_produtos FORCE ROW LEVEL SECURITY;
ALTER TABLE configuracoes FORCE ROW LEVEL SECURITY;

-- =====================================================
-- PARTE 4: POLÍTICAS RLS - USUÁRIOS
-- =====================================================

-- Policy: app_user vê apenas seu tenant
CREATE POLICY policy_usuarios_select_tenant ON usuarios
    FOR SELECT
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_usuarios_insert_tenant ON usuarios
    FOR INSERT
    TO app_user
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_usuarios_update_tenant ON usuarios
    FOR UPDATE
    TO app_user
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_usuarios_delete_tenant ON usuarios
    FOR DELETE
    TO app_user
    USING (tenant_id = current_tenant_id());

-- Policy: app_admin vê tudo (bypass RLS)
CREATE POLICY policy_usuarios_admin_all ON usuarios
    FOR ALL
    TO app_admin
    USING (true)
    WITH CHECK (true);

-- Policy: app_readonly vê apenas seu tenant
CREATE POLICY policy_usuarios_readonly_tenant ON usuarios
    FOR SELECT
    TO app_readonly
    USING (tenant_id = current_tenant_id());

-- =====================================================
-- PARTE 5: POLÍTICAS RLS - LEADS
-- =====================================================

CREATE POLICY policy_leads_select_tenant ON leads
    FOR SELECT
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_leads_insert_tenant ON leads
    FOR INSERT
    TO app_user
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_leads_update_tenant ON leads
    FOR UPDATE
    TO app_user
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_leads_delete_tenant ON leads
    FOR DELETE
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_leads_admin_all ON leads
    FOR ALL
    TO app_admin
    USING (true)
    WITH CHECK (true);

CREATE POLICY policy_leads_readonly_tenant ON leads
    FOR SELECT
    TO app_readonly
    USING (tenant_id = current_tenant_id());

-- =====================================================
-- PARTE 6: POLÍTICAS RLS - OPORTUNIDADES
-- =====================================================

CREATE POLICY policy_oportunidades_select_tenant ON oportunidades
    FOR SELECT
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_oportunidades_insert_tenant ON oportunidades
    FOR INSERT
    TO app_user
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_oportunidades_update_tenant ON oportunidades
    FOR UPDATE
    TO app_user
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_oportunidades_delete_tenant ON oportunidades
    FOR DELETE
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_oportunidades_admin_all ON oportunidades
    FOR ALL
    TO app_admin
    USING (true)
    WITH CHECK (true);

CREATE POLICY policy_oportunidades_readonly_tenant ON oportunidades
    FOR SELECT
    TO app_readonly
    USING (tenant_id = current_tenant_id());

-- =====================================================
-- PARTE 7: POLÍTICAS RLS - ATIVIDADES
-- =====================================================

CREATE POLICY policy_atividades_select_tenant ON atividades
    FOR SELECT
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_atividades_insert_tenant ON atividades
    FOR INSERT
    TO app_user
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_atividades_update_tenant ON atividades
    FOR UPDATE
    TO app_user
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_atividades_delete_tenant ON atividades
    FOR DELETE
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_atividades_admin_all ON atividades
    FOR ALL
    TO app_admin
    USING (true)
    WITH CHECK (true);

CREATE POLICY policy_atividades_readonly_tenant ON atividades
    FOR SELECT
    TO app_readonly
    USING (tenant_id = current_tenant_id());

-- =====================================================
-- PARTE 8: POLÍTICAS RLS - PRODUTOS
-- =====================================================

CREATE POLICY policy_produtos_select_tenant ON produtos
    FOR SELECT
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_produtos_insert_tenant ON produtos
    FOR INSERT
    TO app_user
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_produtos_update_tenant ON produtos
    FOR UPDATE
    TO app_user
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_produtos_delete_tenant ON produtos
    FOR DELETE
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_produtos_admin_all ON produtos
    FOR ALL
    TO app_admin
    USING (true)
    WITH CHECK (true);

CREATE POLICY policy_produtos_readonly_tenant ON produtos
    FOR SELECT
    TO app_readonly
    USING (tenant_id = current_tenant_id());

-- =====================================================
-- PARTE 9: POLÍTICAS RLS - OPORTUNIDADES_PRODUTOS
-- =====================================================

CREATE POLICY policy_oport_produtos_select_tenant ON oportunidades_produtos
    FOR SELECT
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_oport_produtos_insert_tenant ON oportunidades_produtos
    FOR INSERT
    TO app_user
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_oport_produtos_update_tenant ON oportunidades_produtos
    FOR UPDATE
    TO app_user
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_oport_produtos_delete_tenant ON oportunidades_produtos
    FOR DELETE
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_oport_produtos_admin_all ON oportunidades_produtos
    FOR ALL
    TO app_admin
    USING (true)
    WITH CHECK (true);

-- =====================================================
-- PARTE 10: POLÍTICAS RLS - CONFIGURAÇÕES
-- =====================================================

CREATE POLICY policy_configuracoes_select_tenant ON configuracoes
    FOR SELECT
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_configuracoes_insert_tenant ON configuracoes
    FOR INSERT
    TO app_user
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_configuracoes_update_tenant ON configuracoes
    FOR UPDATE
    TO app_user
    USING (tenant_id = current_tenant_id())
    WITH CHECK (tenant_id = current_tenant_id());

CREATE POLICY policy_configuracoes_delete_tenant ON configuracoes
    FOR DELETE
    TO app_user
    USING (tenant_id = current_tenant_id());

CREATE POLICY policy_configuracoes_admin_all ON configuracoes
    FOR ALL
    TO app_admin
    USING (true)
    WITH CHECK (true);

-- =====================================================
-- PARTE 11: TESTES DE VERIFICAÇÃO
-- =====================================================

-- Verificar se RLS está ativo
SELECT 
    schemaname, 
    tablename, 
    rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
    AND tablename IN ('usuarios', 'leads', 'oportunidades', 'atividades', 'produtos')
ORDER BY tablename;

-- Listar todas as policies
SELECT 
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- =====================================================
-- PARTE 12: FUNÇÃO DE TESTE DE ISOLAMENTO
-- =====================================================

CREATE OR REPLACE FUNCTION test_tenant_isolation() RETURNS TABLE(
    teste VARCHAR,
    resultado VARCHAR,
    detalhes TEXT
) AS $$
DECLARE
    tenant1_count INTEGER;
    tenant2_count INTEGER;
BEGIN
    -- Teste 1: Inserir dados como tenant 1
    PERFORM set_config('app.current_tenant', '1', false);
    
    INSERT INTO leads (tenant_id, nome, email) 
    VALUES (1, 'Lead Tenant 1', 'lead1@tenant1.com');
    
    SELECT COUNT(*) INTO tenant1_count FROM leads;
    
    RETURN QUERY SELECT 
        'Teste 1'::VARCHAR,
        CASE WHEN tenant1_count = 1 THEN 'PASSOU' ELSE 'FALHOU' END,
        format('Tenant 1 vê %s lead(s)', tenant1_count);
    
    -- Teste 2: Trocar para tenant 2
    PERFORM set_config('app.current_tenant', '2', false);
    
    SELECT COUNT(*) INTO tenant2_count FROM leads;
    
    RETURN QUERY SELECT 
        'Teste 2'::VARCHAR,
        CASE WHEN tenant2_count = 0 THEN 'PASSOU' ELSE 'FALHOU' END,
        format('Tenant 2 vê %s lead(s) (deveria ser 0)', tenant2_count);
    
    -- Teste 3: Tentar forçar acesso ao tenant 1 (deve falhar)
    BEGIN
        PERFORM * FROM leads WHERE tenant_id = 1;
        RETURN QUERY SELECT 
            'Teste 3'::VARCHAR,
            'FALHOU'::VARCHAR,
            'RLS não bloqueou acesso cross-tenant!'::TEXT;
    EXCEPTION WHEN OTHERS THEN
        RETURN QUERY SELECT 
            'Teste 3'::VARCHAR,
            'PASSOU'::VARCHAR,
            'RLS bloqueou tentativa de acesso cross-tenant'::TEXT;
    END;
    
    -- Limpar dados de teste
    PERFORM set_config('app.current_tenant', '1', false);
    DELETE FROM leads WHERE email = 'lead1@tenant1.com';
END;
$$ LANGUAGE plpgsql;

-- Para executar os testes:
-- SELECT * FROM test_tenant_isolation();

-- =====================================================
-- FIM DAS POLÍTICAS RLS
-- =====================================================

-- PRÓXIMOS PASSOS:
-- 1. Testar acesso como app_user
-- 2. Verificar que tenant_id é forçado
-- 3. Testar que não consegue acessar dados de outro tenant
-- 4. Implementar na aplicação

-- DICAS DE SEGURANÇA:
-- ✅ Sempre use FORCE ROW LEVEL SECURITY
-- ✅ Teste isolamento entre tenants regularmente
-- ✅ Use prepared statements na aplicação
-- ✅ Log todas as tentativas de acesso
-- ✅ Monitore queries suspeitas
-- ✅ Faça backup criptografado
-- ✅ Rotacione senhas das roles periodicamente
