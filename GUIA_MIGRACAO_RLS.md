# 🚀 Guia de Migração para Multi-Tenant com RLS

## ✅ Pré-requisitos

- PostgreSQL 12+ instalado e rodando
- Backup do banco de dados atual
- Python 3.8+ com ambiente virtual ativo
- Usuário postgres com permissões de CREATE ROLE

## 📋 Passo a Passo

### 1. Backup do Banco Atual

```powershell
# Crie backup antes de qualquer alteração
pg_dump -h localhost -p 1222 -U postgres -d crm -F c -f backup_crm_antes_rls.backup

# Ou com SQL plain text
pg_dump -h localhost -p 1222 -U postgres -d crm > backup_crm_antes_rls.sql
```

### 2. Aplicar Migração SQL

Execute o script de migração:

```powershell
# Via psql
psql -h localhost -p 1222 -U postgres -d crm -f migrate_to_rls.sql

# OU via pgAdmin
# 1. Abra pgAdmin
# 2. Conecte ao banco 'crm'
# 3. Tools > Query Tool
# 4. Abra o arquivo migrate_to_rls.sql
# 5. Execute (F5)
```

**O que este script faz:**
- ✅ Cria função `current_tenant_id()`
- ✅ Adiciona colunas `usuario_crm_id` nas tabelas que não têm
- ✅ Cria índices otimizados para tenant
- ✅ Cria roles `app_user` e `app_admin`
- ✅ Ativa RLS em todas as tabelas
- ✅ Cria políticas RLS para isolamento automático

### 3. Atualizar CRM.py

Substitua a importação do database:

**ANTES:**
```python
from database import db
```

**DEPOIS:**
```python
from database_rls import db, tenant_db, init_db
```

No final do arquivo, substitua:

**ANTES:**
```python
if __name__ == '__main__':
    db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

**DEPOIS:**
```python
if __name__ == '__main__':
    init_db(app)  # Inicializa com suporte a RLS
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

### 4. Testar a Migração

Execute os testes:

```powershell
# Teste 1: Verificar se RLS está ativo
psql -h localhost -p 1222 -U postgres -d crm -c "
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename IN ('cliente', 'mesa_negocio');
"

# Deve retornar rowsecurity = t (true) para todas as tabelas

# Teste 2: Testar isolamento
psql -h localhost -p 1222 -U postgres -d crm -c "
SET app.current_tenant = 1;
SELECT COUNT(*) as clientes_tenant_1 FROM cliente;
"

# Teste 3: Iniciar aplicação
python CRM.py
```

### 5. Verificar Funcionalidades

Após iniciar o CRM, teste:

1. **Login de Usuário**
   - Login com usuário do tenant 1
   - Verifique que só vê dados do seu tenant

2. **Criar Cliente**
   - Crie um novo cliente
   - Verifique que `usuario_crm_id` é preenchido automaticamente

3. **Buscar Clientes**
   - Liste todos os clientes
   - Confirme que só aparecem do tenant logado

4. **Login com Outro Tenant**
   - Faça login com usuário de outro tenant
   - Confirme que vê dados diferentes

5. **Super Admin**
   - Se tiver usuário super_admin, teste acesso sem filtro

## 🔍 Diagnóstico de Problemas

### Problema: RLS não está filtrando

**Verificar se RLS está ativo:**
```sql
SELECT tablename, rowsecurity 
FROM pg_tables 
WHERE schemaname = 'public';
```

**Verificar políticas:**
```sql
SELECT * FROM pg_policies 
WHERE schemaname = 'public';
```

### Problema: Erro "permission denied for table"

**Dar permissões aos roles:**
```sql
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO app_user, app_admin;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user, app_admin;
```

### Problema: tenant_id não está sendo setado

