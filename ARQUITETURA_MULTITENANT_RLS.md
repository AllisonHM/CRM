# 🏗️ Arquitetura Multi-Tenant com PostgreSQL RLS

## 📊 Visão Geral da Arquitetura

### Conceito Principal
**Um único banco PostgreSQL** atende múltiplos clientes (tenants) com **isolamento automático** via Row Level Security (RLS).

```
┌─────────────────────────────────────────────────────────┐
│          PostgreSQL Database: crm_saas                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐             │
│  │   Tenant 1      │  │   Tenant 2      │             │
│  │  (tenant_id=1)  │  │  (tenant_id=2)  │             │
│  │                 │  │                 │             │
│  │  - Lead A       │  │  - Lead X       │             │
│  │  - Lead B       │  │  - Lead Y       │             │
│  │  - Produto 1    │  │  - Produto 5    │             │
│  └─────────────────┘  └─────────────────┘             │
│                                                         │
│        🔒 Row Level Security garante isolamento        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Vantagens desta Arquitetura

✅ **Isolamento Forte**: RLS no nível do PostgreSQL (impossível contornar via SQL)  
✅ **Performance**: Índices particionados por tenant_id  
✅ **Simplicidade**: Uma migração para todos os tenants  
✅ **Custo**: Um único banco PostgreSQL  
✅ **Escalável**: Pode migrar tenants grandes para bancos dedicados depois  
✅ **Seguro**: Mesmo com SQL injection, RLS protege  

---

## 🎯 Design Principles

### 1. Tenant Isolation Strategy
- **Shared Database + Shared Schema** com RLS
- Cada row tem `tenant_id`
- RLS força filtro automático
- Aplicação seta `app.current_tenant` na sessão

### 2. Security Layers
```
Camada 1: Aplicação valida permissões
Camada 2: ORM filtra por tenant_id  
Camada 3: RLS força isolamento (backup de segurança)
Camada 4: Audit logs registram acesso
```

### 3. Performance Strategy
- Índices compostos `(tenant_id, ...)`
- Particionamento por tenant_id (opcional, para tenants grandes)
- Connection pooling por tenant
- Query plans otimizados

---

## 📋 Schema do Banco de Dados

### Hierarquia de Entidades

```
tenants (clientes do SaaS)
   ↓
usuarios (usuários de cada tenant)
   ↓
leads → oportunidades → atividades
   ↓
produtos
```

### Tabelas Globais (sem tenant_id)
- `tenants` - Os clientes do SaaS
- `subscriptions` - Planos e pagamentos
- `audit_logs` - Logs centralizados

### Tabelas por Tenant (com tenant_id)
- `usuarios`
- `leads`
- `oportunidades`
- `atividades`
- `produtos`
- `configuracoes`

---

## 🔐 Política de Acesso

### Roles do PostgreSQL

1. **app_admin** - Super usuário da aplicação
   - Pode acessar todos os tenants
   - Usado para migrações e manutenção

2. **app_user** - Usuário normal da aplicação
   - Acessa apenas dados do tenant setado na sessão
   - RLS ativo sempre

3. **app_readonly** - Usuário de leitura (analytics)
   - Apenas SELECT
   - RLS ativo

---

## 🎨 Convenções

### Nomenclatura
- Tabelas: `snake_case` no plural
- Colunas: `snake_case`
- Índices: `idx_<tabela>_<colunas>`
- FK: `fk_<tabela>_<referencia>`
- RLS Policies: `policy_<tabela>_<operacao>_tenant`

### tenant_id
- Tipo: `INTEGER` (ou `UUID` se preferir)
- `NOT NULL` em todas as tabelas de dados
- Sempre primeira coluna após `id`
- Índice composto sempre começa com `tenant_id`

### Timestamps
Todas as tabelas têm:
```sql
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
deleted_at TIMESTAMP NULL  -- Soft delete
```

---

## 🚀 Implementação

Veja os arquivos:
1. **schema_multitenant_rls.sql** - Schema completo
2. **rls_policies.sql** - Políticas de segurança
3. **app_connection.py** - Conexão com tenant_id
4. **middleware_tenant.py** - Middleware Flask
5. **backup_strategy.md** - Backup e restore
6. **migration_strategy.md** - Migração para banco dedicado

---

## 📈 Escalabilidade

### Até 100 tenants
✅ Arquitetura padrão funciona perfeitamente

### 100-1000 tenants
✅ Adicionar particionamento por tenant_id
✅ Connection pooling otimizado
✅ Índices BRIN para tenant_id

### 1000+ tenants ou tenants gigantes
✅ Migrar tenants grandes para bancos dedicados
✅ Sharding por range de tenant_id
✅ Read replicas

---

## 🔒 Segurança

### Checklist de Segurança

- [x] RLS ativo em todas as tabelas de dados
- [x] `tenant_id` validado no login
- [x] Sessão PostgreSQL com `app.current_tenant`
- [x] Audit logs de todos os acessos
- [x] Queries preparadas (prevenção SQL injection)
- [x] Certificados SSL na conexão
- [x] Senhas com bcrypt/argon2
- [x] Rate limiting por tenant
- [x] Backup criptografado
- [x] Testes de isolamento automatizados

---

## 🧪 Testes de Isolamento

Script de teste obrigatório:

```python
def test_tenant_isolation():
    """Garante que tenant 1 não vê dados do tenant 2"""
    
    # Login como tenant 1
    with tenant_context(tenant_id=1):
        Lead.create(nome="Lead Tenant 1")
        assert Lead.query.count() == 1
    
    # Login como tenant 2
    with tenant_context(tenant_id=2):
        leads = Lead.query.all()
        assert len(leads) == 0  # Não vê dados do tenant 1
        
    # Tenta forçar acesso (deve falhar)
    with tenant_context(tenant_id=2):
        try:
            # Mesmo forçando tenant_id=1 na query
            lead = Lead.query.filter_by(tenant_id=1).first()
            assert lead is None  # RLS bloqueia!
        except:
            pass  # RLS deve lançar erro
```

---

## 📊 Monitoramento

### Métricas por Tenant

```sql
-- Uso de storage por tenant
SELECT 
    tenant_id,
    COUNT(*) as total_leads,
    pg_size_pretty(SUM(pg_column_size(leads))) as tamanho
FROM leads
GROUP BY tenant_id
ORDER BY SUM(pg_column_size(leads)) DESC;

-- Queries mais lentas por tenant
SELECT 
    tenant_id,
    query,
    mean_exec_time,
    calls
FROM pg_stat_statements
WHERE query LIKE '%tenant_id%'
ORDER BY mean_exec_time DESC;
```

---

## 🎯 Próximos Passos

1. **Implementar Schema** - Rodar `schema_multitenant_rls.sql`
2. **Ativar RLS** - Rodar `rls_policies.sql`
3. **Adaptar Aplicação** - Usar `app_connection.py`
4. **Testar Isolamento** - Script de testes
5. **Monitorar** - Dashboards de uso por tenant
6. **Planejar Escala** - Estratégia para 1000+ tenants

---

## 📚 Referências

- [PostgreSQL Row Security Policies](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [Multi-Tenant Data Architecture](https://docs.microsoft.com/en-us/azure/architecture/guide/multitenant/considerations/tenancy-models)
- [SaaS Tenant Isolation Strategies](https://aws.amazon.com/blogs/database/multi-tenant-data-isolation-with-postgresql-row-level-security/)
