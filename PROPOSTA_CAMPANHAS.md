# 📊 PROPOSTA: MÓDULO DE CAMPANHAS

## 🎯 VISÃO GERAL

Sistema de **Gestão de Campanhas** integrado ao módulo de Negócios, permitindo:
- Criar campanhas de vendas/marketing
- Importar leads em massa (Excel/CSV)
- Acompanhar progresso via funil visual (Kanban)
- Integrar com WhatsApp para contato automático
- Análise de resultados e conversão

---

## 📐 ARQUITETURA PROPOSTA

### **1. MODELO DE DADOS**

```python
class Campanha(db.Model):
    """Representa uma campanha de marketing/vendas"""
    __tablename__ = 'campanha'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=False)
    
    # Informações Básicas
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(50), nullable=False)  # vendas, marketing, relacionamento, nps
    status = db.Column(db.String(50), default='Ativa')  # Ativa, Pausada, Concluída, Cancelada
    
    # Período
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=True)
    
    # Metas
    meta_leads = db.Column(db.Integer, nullable=True)  # Quantidade de leads esperados
    meta_conversao = db.Column(db.Float, nullable=True)  # % de conversão esperada
    meta_receita = db.Column(db.Float, nullable=True)  # Receita esperada
    
    # Produto/Oferta (opcional)
    produto_principal = db.Column(db.String(200), nullable=True)
    valor_oferta = db.Column(db.Float, nullable=True)
    desconto_percentual = db.Column(db.Float, nullable=True)
    
    # WhatsApp (automação)
    mensagem_template = db.Column(db.Text, nullable=True)  # Template para envio
    envio_automatico = db.Column(db.Boolean, default=False)
    
    # Estatísticas (calculadas)
    total_leads = db.Column(db.Integer, default=0)
    leads_contatados = db.Column(db.Integer, default=0)
    leads_convertidos = db.Column(db.Integer, default=0)
    receita_gerada = db.Column(db.Float, default=0.0)
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relacionamentos
    leads = db.relationship('LeadCampanha', backref='campanha', lazy=True, cascade='all, delete-orphan')
    
    # Propriedades calculadas
    @property
    def taxa_conversao(self):
        if self.total_leads > 0:
            return round((self.leads_convertidos / self.total_leads) * 100, 2)
        return 0.0
    
    @property
    def dias_restantes(self):
        if self.data_fim:
            delta = self.data_fim - datetime.today().date()
            return max(0, delta.days)
        return None


class LeadCampanha(db.Model):
    """Representa um lead dentro de uma campanha (similar a MesaNegocio)"""
    __tablename__ = 'lead_campanha'
    
    id = db.Column(db.Integer, primary_key=True)
    campanha_id = db.Column(db.Integer, db.ForeignKey('campanha.id'), nullable=False)
    usuario_crm_id = db.Column(db.Integer, db.ForeignKey('usuario_crm.id'), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=True)  # Se já existe no CRM
    
    # Informações do Lead (importado do CSV/Excel)
    nome = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(200), nullable=True)
    empresa = db.Column(db.String(200), nullable=True)
    cargo = db.Column(db.String(100), nullable=True)
    origem = db.Column(db.String(100), nullable=True)  # CSV, Manual, Site, etc.
    
    # Funil de Vendas (Estágios da Campanha)
    estagio = db.Column(db.String(50), default='Novo')  
    # Estágios: Novo → Contatado → Qualificado → Proposta → Negociação → Ganho/Perdido
    
    # Informações de Contato
    data_contato = db.Column(db.DateTime, nullable=True)
    canal_contato = db.Column(db.String(50), nullable=True)  # WhatsApp, Email, Telefone, Presencial
    responsavel = db.Column(db.String(100), nullable=True)  # Nome do colaborador responsável
    
    # Negociação
    produto_interesse = db.Column(db.String(200), nullable=True)
    valor_proposta = db.Column(db.Float, nullable=True)
    valor_fechado = db.Column(db.Float, nullable=True)
    
    # Status Final
    resultado = db.Column(db.String(50), nullable=True)  # Ganho, Perdido, Em andamento
    motivo_perda = db.Column(db.String(200), nullable=True)  # Se perdido, qual motivo?
    data_fechamento = db.Column(db.Date, nullable=True)
    
    # Observações e Histórico
    observacoes = db.Column(db.Text, nullable=True)
    historico_interacoes = db.Column(db.JSON, nullable=True)  
    # Exemplo: [{"data": "2026-04-26", "tipo": "whatsapp", "texto": "Enviado proposta"}]
    
    # Tags personalizadas
    tags = db.Column(db.JSON, nullable=True)  # ["quente", "decisor", "orçamento-alto"]
    
    # Timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Índices para performance
    __table_args__ = (
        db.Index('idx_campanha_estagio', 'campanha_id', 'estagio'),
        db.Index('idx_campanha_resultado', 'campanha_id', 'resultado'),
        db.Index('idx_telefone', 'telefone'),
    )
```