**Verificar logs:**
```python
# No CRM.py, adicione no topo:
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Verificar valor na sessão:**
```python
# Em qualquer rota, adicione:
from flask import g
print(f"Tenant ID atual: {g.get('tenant_id')}")
```

### Problema: Dados de outros tenants aparecem

**Verificar se usuario_crm_id está preenchido:**
```sql
SELECT id, nome, usuario_crm_id 
FROM cliente 
WHERE usuario_crm_id IS NULL;
```

**Preencher valores nulos:**
```sql
-- Para clientes sem tenant (dados antigos)
UPDATE cliente 
SET usuario_crm_id = 1  -- ID do primeiro tenant
WHERE usuario_crm_id IS NULL;
```

## 🎯 Checklist Final

- [ ] Backup criado
- [ ] Script migrate_to_rls.sql executado
- [ ] RLS ativo em todas as tabelas (verificado)
- [ ] Políticas criadas (verificado)
- [ ] CRM.py atualizado
- [ ] Aplicação inicia sem erros
- [ ] Login funciona
- [ ] Dados estão isolados por tenant
- [ ] Criação de registros funciona
- [ ] Edição de registros funciona
- [ ] Exclusão de registros funciona

## 🔐 Configurações de Segurança Adicionais

### 1. Usar app_user no lugar do postgres

Edite o `DATABASE_URI` no CRM.py:

**ANTES:**
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Amovoce123%40@localhost:1222/crm'
```

**DEPOIS:**
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://app_user:crm_app_user_2026!@localhost:1222/crm'
```

### 2. SSL/TLS na Conexão

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://app_user:senha@localhost:1222/crm?sslmode=require'
```

### 3. Auditoria de Acessos

Adicione logs de auditoria:

```python
# Em database_rls.py, no _before_request:
logger.info(f"Acesso ao tenant {tenant_id} pelo usuário {current_user.id}")
```

## 📊 Monitoramento

### Queries para Monitoramento

```sql
-- Ver tenant_id de cada sessão ativa
SELECT 
    pid, 
    usename, 
    application_name,
    current_setting('app.current_tenant', true) as tenant_id,
    state,
    query
FROM pg_stat_activity
WHERE datname = 'crm';

-- Contar registros por tenant
SELECT 
    usuario_crm_id as tenant_id,
    COUNT(*) as total_clientes
FROM cliente
GROUP BY usuario_crm_id
ORDER BY usuario_crm_id;

-- Ver tamanho do banco
SELECT 
    pg_size_pretty(pg_database_size('crm')) as tamanho_total;
```

## 🆘 Rollback (Se Necessário)

Se algo der errado:

```sql
-- 1. Desativar RLS
ALTER TABLE cliente DISABLE ROW LEVEL SECURITY;
ALTER TABLE mesa_negocio DISABLE ROW LEVEL SECURITY;
-- Repita para todas as tabelas

-- 2. Remover políticas
DROP POLICY IF EXISTS policy_cliente_select ON cliente;
-- Repita para todas as políticas

-- 3. Restaurar backup
-- Via comando
pg_restore -h localhost -p 1222 -U postgres -d crm -c backup_crm_antes_rls.backup

-- OU via SQL
psql -h localhost -p 1222 -U postgres -d crm < backup_crm_antes_rls.sql
```

## ✨ Benefícios Obtidos

Após a migração, você terá:

- ✅ **Isolamento Automático**: Cada tenant vê apenas seus dados
- ✅ **Segurança em Nível de BD**: RLS garante isolamento mesmo com SQL direto
- ✅ **Performance Otimizada**: Índices começam com tenant_id
- ✅ **Zero Trust**: Dados isolados mesmo se aplicação for comprometida
- ✅ **Pronto para SaaS**: Arquitetura profissional e escalável
- ✅ **Código Mais Limpo**: Não precisa mais filtrar por usuario_crm_id manualmente
- ✅ **Auditável**: Logs de acesso por tenant

## 📞 Suporte

Em caso de dúvidas ou problemas, consulte:
- `ARQUITETURA_MULTITENANT_RLS.md` - Visão geral da arquitetura
- `SECURITY_BEST_PRACTICES_RLS.md` - Práticas de segurança
- Logs da aplicação em `logging.DEBUG`
