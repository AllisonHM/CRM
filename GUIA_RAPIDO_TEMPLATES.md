# 🚀 Guia Rápido - Como Aplicar a Paleta em Novos Templates

## 1️⃣ Template Mínimo

```html
{% extends "base.html" %}
{% block title %}Sua Página - CRM{% endblock %}
{% block content %}

<h1 class="section-title">📋 Título da Página</h1>

<div class="alert alert-info alert-icon">
  Conteúdo aqui...
</div>

{% endblock %}
```

## 2️⃣ Template com Tabela

```html
{% extends "base.html" %}
{% block title %}Clientes - CRM{% endblock %}
{% block content %}

<h1 class="section-title">👥 Clientes</h1>

<div class="mb-3">
  <a href="{{ url_for('add_cliente') }}" class="btn btn-primary btn-rounded">
    ➕ Adicionar Cliente
  </a>
</div>

<div class="table-responsive">
  <table class="table table-crm">
    <thead>
      <tr>
        <th>Nome</th>
        <th>Email</th>
        <th>Status</th>
        <th>Ações</th>
      </tr>
    </thead>
    <tbody>
      {% for cliente in clientes %}
      <tr>
        <td><strong>{{ cliente.nome }}</strong></td>
        <td>{{ cliente.email }}</td>
        <td>
          <span class="badge badge-success">Ativo</span>
        </td>
        <td>
          <a href="#" class="btn btn-sm btn-primary">Ver</a>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

{% endblock %}
```

## 3️⃣ Template com Formulário

```html
{% extends "base.html" %}
{% block title %}Adicionar Cliente - CRM{% endblock %}
{% block content %}

<h1 class="section-title">➕ Adicionar Cliente</h1>

<div class="card card-accent">
  <div class="card-header">📝 Formulário de Cadastro</div>
  <div class="card-body">
    <form method="POST">
      <div class="row">
        <div class="col-md-6">
          <div class="form-group-crm">
            <label for="nome">Nome *</label>
            <input type="text" class="form-control" id="nome" name="nome" required>
          </div>
        </div>
        <div class="col-md-6">
          <div class="form-group-crm">
            <label for="email">Email *</label>
            <input type="email" class="form-control" id="email" name="email" required>
          </div>
        </div>
      </div>

      <div class="form-group-crm">
        <label for="descricao">Descrição</label>
        <textarea class="form-control" id="descricao" name="descricao" rows="4"></textarea>
      </div>

      <div class="d-flex gap-2">
        <button type="submit" class="btn btn-primary btn-rounded">💾 Salvar</button>
        <a href="{{ url_for('cadastro') }}" class="btn btn-outline-secondary btn-rounded">
          ❌ Cancelar
        </a>
      </div>
    </form>
  </div>
</div>

{% endblock %}
```

## 4️⃣ Template com Cards de Estatísticas

```html
{% extends "base.html" %}
{% block title %}Dashboard - CRM{% endblock %}
{% block content %}

<h1 class="section-title">📊 Dashboard</h1>

<div class="row mb-4">
  <div class="col-md-3">
    <div class="stat-card hover-lift">
      <div class="stat-icon">👥</div>
      <div class="stat-value">{{ total_clientes }}</div>
      <div class="stat-label">Total de Clientes</div>
    </div>
  </div>

  <div class="col-md-3">
    <div class="stat-card hover-lift">
      <div class="stat-icon">💰</div>
      <div class="stat-value">R$ {{ receita }}</div>
      <div class="stat-label">Receita Mensal</div>
    </div>
  </div>

  <div class="col-md-3">
    <div class="stat-card hover-lift">
      <div class="stat-icon">📈</div>
      <div class="stat-value">{{ negocios_ativos }}</div>
      <div class="stat-label">Negócios Ativos</div>
    </div>
  </div>

  <div class="col-md-3">
    <div class="stat-card hover-lift">
      <div class="stat-icon">⭐</div>
      <div class="stat-value">{{ satisfacao }}</div>
      <div class="stat-label">Satisfação (5.0)</div>
    </div>
  </div>
</div>

<div class="row">
  <!-- Mais conteúdo aqui -->
</div>

{% endblock %}
```

## 5️⃣ Template com Detalhes (Cards)

