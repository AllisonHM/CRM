# 🔐 Boas Práticas: Prevenção de Vazamento de Dados

## ⚠️ Riscos em Sistemas Multi-Tenant

### Top 5 Vulnerabilidades

1. **Broken Access Control** - Usuário acessa dados de outro tenant
2. **SQL Injection** - Query mal construída bypassa RLS
3. **Insecure Direct Object Reference** - IDs previsíveis
4. **Business Logic Flaws** - Falhas na lógica de isolamento
5. **Configuration Errors** - RLS desativado acidentalmente

---

## ✅ Camadas de Segurança

```
┌─────────────────────────────────────────┐
│  Camada 1: Aplicação (Flask)            │
│  - Validação de permissões              │
│  - Autenticação forte                   │
│  - Rate limiting                        │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  Camada 2: ORM (SQLAlchemy)             │
│  - Filtros automáticos por tenant_id    │
│  - Queries parametrizadas               │
│  - Validação de tipos                   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  Camada 3: Banco (PostgreSQL RLS)       │
│  - Row Level Security (última linha)    │
│  - Tenant ID na sessão                  │
│  - Impossível bypassar via SQL          │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│  Camada 4: Auditoria e Monitoramento    │
│  - Logs de todos os acessos             │
│  - Alertas de anomalias                 │
│  - Testes automatizados                 │
└─────────────────────────────────────────┘
```

---

## 🛡️ Práticas Obrigatórias

### 1. SEMPRE Setar tenant_id na Sessão

**❌ ERRADO:**
```python
@app.route('/leads')
def list_leads():
    leads = Lead.query.all()  # ⚠️ Sem filtro de tenant!
    return jsonify(leads)
```

**✅ CORRETO:**
```python
@app.route('/leads')
@require_tenant
def list_leads():
    session = get_db_session()  # Já tem tenant_id setado
    leads = session.query(Lead).all()  # RLS filtra automaticamente
    return jsonify(leads)
```

---

### 2. Validar tenant_id Explicitamente

**❌ ERRADO:**
```python
# Usuário pode manipular tenant_id na requisição
tenant_id = request.json.get('tenant_id')
lead = Lead.query.filter_by(tenant_id=tenant_id).first()
```

**✅ CORRETO:**
```python
# Sempre use o tenant_id do usuário logado
tenant_id = current_user.tenant_id
lead = Lead.query.filter_by(tenant_id=tenant_id).first()

# Ou melhor, deixe RLS fazer o trabalho
session = get_db_session()  # RLS já filtra
lead = session.query(Lead).first()
```

---

### 3. Nunca Confie em IDs do Cliente

**❌ ERRADO:**
```python
@app.route('/leads/<int:lead_id>')
def get_lead(lead_id):
    # ⚠️ Usuário pode tentar IDs de outros tenants
    lead = Lead.query.get(lead_id)
    return jsonify(lead)
```

**✅ CORRETO:**
```python
@app.route('/leads/<int:lead_id>')
@require_tenant
def get_lead(lead_id):
    session = get_db_session()
    
    # RLS garante que só verá se for do seu tenant
    lead = session.query(Lead).filter_by(id=lead_id).first()
    
    if not lead:
        abort(404)  # Não existe OU não pertence ao tenant
    
    return jsonify(lead)
```

---

### 4. UUIDs para IDs Públicos

**Problema:** IDs sequenciais são previsíveis

```python
# Em vez de:
/api/leads/123  # Usuário pode testar 122, 124, etc

# Use UUIDs:
/api/leads/550e8400-e29b-41d4-a716-446655440000
```

**Implementação:**

```python
import uuid

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    tenant_id = db.Column(db.Integer, nullable=False)
    # ...

# Rotas usam public_id
@app.route('/api/leads/<string:public_id>')
def get_lead(public_id):
    lead = Lead.query.filter_by(public_id=public_id).first_or_404()
    return jsonify(lead)
```

---

### 5. Validar JOINs e Subqueries

**❌ PERIGOSO:**
```python
# JOIN sem validar tenant_id
query = db.session.query(Lead).join(Oportunidade)
```

**✅ SEGURO:**
```python
# RLS protege automaticamente
session = get_db_session()  # Tenant setado
query = session.query(Lead).join(Oportunidade)
# Ambas as tabelas são filtradas por RLS
```

---

### 6. Testes de Isolamento Automatizados

