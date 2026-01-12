-- Script SQL para adicionar manualmente as colunas necessárias
-- Execute este script diretamente no seu banco PostgreSQL

-- 1. Criar tabela usuario_crm (se não existir)
CREATE TABLE IF NOT EXISTS usuario_crm (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    numero_whatsapp VARCHAR(50) NOT NULL UNIQUE,
    api_token VARCHAR(255),
    dias_quarentena_nps INTEGER DEFAULT 30,
    ativo BOOLEAN DEFAULT TRUE,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Adicionar coluna usuario_crm_id na tabela cliente
ALTER TABLE cliente ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);

-- 3. Adicionar coluna data_ultimo_nps_envio na tabela cliente
ALTER TABLE cliente ADD COLUMN IF NOT EXISTS data_ultimo_nps_envio TIMESTAMP;

-- 4. Adicionar coluna usuario_crm_id na tabela mesa_negocio
ALTER TABLE mesa_negocio ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);

-- 5. Adicionar coluna usuario_crm_id na tabela ocorrencia
ALTER TABLE ocorrencia ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);

-- 6. Adicionar coluna usuario_crm_id na tabela whatsapp_mensagem
ALTER TABLE whatsapp_mensagem ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);

-- 7. Adicionar coluna usuario_crm_id na tabela produto
ALTER TABLE produto ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);

-- 8. Adicionar coluna usuario_crm_id na tabela planner_evento
ALTER TABLE planner_evento ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);

-- 9. Inserir usuário CRM inicial (se não existir)
INSERT INTO usuario_crm (nome, numero_whatsapp, dias_quarentena_nps, ativo)
SELECT 'Minha Empresa', '4797043489', 30, TRUE
WHERE NOT EXISTS (SELECT 1 FROM usuario_crm WHERE numero_whatsapp = '4797043489');

-- 10. Atualizar registros existentes para vincular ao primeiro usuário CRM
UPDATE cliente SET usuario_crm_id = 1 WHERE usuario_crm_id IS NULL;
UPDATE mesa_negocio SET usuario_crm_id = 1 WHERE usuario_crm_id IS NULL;
UPDATE ocorrencia SET usuario_crm_id = 1 WHERE usuario_crm_id IS NULL;
UPDATE whatsapp_mensagem SET usuario_crm_id = 1 WHERE usuario_crm_id IS NULL;
UPDATE produto SET usuario_crm_id = 1 WHERE usuario_crm_id IS NULL;
UPDATE planner_evento SET usuario_crm_id = 1 WHERE usuario_crm_id IS NULL;

-- Verificar se as colunas foram criadas
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'cliente' 
AND column_name IN ('usuario_crm_id', 'data_ultimo_nps_envio');
