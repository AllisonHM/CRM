# GUIA_BANCO_POR_CLIENTE.md

# 🗄️ Sistema Multi-Database: Um Banco por Cliente

## 📋 Visão Geral

Este guia explica como o sistema CRM foi estruturado para que **cada cliente tenha seu próprio banco de dados PostgreSQL isolado**.

---

## 🏗️ Arquitetura

### Estrutura de Bancos:

```
PostgreSQL Server
│
├── crm_central                    ← Banco CENTRAL (autenticação)
│   └── Tabela: usuario_crm        ← Todos os usuários do sistema
│
├── crm_cliente_1                  ← Banco do Cliente ID 1
│   ├── cliente
│   ├── mesa_negocio
│   ├── ocorrencia
│   ├── whatsapp_mensagem
│   ├── produto
│   └── planner_evento
│
├── crm_cliente_2                  ← Banco do Cliente ID 2
│   └── [mesmas tabelas]
│
└── crm_cliente_N                  ← Banco do Cliente ID N
    └── [mesmas tabelas]
```

---

## 🔑 Componentes Principais

### 1. **database_manager.py**
Gerencia criação, conexão e operações em múltiplos bancos.

**Principais métodos:**
- `criar_banco_cliente()` - Cria novo banco para um cliente
- `get_session()` - Retorna sessão do banco do cliente
- `session_scope()` - Context manager para transações
- `migrar_banco_cliente()` - Executa migrações em um banco específico
- `excluir_banco_cliente()` - Remove banco (cuidado!)

### 2. **models_central.py**
Define o modelo `UsuarioCRM` que fica no banco central.

**Novos campos:**
- `database_name`: Nome do banco (ex: `crm_cliente_1`)
- `database_criado`: Flag indicando se o banco foi criado

### 3. **models.py** (existente)
Modelos que vão nos bancos individuais dos clientes:
- Cliente
- MesaNegocio
- Ocorrencia
- WhatsAppMensagem
- Produto
- PlannerEvento
- etc.

---

## 🚀 Fluxo de Trabalho

### **1. Novo Cliente Assina o CRM**

```python
# 1. Criar usuário no banco central
novo_usuario = UsuarioCRM(
    nome="Empresa ABC",
    email="contato@empresaabc.com",
    tipo_usuario='admin'
)
novo_usuario.set_password('senha123')
db_central.session.add(novo_usuario)
db_central.session.commit()

# 2. Criar banco de dados dedicado
from database_manager import db_manager

sucesso, msg = db_manager.criar_banco_cliente(
    usuario_crm_id=novo_usuario.id,
    usuario_nome=novo_usuario.nome
)

if sucesso:
    novo_usuario.database_name = db_manager.get_database_name(novo_usuario.id)
    novo_usuario.database_criado = True
    db_central.session.commit()
    print(f"✅ Cliente criado com banco: {novo_usuario.database_name}")
```

**Resultado:**
- ✅ Usuário cadastrado no `crm_central`
- ✅ Banco `crm_cliente_X` criado com todas as tabelas
- ✅ Cliente totalmente isolado

---

### **2. Cliente Faz Login**

```python
@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    senha = request.form.get('senha')
    
    # Busca no banco CENTRAL
    usuario = UsuarioCRM.query.filter_by(email=email).first()
    
    if usuario and usuario.check_password(senha):
        login_user(usuario)
        
        # Sistema agora sabe qual banco usar
        print(f"Cliente logado: {usuario.nome}")
        print(f"Banco de dados: {usuario.get_database_name()}")
        
        return redirect(url_for('menu'))
    
    return "Login inválido", 401
```

---

### **3. Operações no Banco do Cliente**

#### **Método 1: Context Manager (Recomendado)**

```python
from database_manager import db_manager
from flask_login import current_user

@app.route('/clientes/adicionar', methods=['POST'])
@login_required
def adicionar_cliente():
    nome = request.form.get('nome')
    telefone = request.form.get('telefone')
    
    # Pega ID do usuário principal (admin)
    usuario_id = current_user.get_usuario_principal_id()
    
    # Usa o banco específico deste cliente
    with db_manager.session_scope(usuario_id) as session:
        novo_cliente = Cliente(
            nome=nome,
            telefone=telefone
        )
        session.add(novo_cliente)
        # Commit automático ao sair do 'with'
    
    flash('Cliente adicionado!', 'success')
    return redirect(url_for('cadastro'))
```