---

## 🎨 INTERFACE PROPOSTA

### **OPÇÃO 1: ABA DENTRO DE NEGÓCIOS** (Recomendado)

Adicionar uma aba "Campanhas" na tela de Negócios:

```html
<!-- mesas_negocio.html -->
<ul class="nav nav-tabs mb-4" role="tablist">
  <li class="nav-item">
    <a class="nav-link active" data-bs-toggle="tab" href="#tab-mesas">
      <i class="fas fa-handshake"></i> Negociações
    </a>
  </li>
  <li class="nav-item">
    <a class="nav-link" data-bs-toggle="tab" href="#tab-campanhas">
      <i class="fas fa-bullhorn"></i> Campanhas
    </a>
  </li>
</ul>

<div class="tab-content">
  <!-- Aba Negociações (atual) -->
  <div class="tab-pane fade show active" id="tab-mesas">
    <!-- Conteúdo atual de mesas -->
  </div>
  
  <!-- Aba Campanhas (NOVA) -->
  <div class="tab-pane fade" id="tab-campanhas">
    <!-- Lista de campanhas + Kanban -->
  </div>
</div>
```

**Vantagens:**
- ✅ Mantém contexto de negócio
- ✅ Fácil navegação
- ✅ Aproveita código existente
- ✅ Menos poluição no menu

---

### **OPÇÃO 2: PÁGINA SEPARADA** (Alternativa)

Criar rota `/campanhas` independente:

**Vantagens:**
- ✅ Mais espaço visual
- ✅ Mais flexibilidade de layout
- ✅ Carregamento independente

**Desvantagens:**
- ❌ Mais cliques para navegar
- ❌ Precisa adicionar ao menu

---

## 📊 LAYOUT DA TELA DE CAMPANHAS

### **Seção 1: Lista de Campanhas**

```
┌─────────────────────────────────────────────────────────────┐
│  📊 CAMPANHAS                        [+ Nova Campanha]       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  🔵 Black Friday 2026                      🟢 ATIVA          │
│  └─ 150/200 leads | 12% conversão | R$ 45.000 gerados       │
│     📅 01/11 - 30/11  |  📍 23 dias restantes                │
│     [Ver Funil] [Importar Leads] [Relatório]                │
│                                                               │
│  🟡 Captação Maio                          🟡 PAUSADA        │
│  └─ 80/100 leads | 8% conversão | R$ 12.000 gerados         │
│     📅 01/05 - 31/05  |  ✓ Concluída                         │
│     [Ver Funil] [Relatório]                                  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### **Seção 2: Funil Kanban (ao clicar em "Ver Funil")**

```
┌────────────────────────────────────────────────────────────────────┐
│  ⬅ Voltar   Campanha: Black Friday 2026    [Importar CSV/Excel]   │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  📋 FUNIL DE VENDAS                                                 │
│                                                                      │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐      │
│  │ NOVO │  │CONTA-│  │QUALI-│  │PROPO-│  │NEGOC.│  │GANHO │      │
│  │      │  │ TADO │  │FICADO│  │ STA  │  │      │  │      │      │
│  │  45  │  │  32  │  │  18  │  │  12  │  │   8  │  │  18  │      │
│  ├──────┤  ├──────┤  ├──────┤  ├──────┤  ├──────┤  ├──────┤      │
│  │ Lead │  │ Lead │  │ Lead │  │ Lead │  │ Lead │  │ Lead │      │
│  │ #001 │  │ #005 │  │ #010 │  │ #015 │  │ #020 │  │ #025 │      │
│  │ João │  │ Maria│  │ Pedro│  │ Ana  │  │ Lucas│  │Carlos│      │
│  │ ▼    │  │ ▼    │  │ ▼    │  │ ▼    │  │ ▼    │  │ ▼    │      │
│  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘  └──────┘      │
│                                                                      │
│  📊 Estatísticas:                                                   │
│  • Taxa de Conversão: 12% (18 ganhos / 150 leads)                  │
│  • Ticket Médio: R$ 2.500                                           │
│  • Tempo Médio de Conversão: 15 dias                                │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 📥 IMPORTAÇÃO DE LEADS (CSV/EXCEL)

