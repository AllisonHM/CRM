-- =====================================================
-- SCHEMA MULTI-TENANT COM ROW LEVEL SECURITY
-- PostgreSQL 12+
-- =====================================================

-- =====================================================
-- PARTE 1: TABELAS GLOBAIS (SEM TENANT_ID)
-- =====================================================

-- Clientes do SaaS (os "tenants")
CREATE TABLE tenants (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE, -- Ex: "empresa-abc"
    dominio VARCHAR(200) UNIQUE,       -- Ex: "empresaabc.com"
    
    -- Configurações do tenant
    plano VARCHAR(50) DEFAULT 'free',  -- free, basic, premium, enterprise
    max_usuarios INTEGER DEFAULT 5,
    max_leads INTEGER DEFAULT 1000,
    storage_mb INTEGER DEFAULT 1024,
    
    -- Status
    ativo BOOLEAN DEFAULT true,
    data_trial_fim TIMESTAMP,
    
    -- Metadados
    configuracoes JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- Índices para busca rápida
CREATE INDEX idx_tenants_slug ON tenants(slug) WHERE deleted_at IS NULL;
CREATE INDEX idx_tenants_ativo ON tenants(ativo) WHERE ativo = true;
CREATE INDEX idx_tenants_plano ON tenants(plano);

-- Subscriptions/Pagamentos
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    plano VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active', -- active, canceled, suspended, past_due
    valor_mensal DECIMAL(10,2) NOT NULL,
    
    data_inicio TIMESTAMP NOT NULL,
    data_fim TIMESTAMP,
    proximo_pagamento TIMESTAMP,
    
    metodo_pagamento VARCHAR(50), -- credit_card, boleto, pix
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_tenant ON subscriptions(tenant_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);

-- Logs de auditoria (opcional, mas recomendado)
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    tenant_id INTEGER REFERENCES tenants(id),
    usuario_id INTEGER,
    
    acao VARCHAR(100) NOT NULL,          -- login, create_lead, update_oportunidade
    tabela VARCHAR(100),
    registro_id INTEGER,
    
    dados_antes JSONB,
    dados_depois JSONB,
    
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_tenant_data ON audit_logs(tenant_id, created_at DESC);
CREATE INDEX idx_audit_usuario ON audit_logs(usuario_id);
CREATE INDEX idx_audit_acao ON audit_logs(acao);

-- =====================================================
-- PARTE 2: TABELAS POR TENANT (COM TENANT_ID + RLS)
-- =====================================================

-- ----------------
-- USUÁRIOS
-- ----------------
CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(200) NOT NULL,
    senha_hash VARCHAR(255) NOT NULL,
    
    tipo VARCHAR(50) DEFAULT 'usuario', -- admin, usuario, readonly
    ativo BOOLEAN DEFAULT true,
    
    -- Metadados
    ultimo_login TIMESTAMP,
    configuracoes JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    
    -- Constraint: email único por tenant
    CONSTRAINT uk_usuarios_tenant_email UNIQUE (tenant_id, email)
);