#### **Método 2: Helper Global**

```python
from flask import g

def get_cliente_db_session():
    """Retorna sessão do banco do cliente logado"""
    if not hasattr(g, 'cliente_db_session'):
        usuario_id = current_user.get_usuario_principal_id()
        g.cliente_db_session = db_manager.get_session(usuario_id)
    return g.cliente_db_session

@app.teardown_appcontext
def shutdown_session(exception=None):
    """Fecha sessão ao fim da requisição"""
    session = g.pop('cliente_db_session', None)
    if session:
        session.close()

@app.route('/clientes')
@login_required
def listar_clientes():
    # Usa a sessão do banco do cliente
    session = get_cliente_db_session()
    clientes = session.query(Cliente).all()
    return render_template('cadastro.html', clientes=clientes)
```

---

## 🔧 Manutenção e Administração

### **Migrar Todos os Bancos**

Quando adicionar novas tabelas ou colunas:

```python
from database_manager import db_manager
from models_central import UsuarioCRM

def migrar_todos():
    admins = UsuarioCRM.query.filter_by(
        tipo_usuario='admin', 
        ativo=True
    ).all()
    
    for admin in admins:
        if admin.database_criado:
            print(f"Migrando: {admin.database_name}")
            sucesso, msg = db_manager.migrar_banco_cliente(admin.id)
            print(f"  {'✅' if sucesso else '❌'} {msg}")

# Executar
with app.app_context():
    migrar_todos()
```

---

### **Backup de Um Cliente**

```python
import subprocess
from datetime import datetime

def backup_cliente(usuario_id):
    db_name = db_manager.get_database_name(usuario_id)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{db_name}_{timestamp}.sql"
    
    comando = [
        'pg_dump',
        '-h', 'localhost',
        '-p', '1222',
        '-U', 'postgres',
        '-d', db_name,
        '-f', backup_file
    ]
    
    subprocess.run(comando, check=True)
    print(f"✅ Backup: {backup_file}")
```

---

### **Listar Todos os Bancos**

```python
from database_manager import db_manager

bancos = db_manager.listar_bancos_clientes()
print(f"📊 Total de bancos: {len(bancos)}")

for banco in bancos:
    print(f"  - {banco}")
```

**Saída:**
```
📊 Total de bancos: 3
  - crm_cliente_1
  - crm_cliente_2
  - crm_cliente_5
```

---

### **Remover Banco de Um Cliente** ⚠️

```python
# ⚠️ CUIDADO! Esta operação é IRREVERSÍVEL!

usuario_id = 5  # ID do cliente a remover

sucesso, msg = db_manager.excluir_banco_cliente(usuario_id)

if sucesso:
    # Também remove do banco central
    usuario = UsuarioCRM.query.get(usuario_id)
    usuario.database_criado = False
    usuario.ativo = False
    db_central.session.commit()
    print(f"✅ Cliente {usuario_id} removido")
```

---

## 📊 Exemplo Completo: Dashboard Admin

```python
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.tipo_usuario != 'super_admin':
        return "Acesso negado", 403
    
    # Lista todos os clientes
    clientes = UsuarioCRM.query.filter_by(
        tipo_usuario='admin',
        ativo=True
    ).all()
    
    estatisticas = []
    
    for cliente in clientes:
        if cliente.database_criado:
            # Conecta no banco do cliente
            with db_manager.session_scope(cliente.id) as session:
                total_clientes = session.query(Cliente).count()
                total_negocios = session.query(MesaNegocio).count()
                
                estatisticas.append({
                    'nome': cliente.nome,
                    'email': cliente.email,
                    'database': cliente.database_name,
                    'total_clientes': total_clientes,
                    'total_negocios': total_negocios
                })
    
    return render_template('admin_dashboard.html', stats=estatisticas)
```

---

## ✅ Vantagens

1. **🔒 Isolamento Total**
   - Dados de um cliente nunca vazam para outro
   - Segurança e compliance (LGPD/GDPR)

2. **⚡ Performance**
   - Queries não competem entre clientes
   - Índices otimizados por cliente

3. **💾 Backups Independentes**
   - Backup/restore por cliente
   - Não afeta outros clientes