### **Formato Esperado**

```csv
nome,telefone,email,empresa,cargo,origem,observacoes
João Silva,11999999999,joao@empresa.com,Empresa X,Diretor,Site,Cliente antigo
Maria Santos,11988888888,maria@empresa.com,Empresa Y,Gerente,Indicação,
Pedro Costa,11977777777,pedro@empresa.com,,,,
```

### **Mapeamento Flexível**

```
┌──────────────────────────────────────────────────┐
│  IMPORTAR LEADS - Passo 1: Upload                │
├──────────────────────────────────────────────────┤
│                                                    │
│  Selecione o arquivo: [📁 Escolher arquivo]       │
│  Formatos aceitos: .csv, .xlsx, .xls              │
│                                                    │
│  [Fazer Upload]                                    │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│  IMPORTAR LEADS - Passo 2: Mapear Colunas        │
├──────────────────────────────────────────────────┤
│                                                    │
│  Coluna do Arquivo    →    Campo do Sistema      │
│  ─────────────────────────────────────────────   │
│  Coluna A (Nome)      →    [Nome *]              │
│  Coluna B (Tel)       →    [Telefone]            │
│  Coluna C (Email)     →    [Email]               │
│  Coluna D (Emp)       →    [Empresa]             │
│  Coluna E (Cargo)     →    [Cargo]               │
│  Coluna F             →    [-- Ignorar --]       │
│                                                    │
│  ✓ Detectar automaticamente se lead já existe    │
│  ✓ Criar clientes no CRM para novos leads        │
│                                                    │
│  [Voltar]  [Importar 150 leads]                  │
└──────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────┐
│  IMPORTAÇÃO CONCLUÍDA                             │
├──────────────────────────────────────────────────┤
│                                                    │
│  ✅ 150 leads importados com sucesso              │
│  ⚠️  12 leads duplicados (ignorados)              │
│  ❌  3 linhas com erro (telefone inválido)        │
│                                                    │
│  [Ver Funil]  [Baixar Log de Erros]              │
└──────────────────────────────────────────────────┘
```

---

## 🔄 FUNCIONALIDADES PRINCIPAIS

### **1. Gestão de Campanhas**

- ✅ **Criar campanha** com metas e período
- ✅ **Pausar/Reativar** campanha
- ✅ **Arquivar** campanhas antigas
- ✅ **Duplicar** campanha (template)
- ✅ **Excluir** campanha (e todos leads)

### **2. Gestão de Leads**

- ✅ **Importar** via CSV/Excel
- ✅ **Adicionar** lead manualmente
- ✅ **Editar** informações do lead
- ✅ **Mover** lead entre estágios (drag & drop)
- ✅ **Atribuir** responsável
- ✅ **Adicionar** observações e tags
- ✅ **Vincular** lead a cliente existente
- ✅ **Converter** lead em cliente
- ✅ **Marcar** como Ganho/Perdido

### **3. Integração WhatsApp**

- ✅ **Enviar mensagem** individual para lead
- ✅ **Disparo em massa** para estágio específico
- ✅ **Templates** de mensagem personalizados
- ✅ **Variáveis** dinâmicas: `{nome}`, `{empresa}`, `{produto}`

Exemplo:
```
Olá {nome}! 👋

Vi que você tem interesse em {produto}.

Temos uma oferta especial de Black Friday com 30% OFF!

Quer saber mais? 😊
```

### **4. Relatórios e Análises**

- ✅ **Dashboard** com KPIs:
  - Total de leads
  - Taxa de conversão
  - Ticket médio
  - Receita gerada
  - Tempo médio de conversão
  
- ✅ **Gráficos**:
  - Funil de conversão
  - Evolução temporal
  - Distribuição por origem
  - Motivos de perda

- ✅ **Exportação**:
  - CSV completo
  - Excel com formatação
  - PDF de relatório

---

## 🎯 FLUXO DE TRABALHO TÍPICO

### **Cenário: Black Friday**

1. **Criar Campanha**
   - Nome: "Black Friday 2026"
   - Período: 01/11 - 30/11
   - Meta: 200 leads, 15% conversão, R$ 100k receita
   - Produto: "Pacote Premium"
   - Desconto: 30%