-- Índices otimizados (sempre começam com tenant_id)
CREATE INDEX idx_usuarios_tenant ON usuarios(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_usuarios_tenant_email ON usuarios(tenant_id, email) WHERE deleted_at IS NULL;
CREATE INDEX idx_usuarios_tenant_ativo ON usuarios(tenant_id, ativo) WHERE ativo = true;

-- ----------------
-- LEADS
-- ----------------
CREATE TABLE leads (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(200),
    telefone VARCHAR(50),
    empresa VARCHAR(200),
    
    status VARCHAR(50) DEFAULT 'novo', -- novo, qualificado, contatado, convertido, perdido
    origem VARCHAR(100),               -- website, indicacao, evento, cold_call
    
    pontuacao INTEGER DEFAULT 0,       -- Lead scoring (0-100)
    
    -- Atribuição
    usuario_responsavel_id INTEGER REFERENCES usuarios(id),
    
    -- Datas importantes
    data_ultimo_contato TIMESTAMP,
    data_proximo_followup TIMESTAMP,
    
    -- Metadados
    tags TEXT[],
    campos_customizados JSONB DEFAULT '{}'::jsonb,
    observacoes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- Índices otimizados
CREATE INDEX idx_leads_tenant ON leads(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_leads_tenant_status ON leads(tenant_id, status) WHERE deleted_at IS NULL;
CREATE INDEX idx_leads_tenant_responsavel ON leads(tenant_id, usuario_responsavel_id);
CREATE INDEX idx_leads_tenant_email ON leads(tenant_id, email);
CREATE INDEX idx_leads_tenant_created ON leads(tenant_id, created_at DESC);

-- Índice GIN para busca em tags
CREATE INDEX idx_leads_tags ON leads USING GIN(tags);

-- ----------------
-- OPORTUNIDADES (Negócios)
-- ----------------
CREATE TABLE oportunidades (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    lead_id INTEGER REFERENCES leads(id) ON DELETE SET NULL,
    
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    
    valor DECIMAL(15,2) DEFAULT 0,
    moeda VARCHAR(3) DEFAULT 'BRL',
    
    estagio VARCHAR(50) DEFAULT 'prospeccao', 
    -- prospeccao, qualificacao, proposta, negociacao, fechado_ganho, fechado_perdido
    
    probabilidade INTEGER DEFAULT 50, -- 0-100%
    
    -- Datas
    data_fechamento_esperado DATE,
    data_fechamento_real DATE,
    
    -- Atribuição
    usuario_responsavel_id INTEGER REFERENCES usuarios(id),
    
    -- Metadados
    produtos_interesse TEXT[],
    concorrentes TEXT[],
    campos_customizados JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- Índices
CREATE INDEX idx_oportunidades_tenant ON oportunidades(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_oportunidades_tenant_estagio ON oportunidades(tenant_id, estagio);
CREATE INDEX idx_oportunidades_tenant_responsavel ON oportunidades(tenant_id, usuario_responsavel_id);
CREATE INDEX idx_oportunidades_tenant_lead ON oportunidades(tenant_id, lead_id);
CREATE INDEX idx_oportunidades_tenant_valor ON oportunidades(tenant_id, valor DESC);

-- ----------------
-- ATIVIDADES (Interações, Tarefas)
-- ----------------
CREATE TABLE atividades (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    tipo VARCHAR(50) NOT NULL, -- email, ligacao, reuniao, tarefa, nota
    
    -- Relacionamentos (pode estar ligada a lead ou oportunidade)
    lead_id INTEGER REFERENCES leads(id) ON DELETE CASCADE,
    oportunidade_id INTEGER REFERENCES oportunidades(id) ON DELETE CASCADE,
    
    titulo VARCHAR(200) NOT NULL,
    descricao TEXT,
    
    -- Agendamento
    data_hora TIMESTAMP,
    duracao_minutos INTEGER,
    concluida BOOLEAN DEFAULT false,
    
    -- Atribuição
    usuario_responsavel_id INTEGER REFERENCES usuarios(id),
    
    -- Resultado (para ligações/reuniões)
    resultado VARCHAR(50), -- sem_resposta, marcou_reuniao, nao_interessado, etc
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- Índices
CREATE INDEX idx_atividades_tenant ON atividades(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_atividades_tenant_tipo ON atividades(tenant_id, tipo);
CREATE INDEX idx_atividades_tenant_lead ON atividades(tenant_id, lead_id);
CREATE INDEX idx_atividades_tenant_oportunidade ON atividades(tenant_id, oportunidade_id);
CREATE INDEX idx_atividades_tenant_responsavel ON atividades(tenant_id, usuario_responsavel_id);
CREATE INDEX idx_atividades_tenant_data ON atividades(tenant_id, data_hora);
CREATE INDEX idx_atividades_tenant_concluida ON atividades(tenant_id, concluida) WHERE concluida = false;

-- ----------------
-- PRODUTOS
-- ----------------
CREATE TABLE produtos (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    nome VARCHAR(200) NOT NULL,
    codigo_sku VARCHAR(100),
    descricao TEXT,
    
    categoria VARCHAR(100),
    
    -- Precificação
    preco DECIMAL(15,2) NOT NULL,
    custo DECIMAL(15,2),
    moeda VARCHAR(3) DEFAULT 'BRL',
    
    -- Estoque (opcional)
    estoque_atual INTEGER DEFAULT 0,
    estoque_minimo INTEGER DEFAULT 0,
    
    ativo BOOLEAN DEFAULT true,
    
    -- Metadados
    campos_customizados JSONB DEFAULT '{}'::jsonb,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    
    CONSTRAINT uk_produtos_tenant_sku UNIQUE (tenant_id, codigo_sku)
);

-- Índices
CREATE INDEX idx_produtos_tenant ON produtos(tenant_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_produtos_tenant_ativo ON produtos(tenant_id, ativo) WHERE ativo = true;
CREATE INDEX idx_produtos_tenant_categoria ON produtos(tenant_id, categoria);
CREATE INDEX idx_produtos_tenant_nome ON produtos(tenant_id, nome);

-- ----------------
-- PRODUTOS em OPORTUNIDADES (relacionamento N:N)
-- ----------------
CREATE TABLE oportunidades_produtos (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    oportunidade_id INTEGER NOT NULL REFERENCES oportunidades(id) ON DELETE CASCADE,
    produto_id INTEGER NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
    
    quantidade INTEGER DEFAULT 1,
    preco_unitario DECIMAL(15,2) NOT NULL,
    desconto_percentual DECIMAL(5,2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_oportunidade_produto UNIQUE (oportunidade_id, produto_id)
);

CREATE INDEX idx_oport_produtos_tenant ON oportunidades_produtos(tenant_id);
CREATE INDEX idx_oport_produtos_oportunidade ON oportunidades_produtos(oportunidade_id);
CREATE INDEX idx_oport_produtos_produto ON oportunidades_produtos(produto_id);

-- ----------------
-- CONFIGURAÇÕES por Tenant
-- ----------------
CREATE TABLE configuracoes (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    chave VARCHAR(100) NOT NULL,
    valor JSONB NOT NULL,
    
    tipo VARCHAR(50), -- crm, whatsapp, email, integracao
    descricao TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT uk_configuracoes_tenant_chave UNIQUE (tenant_id, chave)
);

CREATE INDEX idx_configuracoes_tenant ON configuracoes(tenant_id);
CREATE INDEX idx_configuracoes_tenant_tipo ON configuracoes(tenant_id, tipo);

-- =====================================================
-- PARTE 3: FUNÇÕES AUXILIARES
-- =====================================================

-- Função para pegar o tenant_id da sessão
CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS INTEGER AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_tenant', true), '')::INTEGER;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Trigger para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Aplicar trigger em todas as tabelas relevantes
CREATE TRIGGER update_tenants_updated_at BEFORE UPDATE ON tenants
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usuarios_updated_at BEFORE UPDATE ON usuarios
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leads_updated_at BEFORE UPDATE ON leads
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_oportunidades_updated_at BEFORE UPDATE ON oportunidades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_atividades_updated_at BEFORE UPDATE ON atividades
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_produtos_updated_at BEFORE UPDATE ON produtos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configuracoes_updated_at BEFORE UPDATE ON configuracoes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- PARTE 4: VIEWS ÚTEIS
-- =====================================================

-- View: Pipeline de vendas por tenant
CREATE OR REPLACE VIEW vw_pipeline_vendas AS
SELECT 
    o.tenant_id,
    o.estagio,
    COUNT(*) as quantidade_oportunidades,
    SUM(o.valor) as valor_total,
    AVG(o.probabilidade) as probabilidade_media
FROM oportunidades o
WHERE o.deleted_at IS NULL
GROUP BY o.tenant_id, o.estagio;

-- View: Conversão de leads
CREATE OR REPLACE VIEW vw_conversao_leads AS
SELECT 
    l.tenant_id,
    l.status,
    COUNT(*) as quantidade,
    COUNT(o.id) as convertidos_em_oportunidade
FROM leads l
LEFT JOIN oportunidades o ON o.lead_id = l.id AND o.deleted_at IS NULL
WHERE l.deleted_at IS NULL
GROUP BY l.tenant_id, l.status;

-- =====================================================
-- PARTE 5: DADOS DE EXEMPLO (OPCIONAL)
-- =====================================================

-- Criar um tenant de exemplo
INSERT INTO tenants (nome, slug, dominio, plano, ativo) VALUES
('Empresa Demo', 'empresa-demo', 'demo.com', 'premium', true);

-- Criar usuário admin do tenant
INSERT INTO usuarios (tenant_id, nome, email, senha_hash, tipo) VALUES
(1, 'Admin Demo', 'admin@demo.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7z2.OVfXBi', 'admin');

-- =====================================================
-- FIM DO SCHEMA
-- =====================================================

-- Para verificar o schema:
-- \dt - Lista todas as tabelas
-- \d usuarios - Descreve a tabela usuarios
-- \di - Lista todos os índices