4. **📈 Escalabilidade**
   - Pode distribuir bancos em servidores diferentes
   - Clientes grandes em servidores dedicados

5. **🎯 Customização**
   - Pode adicionar campos específicos para um cliente
   - Schema personalizado se necessário

---

## ⚠️ Desvantagens

1. **🔧 Complexidade de Manutenção**
   - Migrações precisam rodar em N bancos
   - Mais difícil de gerenciar

2. **💰 Custo**
   - Mais bancos = mais recursos
   - Pode precisar mais servidores

3. **🔍 Relatórios Globais**
   - Análises cross-client são mais complexas
   - Precisa agregar dados de múltiplos bancos

---

## 🔄 Migração do Sistema Atual

Se você já tem um sistema funcionando com banco único:

### **Passo 1: Setup Inicial**

```bash
# 1. Instalar dependências
pip install psycopg2-binary

# 2. Criar banco central
createdb -h localhost -p 1222 -U postgres crm_central
```

### **Passo 2: Migrar Dados**

```python
# script_migrar_para_multi_db.py

from database import db
from database_manager import db_manager, db_central
from models import Cliente, MesaNegocio, Ocorrencia
from models_central import UsuarioCRM
import app

with app.app_context():
    # 1. Busca todos os admins do sistema antigo
    admins = UsuarioCRM.query.filter_by(tipo_usuario='admin').all()
    
    for admin in admins:
        print(f"\n📦 Migrando dados de: {admin.nome}")
        
        # 2. Cria banco novo para este admin
        sucesso, msg = db_manager.criar_banco_cliente(admin.id, admin.nome)
        
        if not sucesso:
            print(f"  ❌ Erro: {msg}")
            continue
        
        # 3. Busca dados do banco antigo
        clientes_antigos = Cliente.query.filter_by(usuario_crm_id=admin.id).all()
        
        # 4. Copia para o banco novo
        with db_manager.session_scope(admin.id) as session:
            for cliente in clientes_antigos:
                # Cria novo objeto (não pode usar o mesmo)
                novo_cliente = Cliente(
                    nome=cliente.nome,
                    telefone=cliente.telefone,
                    email=cliente.email,
                    # ... outros campos
                )
                session.add(novo_cliente)
        
        print(f"  ✅ {len(clientes_antigos)} clientes migrados")
        
        # Atualiza flag
        admin.database_criado = True
        admin.database_name = db_manager.get_database_name(admin.id)
    
    db_central.session.commit()
    print("\n✅ Migração concluída!")
```

---

## 🎓 Resumo

**Como funciona:**
1. Usuário faz login → sistema identifica qual banco usar
2. Todas as operações vão para o banco específico daquele cliente
3. Dados totalmente isolados e seguros

**Principais arquivos:**
- `database_manager.py` - Gerencia múltiplos bancos
- `models_central.py` - Modelo de usuário (banco central)
- `models.py` - Modelos de dados (bancos dos clientes)
- `exemplo_uso_multi_db.py` - Exemplos práticos

**Próximos passos:**
1. Testar criação de banco para novo cliente
2. Adaptar rotas existentes para usar `db_manager`
3. Implementar script de migração (se já tem dados)
4. Configurar backups automáticos por cliente

---

## 📞 Dúvidas Comuns

**P: E se um colaborador faz login?**
R: O sistema usa `current_user.get_usuario_principal_id()` que retorna o ID do admin (pai). Assim, colaborador acessa o banco do seu admin.

**P: Como fazer relatórios de todos os clientes?**
R: Super admin pode iterar pelos bancos e agregar dados:
```python
for admin in admins:
    with db_manager.session_scope(admin.id) as s:
        dados = s.query(Cliente).count()
        # ... agregar
```

**P: Posso ter clientes em servidores diferentes?**
R: Sim! Basta modificar `database_manager.py` para aceitar host/port por cliente.

---

## 📚 Recursos Adicionais

- [PostgreSQL Multitenancy](https://www.postgresql.org/docs/current/ddl-schemas.html)
- [SQLAlchemy Multiple Databases](https://docs.sqlalchemy.org/en/20/core/engines.html)
- [Flask-SQLAlchemy Binds](https://flask-sqlalchemy.palletsprojects.com/en/3.0.x/binds/)