2. **Importar Leads**
   - Upload arquivo: `leads_blackfriday.xlsx` (250 linhas)
   - Mapear colunas automaticamente
   - Importar 237 leads (13 duplicados)

3. **Distribuir Responsáveis**
   - João: 80 leads
   - Maria: 80 leads
   - Pedro: 77 leads

4. **Enviar Mensagem Inicial** (WhatsApp)
   ```
   🎉 Black Friday Vitriun CRM!
   
   {nome}, aproveite 30% OFF no Pacote Premium!
   
   Oferta válida até 30/11.
   Quer saber mais?
   ```

5. **Acompanhar Funil**
   - Ver quantos leads foram contatados
   - Mover leads entre estágios
   - Marcar Ganho/Perdido

6. **Análise Final**
   - Taxa conversão: 14% (33 ganhos)
   - Receita: R$ 82.500
   - Ticket médio: R$ 2.500
   - Principais motivos de perda: preço (12), prazo (8)

---

## 💾 ESTRUTURA DE ROTAS

```python
# Campanhas
@app.route("/campanhas")
def listar_campanhas()

@app.route("/campanhas/criar", methods=['GET', 'POST'])
def criar_campanha()

@app.route("/campanhas/<int:id>")
def ver_campanha(id)  # Funil Kanban

@app.route("/campanhas/<int:id>/editar", methods=['GET', 'POST'])
def editar_campanha(id)

@app.route("/campanhas/<int:id>/pausar", methods=['POST'])
def pausar_campanha(id)

@app.route("/campanhas/<int:id>/excluir", methods=['POST'])
def excluir_campanha(id)

# Leads
@app.route("/campanhas/<int:campanha_id>/importar", methods=['GET', 'POST'])
def importar_leads(campanha_id)

@app.route("/campanhas/<int:campanha_id>/leads/adicionar", methods=['GET', 'POST'])
def adicionar_lead(campanha_id)

@app.route("/leads/<int:id>/editar", methods=['GET', 'POST'])
def editar_lead(id)

@app.route("/leads/<int:id>/mover", methods=['POST'])
def mover_lead_estagio(id)  # AJAX para drag & drop

@app.route("/leads/<int:id>/observacao", methods=['POST'])
def adicionar_observacao_lead(id)

# WhatsApp
@app.route("/campanhas/<int:id>/enviar-mensagem", methods=['POST'])
def enviar_mensagem_campanha(id)

# Relatórios
@app.route("/campanhas/<int:id>/relatorio")
def relatorio_campanha(id)

@app.route("/campanhas/<int:id>/exportar-csv")
def exportar_leads_csv(id)
```

---

## 📱 INTEGRAÇÃO COM WHATSAPP

### **Envio Individual**

```python
def enviar_whatsapp_lead(lead_id):
    lead = LeadCampanha.query.get(lead_id)
    campanha = lead.campanha
    
    # Substituir variáveis no template
    mensagem = campanha.mensagem_template
    mensagem = mensagem.replace('{nome}', lead.nome)
    mensagem = mensagem.replace('{empresa}', lead.empresa or '')
    mensagem = mensagem.replace('{produto}', campanha.produto_principal or '')
    
    # Enviar via Z-API
    resultado = enviar_whatsapp_zapi(
        numero=lead.telefone,
        mensagem=mensagem,
        instance_id=current_user.api_instance,
        token_id=current_user.api_token
    )
    
    # Registrar interação
    if lead.historico_interacoes is None:
        lead.historico_interacoes = []
    
    lead.historico_interacoes.append({
        'data': datetime.now().isoformat(),
        'tipo': 'whatsapp',
        'texto': mensagem,
        'status': resultado.get('status')
    })
    
    lead.data_contato = datetime.now()
    lead.canal_contato = 'WhatsApp'
    
    if lead.estagio == 'Novo':
        lead.estagio = 'Contatado'
    
    db.session.commit()
```

### **Disparo em Massa**

```python
def disparar_massa_campanha(campanha_id, estagio=None):
    campanha = Campanha.query.get(campanha_id)
    
    query = LeadCampanha.query.filter_by(campanha_id=campanha_id)
    if estagio:
        query = query.filter_by(estagio=estagio)
    
    leads = query.all()
    
    enviados = 0
    erros = 0
    
    for lead in leads:
        try:
            enviar_whatsapp_lead(lead.id)
            enviados += 1
            time.sleep(2)  # Delay entre mensagens
        except Exception as e:
            erros += 1
            print(f"Erro ao enviar para {lead.nome}: {e}")
    
    return {
        'enviados': enviados,
        'erros': erros,
        'total': len(leads)
    }
```