```python
import pytest

def test_tenant_isolation(app, db):
    """
    TESTE CRÍTICO: Garante que tenant 1 não vê dados do tenant 2
    Deve rodar em TODA build
    """
    with app.app_context():
        # Cria lead para tenant 1
        with tenant_context(tenant_id=1):
            lead1 = Lead(nome="Lead Tenant 1", tenant_id=1)
            db.session.add(lead1)
            db.session.commit()
            lead1_id = lead1.id
        
        # Tenta acessar como tenant 2
        with tenant_context(tenant_id=2):
            # RLS deve bloquear
            lead = Lead.query.get(lead1_id)
            assert lead is None, "❌ FALHA CRÍTICA: Tenant 2 viu dados do tenant 1!"
        
        # Limpeza
        with tenant_context(tenant_id=1):
            Lead.query.filter_by(id=lead1_id).delete()
            db.session.commit()

def test_sql_injection_protection(app, db):
    """Testa proteção contra SQL injection"""
    with app.app_context():
        with tenant_context(tenant_id=1):
            # Tenta SQL injection
            malicious_input = "' OR '1'='1"
            
            # Query parametrizada protege
            result = Lead.query.filter_by(nome=malicious_input).all()
            assert len(result) == 0
            
            # RLS também protege
            result = db.session.execute(
                "SELECT * FROM leads WHERE nome = :nome",
                {"nome": malicious_input}
            ).fetchall()
            assert len(result) == 0

def test_direct_id_access(app, db):
    """Testa que não consegue acessar por ID de outro tenant"""
    with app.app_context():
        # Cria leads em tenants diferentes
        with tenant_context(tenant_id=1):
            lead1 = Lead(nome="Lead T1", tenant_id=1)
            db.session.add(lead1)
            db.session.commit()
            lead1_id = lead1.id
        
        with tenant_context(tenant_id=2):
            lead2 = Lead(nome="Lead T2", tenant_id=2)
            db.session.add(lead2)
            db.session.commit()
        
        # Tenant 2 tenta acessar lead do tenant 1
        with tenant_context(tenant_id=2):
            # Por ID
            lead = Lead.query.get(lead1_id)
            assert lead is None
            
            # Por filtro explícito (tentando bypassar)
            lead = Lead.query.filter_by(id=lead1_id, tenant_id=1).first()
            assert lead is None  # RLS bloqueia mesmo forçando tenant_id!
```

---

### 7. Audit Logging Completo

```python
def log_access(func):
    """Decorator que loga todos os acessos"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        tenant_id = g.get('tenant_id')
        user_id = current_user.id if current_user.is_authenticated else None
        
        # Log ANTES da ação
        audit_log = AuditLog(
            tenant_id=tenant_id,
            usuario_id=user_id,
            acao=f"{request.method} {request.path}",
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:200],
            request_data=request.get_json() if request.is_json else None
        )
        db.session.add(audit_log)
        db.session.commit()
        
        try:
            result = func(*args, **kwargs)
            
            # Log sucesso
            audit_log.status = 'success'
            db.session.commit()
            
            return result
        
        except Exception as e:
            # Log erro
            audit_log.status = 'error'
            audit_log.error_message = str(e)
            db.session.commit()
            raise
    
    return wrapper

# Uso
@app.route('/api/leads', methods=['POST'])
@log_access
def create_lead():
    # ... código ...
    pass
```

---

### 8. Rate Limiting por Tenant

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=lambda: f"{g.tenant_id}:{get_remote_address()}",
    default_limits=["1000 per hour", "100 per minute"]
)

@app.route('/api/leads')
@limiter.limit("100 per minute")  # 100 requisições/minuto por tenant
def list_leads():
    pass
```

---

### 9. Validação de Schema

```python
from marshmallow import Schema, fields, validates, ValidationError

class LeadSchema(Schema):
    nome = fields.Str(required=True, validate=lambda x: len(x) > 0)
    email = fields.Email()
    telefone = fields.Str()
    tenant_id = fields.Int(dump_only=True)  # Não aceita do cliente!

@app.route('/api/leads', methods=['POST'])
def create_lead():
    schema = LeadSchema()
    
    try:
        # Valida input
        data = schema.load(request.json)
    except ValidationError as e:
        return jsonify({'errors': e.messages}), 400
    
    # Força tenant_id do usuário logado
    data['tenant_id'] = g.tenant_id
    
    lead = Lead(**data)
    session = get_db_session()
    session.add(lead)
    session.commit()
    
    return jsonify(schema.dump(lead)), 201
```

---

### 10. Monitoramento de Anomalias

```python
def detect_anomaly():
    """Detecta comportamentos suspeitos"""
    from datetime import datetime, timedelta
    
    # Múltiplos tenants acessados pelo mesmo IP
    query = """
        SELECT ip_address, COUNT(DISTINCT tenant_id) as tenant_count
        FROM audit_logs
        WHERE created_at > NOW() - INTERVAL '1 hour'
        GROUP BY ip_address
        HAVING COUNT(DISTINCT tenant_id) > 3
    """
    
    suspicious_ips = db.session.execute(query).fetchall()
    
    if suspicious_ips:
        for ip, count in suspicious_ips:
            alert(f"⚠️ IP {ip} acessou {count} tenants diferentes na última hora")
    
    # Tentativas de acesso a IDs fora do range esperado
    query = """
        SELECT tenant_id, usuario_id, COUNT(*) as attempts
        FROM audit_logs
        WHERE created_at > NOW() - INTERVAL '1 hour'
            AND status = 'error'
            AND acao LIKE '%404%'
        GROUP BY tenant_id, usuario_id
        HAVING COUNT(*) > 50
    """
    
    suspicious_users = db.session.execute(query).fetchall()
    
    if suspicious_users:
        for tenant, user, attempts in suspicious_users:
            alert(f"⚠️ Tenant {tenant}, User {user}: {attempts} tentativas de acesso negadas")