```html
{% extends "base.html" %}
{% block title %}{{ cliente.nome }} - CRM{% endblock %}
{% block content %}

<h1 class="section-title">👤 {{ cliente.nome }}</h1>

<div class="row">
  <div class="col-md-6">
    <div class="card card-accent hover-lift">
      <div class="card-header">📋 Informações Pessoais</div>
      <div class="card-body">
        <p><strong>Email:</strong> {{ cliente.email }}</p>
        <p><strong>Telefone:</strong> {{ cliente.telefone }}</p>
        <p><strong>Criado em:</strong> {{ cliente.data_criacao }}</p>
      </div>
    </div>
  </div>

  <div class="col-md-6">
    <div class="card card-accent hover-lift">
      <div class="card-header">📊 Estatísticas</div>
      <div class="card-body">
        <p><strong>Total de Negócios:</strong> 
          <span class="badge badge-primary">{{ cliente.total_negocios }}</span>
        </p>
        <p><strong>Em Andamento:</strong> 
          <span class="badge badge-warning">{{ cliente.negocios_andamento }}</span>
        </p>
        <p><strong>Ocorrências:</strong> 
          <span class="badge badge-danger">{{ cliente.ocorrencias }}</span>
        </p>
      </div>
    </div>
  </div>
</div>

<div class="row mt-4">
  <div class="col-md-12">
    <div class="card">
      <div class="card-header">⚙️ Ações</div>
      <div class="card-body">
        <a href="{{ url_for('editar_cliente', cliente_id=cliente.id) }}" 
           class="btn btn-primary btn-rounded me-2">✏️ Editar</a>
        <a href="{{ url_for('detalhe_cliente', cliente_id=cliente.id) }}" 
           class="btn btn-warning btn-rounded me-2">📋 Ver Negócios</a>
        <button class="btn btn-danger btn-rounded">🗑️ Deletar</button>
      </div>
    </div>
  </div>
</div>

{% endblock %}
```

## 6️⃣ Template com Alertas

```html
{% extends "base.html" %}
{% block title %}Ações - CRM{% endblock %}
{% block content %}

<h1 class="section-title">⚠️ Ações e Avisos</h1>

<!-- Sucesso -->
<div class="alert alert-success alert-icon">
  <strong>Sucesso!</strong> Cliente cadastrado com sucesso.
</div>

<!-- Info -->
<div class="alert alert-info alert-icon">
  <strong>Informação:</strong> Este cliente tem 5 negócios ativos.
</div>

<!-- Aviso -->
<div class="alert alert-warning alert-icon">
  <strong>Aviso:</strong> Há negócios próximos de vencer.
</div>

<!-- Erro -->
<div class="alert alert-danger alert-icon">
  <strong>Erro!</strong> Não foi possível salvar o cliente.
</div>

{% endblock %}
```

## 7️⃣ Template com Timeline

```html
{% extends "base.html" %}
{% block title %}Histórico - CRM{% endblock %}
{% block content %}

<h1 class="section-title">📅 Histórico de Movimentações</h1>

<div class="timeline">
  {% for evento in eventos %}
  <div class="timeline-item">
    <strong>{{ evento.titulo }}</strong>
    <p class="text-muted">{{ evento.descricao }}</p>
    <small class="text-secondary">{{ evento.data }}</small>
  </div>
  {% endfor %}
</div>

{% endblock %}
```

## 🎨 Checklist de Implementação

Para cada novo template, siga este checklist:

- [ ] Template estende `base.html`
- [ ] Título está em `<h1 class="section-title">` com emoji
- [ ] Botões primários usam `btn btn-primary btn-rounded`
- [ ] Botões secundários usam `btn btn-warning btn-rounded`
- [ ] Tabelas usam `class="table table-crm"`
- [ ] Cards usam `class="card"` ou `class="card card-accent"`
- [ ] Formulários usam `class="form-group-crm"`
- [ ] Badges usam `class="badge badge-primary"` ou similar
- [ ] Alertas usam `class="alert alert-success alert-icon"`
- [ ] Links de ação usam `class="btn btn-sm btn-primary"`

## 📋 Classes CSS Disponíveis

### Botões
```html
<!-- Primário -->
<button class="btn btn-primary btn-rounded">Ação</button>

<!-- Secundário -->
<button class="btn btn-warning btn-rounded">Ação</button>

<!-- Outline -->
<button class="btn btn-outline-primary btn-rounded">Ação</button>
```

### Tabelas
```html
<table class="table table-crm">
  <!-- thead e tbody -->
</table>
```

### Cards
```html
<!-- Básico -->
<div class="card">
  <div class="card-header">Título</div>
  <div class="card-body">Conteúdo</div>
</div>

<!-- Com Acento -->
<div class="card card-accent">
  <!-- mesmo conteúdo -->
</div>

<!-- Com Hover -->
<div class="card hover-lift">
  <!-- mesmo conteúdo -->
</div>
```