---

## 📊 DASHBOARD DE CAMPANHA

### **Cards de Métricas**

```html
<div class="row mb-4">
  <div class="col-md-3">
    <div class="metric-card">
      <div class="metric-value">150</div>
      <div class="metric-label">Total de Leads</div>
      <div class="metric-progress">75% da meta</div>
    </div>
  </div>
  
  <div class="col-md-3">
    <div class="metric-card">
      <div class="metric-value">18</div>
      <div class="metric-label">Convertidos</div>
      <div class="metric-progress">12% taxa</div>
    </div>
  </div>
  
  <div class="col-md-3">
    <div class="metric-card">
      <div class="metric-value">R$ 45.000</div>
      <div class="metric-label">Receita Gerada</div>
      <div class="metric-progress">45% da meta</div>
    </div>
  </div>
  
  <div class="col-md-3">
    <div class="metric-card">
      <div class="metric-value">23 dias</div>
      <div class="metric-label">Restantes</div>
      <div class="metric-progress">até 30/11</div>
    </div>
  </div>
</div>
```

### **Gráfico de Funil**

```javascript
// Chart.js - Funil de Conversão
const ctx = document.getElementById('chartFunil').getContext('2d');
new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Novo', 'Contatado', 'Qualificado', 'Proposta', 'Negociação', 'Ganho'],
    datasets: [{
      label: 'Quantidade de Leads',
      data: [150, 98, 52, 32, 22, 18],
      backgroundColor: [
        '#6c757d',
        '#0dcaf0',
        '#ffc107',
        '#fd7e14',
        '#0d6efd',
        '#198754'
      ]
    }]
  },
  options: {
    indexAxis: 'y',  // Horizontal
    responsive: true
  }
});
```

---

## ⚙️ CONFIGURAÇÕES AVANÇADAS

### **Estágios Personalizáveis**

Permitir que o usuário customize os estágios do funil:

```python
class CampanhaEstagio(db.Model):
    """Estágios personalizados para cada campanha"""
    id = db.Column(db.Integer, primary_key=True)
    campanha_id = db.Column(db.Integer, db.ForeignKey('campanha.id'))
    nome = db.Column(db.String(100), nullable=False)
    ordem = db.Column(db.Integer, nullable=False)
    cor = db.Column(db.String(7), default='#6c757d')  # Hex color
```

Exemplos de funis customizados:

**Funil Simples:**
1. Novo
2. Em andamento
3. Fechado

**Funil Complexo:**
1. Lead Frio
2. Lead Morno
3. Lead Quente
4. Reunião Agendada
5. Proposta Enviada
6. Negociação Preço
7. Contrato Enviado
8. Ganho

---

## 🎨 COMPONENTE KANBAN (Drag & Drop)

### **HTML/CSS**

```html
<div class="kanban-board">
  <div class="kanban-column" data-estagio="Novo">
    <div class="kanban-header">
      <h5>🆕 Novo</h5>
      <span class="badge">45</span>
    </div>
    <div class="kanban-cards" id="cards-novo">
      <!-- Cards aqui -->
      <div class="kanban-card" draggable="true" data-lead-id="1">
        <div class="card-title">João Silva</div>
        <div class="card-subtitle">Empresa X</div>
        <div class="card-tags">
          <span class="tag">📞 11999999999</span>
        </div>
      </div>
    </div>
  </div>
  
  <div class="kanban-column" data-estagio="Contatado">
    <!-- ... -->
  </div>
</div>
```

### **JavaScript (Drag & Drop)**

```javascript
// Tornar cards arrastáveis
document.querySelectorAll('.kanban-card').forEach(card => {
  card.addEventListener('dragstart', (e) => {
    e.dataTransfer.setData('lead-id', card.dataset.leadId);
    card.classList.add('dragging');
  });
  
  card.addEventListener('dragend', () => {
    card.classList.remove('dragging');
  });
});

// Permitir drop nas colunas
document.querySelectorAll('.kanban-cards').forEach(column => {
  column.addEventListener('dragover', (e) => {
    e.preventDefault();
  });
  
  column.addEventListener('drop', async (e) => {
    e.preventDefault();
    const leadId = e.dataTransfer.getData('lead-id');
    const novoEstagio = column.closest('.kanban-column').dataset.estagio;
    
    // Mover via AJAX
    const response = await fetch(`/leads/${leadId}/mover`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ estagio: novoEstagio })
    });
    
    if (response.ok) {
      // Mover visualmente
      const card = document.querySelector(`[data-lead-id="${leadId}"]`);
      column.appendChild(card);
      
      // Atualizar contadores
      atualizarContadores();
    }
  });
});
```