```

---

## 📋 Security Checklist

### Desenvolvimento
- [ ] RLS ativo em TODAS as tabelas com tenant_id
- [ ] `FORCE ROW LEVEL SECURITY` configurado
- [ ] tenant_id setado em TODA sessão
- [ ] Queries sempre parametrizadas (nunca string concatenation)
- [ ] IDs públicos são UUIDs
- [ ] Input validation em todas as rotas
- [ ] Testes de isolamento automatizados
- [ ] Audit logging configurado

### Infraestrutura
- [ ] PostgreSQL 12+ com RLS
- [ ] SSL/TLS nas conexões
- [ ] Firewall configurado
- [ ] Backups criptografados
- [ ] Senhas das roles rotacionadas
- [ ] Monitoramento ativo
- [ ] Alertas de segurança configurados

### Processo
- [ ] Code review obrigatório
- [ ] Testes de penetração regulares
- [ ] Análise de logs semanalmente
- [ ] Plano de resposta a incidentes
- [ ] Treinamento da equipe
- [ ] Documentação atualizada

---

## 🚨 Incident Response

### Se Detectar Vazamento de Dados:

1. **ISOLAR** - Desativar tenant afetado imediatamente
2. **INVESTIGAR** - Analisar logs, identificar escopo
3. **NOTIFICAR** - Informar clientes afetados (LGPD/GDPR)
4. **CORRIGIR** - Fechar brecha de segurança
5. **VALIDAR** - Testes extensivos
6. **DOCUMENTAR** - Post-mortem completo
7. **PREVENIR** - Implementar controles adicionais

---

## 🎓 Treinamento da Equipe

### Regras de Ouro:

1. **Nunca** confie em dados do cliente
2. **Sempre** valide tenant_id do usuário logado
3. **Jamais** desative RLS
4. **Teste** isolamento em TODA mudança
5. **Registre** todas as ações em audit log
6. **Monitore** comportamentos anômalos
7. **Responda** rapidamente a alertas

---

## 📊 Métricas de Segurança

```sql
-- Dashboard de segurança

-- 1. Tentativas de acesso negadas por tenant
SELECT 
    tenant_id,
    DATE(created_at) as dia,
    COUNT(*) as tentativas_negadas
FROM audit_logs
WHERE status = 'error'
    AND acao LIKE '%401%' OR acao LIKE '%403%'
GROUP BY tenant_id, DATE(created_at)
ORDER BY tentativas_negadas DESC;

-- 2. Acessos cross-tenant suspeitos
SELECT 
    usuario_id,
    COUNT(DISTINCT tenant_id) as tenants_diferentes,
    array_agg(DISTINCT tenant_id) as tenant_ids
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY usuario_id
HAVING COUNT(DISTINCT tenant_id) > 1;

-- 3. IPs com múltiplos tenants
SELECT 
    ip_address,
    COUNT(DISTINCT tenant_id) as tenant_count,
    array_agg(DISTINCT tenant_id) as tenants
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY ip_address
HAVING COUNT(DISTINCT tenant_id) > 2;

-- 4. Queries mais lentas (possível ataque DoS)
SELECT 
    tenant_id,
    substring(acao, 1, 100) as acao,
    COUNT(*) as total,
    AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) as tempo_medio_seg
FROM audit_logs
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY tenant_id, substring(acao, 1, 100)
HAVING AVG(EXTRACT(EPOCH FROM (updated_at - created_at))) > 5
ORDER BY tempo_medio_seg DESC;
```

---

## 🔒 Encryption at Rest e in Transit

### Banco de Dados

```sql
-- Habilitar criptografia em colunas sensíveis
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Criptografar dados
INSERT INTO usuarios (nome, email, senha_hash)
VALUES (
    'João',
    pgp_sym_encrypt('joao@example.com', 'chave_secreta'),
    '$2b$12$...'
);

-- Descriptografar
SELECT 
    nome,
    pgp_sym_decrypt(email::bytea, 'chave_secreta') as email
FROM usuarios
WHERE id = 1;
```

### Conexão

```python
# Flask config
app.config['SQLALCHEMY_DATABASE_URI'] = (
    'postgresql://user:pass@host/db'
    '?sslmode=require'  # SSL obrigatório
    '&sslrootcert=/path/to/ca.pem'
)
```

---

## 🎯 Conclusão

**Segurança em multi-tenant é CRÍTICA!**

Um único bug pode expor dados de TODOS os clientes.

**Defesa em profundidade:**
- ✅ Validação na aplicação
- ✅ Filtros no ORM
- ✅ RLS no banco (última linha de defesa)
- ✅ Audit logs
- ✅ Monitoramento
- ✅ Testes automatizados

**Nunca confie apenas em uma camada!**