### Formulários
```html
<div class="form-group-crm">
  <label for="campo">Label</label>
  <input type="text" class="form-control" id="campo">
  <small class="form-text">Texto de ajuda</small>
</div>
```

### Badges
```html
<span class="badge badge-primary">Primary</span>
<span class="badge badge-warning">Warning</span>
<span class="badge badge-success">Success</span>
<span class="badge badge-danger">Danger</span>
<span class="badge badge-info">Info</span>
```

### Alertas
```html
<div class="alert alert-success alert-icon">Mensagem</div>
<div class="alert alert-warning alert-icon">Mensagem</div>
<div class="alert alert-danger alert-icon">Mensagem</div>
<div class="alert alert-info alert-icon">Mensagem</div>
```

### Estatísticas
```html
<div class="stat-card hover-lift">
  <div class="stat-icon">🎯</div>
  <div class="stat-value">123</div>
  <div class="stat-label">Label</div>
</div>
```

## 🎯 Dicas Importantes

1. **Sempre estenda `base.html`**
   - Garante navbar, CSS global, Socket.IO

2. **Use emojis nos títulos**
   - 👥 Clientes, 📊 Dashboard, 💰 Vendas, etc

3. **Botões devem ser `btn-rounded`**
   - Mais elegante e moderno

4. **Tabelas devem usar `table-crm`**
   - Padrão visual consistente

5. **Formulários com `form-group-crm`**
   - Styling completo com label, input, help text

6. **Use hover-lift em cards**
   - Efeito visual elegante

7. **Cores de status corretas**
   - Verde = Sucesso, Laranja = Aviso, Vermelho = Erro

## 🚀 Exemplo Completo - Página de Negócios

```html
{% extends "base.html" %}
{% block title %}Negócios - CRM{% endblock %}
{% block content %}

<h1 class="section-title">💼 Meus Negócios</h1>

<!-- Botões de Ação -->
<div class="mb-3">
  <a href="{{ url_for('add_negocio') }}" class="btn btn-primary btn-rounded me-2">
    ➕ Novo Negócio
  </a>
  <a href="#" class="btn btn-warning btn-rounded">
    📥 Importar
  </a>
</div>

<!-- Estatísticas -->
<div class="row mb-4">
  <div class="col-md-3">
    <div class="stat-card hover-lift">
      <div class="stat-icon">📊</div>
      <div class="stat-value">{{ total }}</div>
      <div class="stat-label">Total de Negócios</div>
    </div>
  </div>
  <div class="col-md-3">
    <div class="stat-card hover-lift">
      <div class="stat-icon">⏳</div>
      <div class="stat-value">{{ andamento }}</div>
      <div class="stat-label">Em Andamento</div>
    </div>
  </div>
  <div class="col-md-3">
    <div class="stat-card hover-lift">
      <div class="stat-icon">✅</div>
      <div class="stat-value">{{ concluidos }}</div>
      <div class="stat-label">Concluídos</div>
    </div>
  </div>
  <div class="col-md-3">
    <div class="stat-card hover-lift">
      <div class="stat-icon">💰</div>
      <div class="stat-value">R$ {{ valor_total }}</div>
      <div class="stat-label">Valor Total</div>
    </div>
  </div>
</div>

<!-- Tabela de Negócios -->
<div class="table-responsive">
  <table class="table table-crm">
    <thead>
      <tr>
        <th>Título</th>
        <th>Cliente</th>
        <th>Valor</th>
        <th>Status</th>
        <th>Ações</th>
      </tr>
    </thead>
    <tbody>
      {% for negocio in negocios %}
      <tr>
        <td><strong>{{ negocio.titulo }}</strong></td>
        <td>{{ negocio.cliente.nome }}</td>
        <td>R$ {{ negocio.valor }}</td>
        <td>
          {% if negocio.status == 'Concluído' %}
          <span class="badge badge-success">✓ {{ negocio.status }}</span>
          {% elif negocio.status == 'Em Andamento' %}
          <span class="badge badge-warning">⏳ {{ negocio.status }}</span>
          {% else %}
          <span class="badge badge-danger">✕ {{ negocio.status }}</span>
          {% endif %}
        </td>
        <td>
          <a href="{{ url_for('detalhe_negocio', negocio_id=negocio.id) }}" 
             class="btn btn-sm btn-primary">
            Ver
          </a>
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

{% endblock %}
```

---

## 📞 Suporte

Dúvidas sobre as cores ou componentes?
- Consulte `PALETA_CORES.md`
- Veja `demo_cores.html` para exemplos visuais
- Verifique `IMPLEMENTACAO_CORES_FINAL.md` para detalhes