---

## 🚀 ROADMAP DE IMPLEMENTAÇÃO

### **FASE 1: MVP (1-2 semanas)**
- ✅ Criar modelos de dados (Campanha, LeadCampanha)
- ✅ Migração do banco de dados
- ✅ Criar rota e template básico de campanhas
- ✅ Listar campanhas
- ✅ Criar campanha manualmente
- ✅ Adicionar lead manualmente

### **FASE 2: Importação (1 semana)**
- ✅ Upload de CSV/Excel
- ✅ Parsing e validação
- ✅ Mapeamento de colunas
- ✅ Importação em lote
- ✅ Detecção de duplicados

### **FASE 3: Funil Kanban (1 semana)**
- ✅ Interface Kanban
- ✅ Drag & drop de leads
- ✅ Atualização de estágios
- ✅ Detalhes do lead (modal)
- ✅ Adicionar observações

### **FASE 4: WhatsApp (3-4 dias)**
- ✅ Templates de mensagem
- ✅ Envio individual
- ✅ Disparo em massa
- ✅ Registro de histórico

### **FASE 5: Relatórios (3-4 dias)**
- ✅ Dashboard de métricas
- ✅ Gráficos (Chart.js)
- ✅ Exportação CSV/Excel
- ✅ Relatório PDF

### **FASE 6: Melhorias (contínuo)**
- ⚙️ Estágios personalizáveis
- ⚙️ Automações (mover lead automaticamente após X dias)
- ⚙️ Integração com Calendário (agendar follow-up)
- ⚙️ Pontuação de leads (lead scoring)
- ⚙️ Notificações push

---

## 💡 DIFERENCIAIS

### **Recursos Premium:**

1. **Lead Scoring Automático**
   - Pontua leads baseado em:
     - Tamanho da empresa
     - Cargo do contato
     - Engajamento (abriu email, respondeu WhatsApp)
     - Histórico de compras

2. **Automação de Fluxo**
   ```
   SE lead não responder em 3 dias
   ENTÃO mover para "Perdido"
   E enviar email de reengajamento
   ```

3. **Integração com Email**
   - Sincronizar com Gmail/Outlook
   - Rastrear aberturas de email
   - Templates de email

4. **Análise Preditiva**
   - Previsão de probabilidade de conversão
   - Sugestão de melhor horário para contato
   - Identificação de padrões de sucesso

---

## 📋 RESUMO EXECUTIVO

### **O QUE SERÁ CRIADO:**

✅ **Sistema de Campanhas** completo integrado ao CRM  
✅ **Importação em massa** via CSV/Excel  
✅ **Funil Kanban** visual para acompanhamento  
✅ **Integração WhatsApp** para contato automatizado  
✅ **Dashboard de métricas** e conversão  
✅ **Relatórios** exportáveis  

### **BENEFÍCIOS:**

📈 **Organização:** Centralizar todas campanhas em um lugar  
🎯 **Produtividade:** Importar centenas de leads em segundos  
👁️ **Visibilidade:** Ver status de cada lead no funil  
🤖 **Automação:** Envios em massa via WhatsApp  
📊 **Análise:** Métricas de conversão em tempo real  

### **INTEGRAÇÃO COM NEGÓCIOS:**

- Lead convertido → cria Mesa de Negócio automaticamente
- Cliente da campanha → vincula ao cadastro do CRM
- Histórico preservado → rastreabilidade completa

---

## 🎬 PRÓXIMOS PASSOS

**Quer que eu comece a implementar?**

1. ✅ Criar os modelos de dados (`Campanha`, `LeadCampanha`)
2. ✅ Criar migration do banco de dados
3. ✅ Criar interface básica (Opção 1: aba em Negócios)
4. ✅ Implementar importação CSV/Excel
5. ✅ Criar funil Kanban

**Ou prefere que eu:**
- 📝 Refine alguma parte específica da proposta?
- 🎨 Crie mockups visuais mais detalhados?
- 💻 Comece direto pelo código?

**Me diga o que acha e qual caminho prefere seguir!** 🚀
