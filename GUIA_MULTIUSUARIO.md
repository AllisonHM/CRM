# GUIA DE ATIVAÇÃO DO SISTEMA MULTIUSUÁRIO

## ✅ O QUE JÁ FOI IMPLEMENTADO:

1. **Modelo de Dados:**
   - UsuarioCRM com campos de autenticação (email, senha_hash, tipo_usuario, permissoes)
   - Hierarquia: super_admin > admin (cliente) > colaborador
   - Migrations aplicadas no banco

2. **Autenticação:**
   - Flask-Login instalado e configurado
   - Tela de login funcional
   - Rotas de login/logout

3. **Gestão de Usuários:**
   - Super Admin pode criar/editar clientes (admin)
   - Clientes (admin) podem criar/editar seus colaboradores
   - Sistema de permissões granulares por módulo

## 🚀 PRIMEIROS PASSOS:

### 1. Criar Super Admin
Acesse no navegador: `http://127.0.0.1:5000/criar_super_admin`

**Credenciais:**
- Email: admin@crm.com
- Senha: admin123

⚠️ **IMPORTANTE:** Altere essa senha após o primeiro login!

### 2. Fazer Login
Acesse: `http://127.0.0.1:5000/login`
Use as credenciais acima.

### 3. Criar seus Clientes
Como Super Admin, você pode:
- Acessar `/usuarios` para gerenciar clientes
- Definir permissões específicas para cada cliente
- Configurar tokens de API WhatsApp individuais

### 4. Clientes criam Colaboradores
Seus clientes podem:
- Acessar `/colaboradores` para gerenciar sua equipe
- Definir quais módulos cada colaborador pode acessar

## ⚠️ TRABALHO RESTANTE (CRÍTICO):

### A. Adicionar @login_required em TODAS as rotas

As rotas que NÃO devem ter @login_required:
- /login
- /criar_super_admin

Todas as outras rotas precisam de:
```python
@app.route('/rota')
@login_required  # <-- ADICIONAR
def minha_rota():
    ...
```

### B. Filtrar dados por usuário em TODAS as queries

**Padrão atual (errado - mostra dados de todos):**
```python
clientes = Cliente.query.all()
```

**Padrão correto (filtrar por usuário):**
```python
# Para queries de contagem
def get_user_filter():
    if current_user.tipo_usuario == 'super_admin':
        return None  # Super admin vê tudo
    return current_user.get_usuario_principal_id()

# Usar assim:
user_id = get_user_filter()
if user_id:
    clientes = Cliente.query.filter_by(usuario_crm_id=user_id).all()
else:
    clientes = Cliente.query.all()
```

**Exemplos de rotas que precisam ser atualizadas:**
- `/menu` - filtrar todas as estatísticas
- `/clientes` - mostrar apenas clientes do usuário
- `/mesas` - mostrar apenas mesas do usuário
- `/ocorrencias` - filtrar ocorrências
- `/whatsapp` - filtrar mensagens
- E TODAS as outras rotas que fazem queries

### C. Atualizar base.html com controle de permissões

O menu lateral precisa mostrar/ocultar itens baseado nas permissões:

```html
{% if current_user.tem_permissao('clientes') %}
<li class="nav-item">
    <a class="nav-link" href="{{ url_for('relacionamento') }}">
        👥 Clientes
    </a>
</li>
{% endif %}
```

### D. Ao cadastrar novos dados, adicionar usuario_crm_id

Ao criar Cliente, MesaNegocio, Ocorrencia, etc:
```python
novo_cliente = Cliente(
    nome=nome,
    usuario_crm_id=current_user.get_usuario_principal_id(),  # <-- ADICIONAR
    ...
)
```

## 📋 HIERARQUIA DE USUÁRIOS:

```
Super Admin (você)
└─ Cliente 1 (admin)
   ├─ Colaborador 1.1
   ├─ Colaborador 1.2
   └─ Dados (clientes, mesas, etc)
└─ Cliente 2 (admin)
   ├─ Colaborador 2.1
   └─ Dados (clientes, mesas, etc)
```

**Regras:**
- Super Admin: vê e gerencia TUDO
- Cliente (admin): vê apenas SEUS dados e gerencia SEUS colaboradores
- Colaborador: vê dados do cliente pai, limitado pelas permissões

## 🔒 MÓDULOS E PERMISSÕES:

Módulos disponíveis para controle:
- clientes
- mesas
- ocorrencias
- produtos
- whatsapp
- chatbot
- planner
- nps
- relatorios

## ⚡ CHECKLIST DE SEGURANÇA:

- [ ] Criar super admin
- [ ] Alterar senha padrão
- [ ] Adicionar @login_required em todas as rotas
- [ ] Filtrar todas as queries por usuario_crm_id
- [ ] Atualizar menu com controle de permissões
- [ ] Testar isolamento de dados entre clientes
- [ ] Remover/proteger rota /criar_super_admin após criação

## 🛠️ EXEMPLO COMPLETO DE ROTA ATUALIZADA:

**ANTES:**
```python
@app.route('/clientes')
def relacionamento():
    clientes = Cliente.query.all()
    return render_template('relacionamento.html', clientes=clientes)
```

**DEPOIS:**
```python
@app.route('/clientes')
@login_required
@permission_required('clientes')
def relacionamento():
    user_id = get_usuario_filter()
    if user_id:
        clientes = Cliente.query.filter_by(usuario_crm_id=user_id).all()
    else:
        clientes = Cliente.query.all()
    return render_template('relacionamento.html', clientes=clientes)
```

## 📞 DÚVIDAS COMUNS:

**Q: Como um cliente adiciona colaboradores?**
A: Cliente faz login → acessa /colaboradores → adiciona novo colaborador

**Q: Colaborador pode ver dados de outro cliente?**
A: NÃO! Cada colaborador vê apenas dados do seu cliente pai.

**Q: Super admin precisa de permissões?**
A: Não, super admin tem acesso total sempre.

**Q: Como desativar um usuário sem deletar?**
A: Ao editar, desmarque "Usuário Ativo"

## 🎯 PRÓXIMA TAREFA:

1. Criar super admin
2. Testar login
3. Criar um cliente de teste
4. Implementar filtros nas rotas principais (menu, clientes, mesas)
5. Adicionar @login_required progressivamente

Boa sorte! 🚀
