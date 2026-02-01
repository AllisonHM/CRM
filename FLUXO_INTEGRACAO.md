# 🔄 FLUXO DE INTEGRAÇÃO - SITE → CRM

## 📊 Arquitetura da Solução

```
┌─────────────────────────────────────────────────────────────────┐
│                     SITE INSTITUCIONAL                          │
│                   (GitHub Pages / Netlify)                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  index.html                                              │  │
│  │  • Formulário de captação                                │  │
│  │  • Nome, Email, Telefone, Mensagem                       │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  script.js                                               │  │
│  │  • Valida dados (frontend)                               │  │
│  │  • Envia via fetch() para API                            │  │
│  │  • Headers: X-API-Key                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ HTTPS POST
                           │ /api/public/lead
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND CRM                                 │
│                (Railway / Render / Fly.io)                      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  ROTA: /api/public/lead                                  │  │
│  │  • Valida API Key                                        │  │
│  │  • Rate Limit (5 req/min)                                │  │
│  │  • CORS check                                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  VALIDAÇÕES                                              │  │
│  │  • Nome: min 3 chars                                     │  │
│  │  • Email: regex válido                                   │  │
│  │  • Telefone: min 10 dígitos                              │  │
│  │  • Duplicatas: verificar email                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  CRIAR LEAD                                              │  │
│  │  • Tabela: Cliente (existente)                           │  │
│  │  • tipo_pessoa: "Lead Site"                              │  │
│  │  • usuario_crm_id: do .env                               │  │
│  │  • observacoes: data/hora + mensagem                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  BANCO DE DADOS (PostgreSQL)                             │  │
│  │  • INSERT INTO cliente                                   │  │
│  │  • Commit                                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ▼                                      │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  RESPOSTA JSON                                           │  │
│  │  • 201: Sucesso                                          │  │
│  │  • 400: Erro validação                                   │  │
│  │  • 401: API Key inválida                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                           │
                           │ JSON Response
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     USUÁRIO (NAVEGADOR)                         │
│                                                                 │
│  ✅ "Cadastro realizado com sucesso!"                           │
│  ou                                                             │
│  ❌ "Erro: Email já cadastrado"                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Camadas de Segurança

```
┌──────────────────────────────────────────────────────────┐
│  1. HTTPS (TLS)                                          │
│     • GitHub Pages / Netlify: automático                 │
│     • Railway / Render: automático                       │
└──────────────────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────┐
│  2. CORS                                                 │
│     • Apenas origens permitidas (ALLOWED_ORIGINS)        │
│     • Bloqueia chamadas de sites maliciosos              │
└──────────────────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────┐
│  3. API KEY                                              │
│     • Header: X-API-Key                                  │
│     • Valida antes de processar                          │
└──────────────────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────┐
│  4. RATE LIMITING                                        │
│     • 5 requisições/minuto por IP                        │
│     • Previne spam/ataques                               │
└──────────────────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────┐
│  5. VALIDAÇÃO DE DADOS                                   │
│     • Regex para email                                   │
│     • Formato de telefone                                │
│     • Tamanho mínimo de campos                           │
└──────────────────────────────────────────────────────────┘
                      ▼
┌──────────────────────────────────────────────────────────┐
│  6. VERIFICAÇÃO DE DUPLICATAS                            │
│     • Email já existe no banco?                          │
│     • Previne cadastros duplicados                       │
└──────────────────────────────────────────────────────────┘
```

---

## 📂 Estrutura de Dados

### REQUEST (Frontend → Backend)

```json
POST /api/public/lead
Headers:
  Content-Type: application/json
  X-API-Key: minha-chave-secreta-123

Body:
{
  "nome": "João Silva",
  "email": "joao@email.com",
  "telefone": "(11) 98888-7777",
  "mensagem": "Gostaria de saber mais"
}
```

### RESPONSE (Backend → Frontend)

**✅ Sucesso (201):**
```json
{
  "sucesso": true,
  "mensagem": "Cadastro realizado com sucesso!",
  "lead_id": 42
}
```

**❌ Erro de Validação (400):**
```json
{
  "erro": "Dados inválidos",
  "detalhes": [
    "Nome deve ter no mínimo 3 caracteres",
    "Email inválido"
  ],
  "codigo": "VALIDACAO_FALHOU"
}
```

**❌ API Key Inválida (401):**
```json
{
  "erro": "API Key inválida",
  "codigo": "API_KEY_INVALIDA"
}
```

**❌ Email Duplicado (400):**
```json
{
  "erro": "Este email já está cadastrado",
  "codigo": "EMAIL_DUPLICADO"
}
```

---

## 🗄️ Estrutura no Banco de Dados

### Tabela: `cliente` (existente)

```sql
INSERT INTO cliente (
    usuario_crm_id,
    nome,
    email,
    telefone,
    tipo_pessoa,
    observacoes
) VALUES (
    1,                           -- ID do admin (do .env)
    'João Silva',
    'joao@email.com',
    '11988887777',
    'Lead Site',                 -- Identificador de origem
    'Lead capturado do site institucional em 01/02/2026 às 14:30\n\nMensagem: Gostaria de saber mais'
);
```

### Consulta para Ver Leads do Site

```sql
SELECT id, nome, email, telefone, observacoes
FROM cliente
WHERE tipo_pessoa = 'Lead Site'
ORDER BY id DESC;
```

---

## 🔄 Fluxo de Deploy

```
┌─────────────────────────────────────────────────────────┐
│  DESENVOLVEDOR                                          │
└─────────────────────────────────────────────────────────┘
                    │
                    │ 1. Código pronto
                    ▼
┌─────────────────────────────────────────────────────────┐
│  GIT / GITHUB                                           │
│  • Push backend → github.com/user/crm-backend           │
│  • Push frontend → github.com/user/site-crm             │
└─────────────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────────┐  ┌──────────────────┐
│  RAILWAY/RENDER  │  │  GITHUB PAGES    │
│  (Backend)       │  │  (Frontend)      │
│                  │  │                  │
│  • Auto deploy   │  │  • Auto deploy   │
│  • HTTPS auto    │  │  • HTTPS auto    │
│  • Logs          │  │  • CDN global    │
└──────────────────┘  └──────────────────┘
        │                       │
        │                       │
        └───────────┬───────────┘
                    ▼
┌─────────────────────────────────────────────────────────┐
│  USUÁRIO FINAL                                          │
│  • Acessa site                                          │
│  • Preenche formulário                                  │
│  • Vira lead no CRM                                     │
└─────────────────────────────────────────────────────────┘
```

---

## 💰 Custos (FREE TIER)

```
┌──────────────────────────────────────────────────────────┐
│  FRONTEND (GitHub Pages)                                 │
│  • Banda: 100GB/mês                   │ CUSTO: R$ 0      │
│  • Deploy: ilimitado                  │                  │
│  • HTTPS: incluído                    │                  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  BACKEND (Railway)                                       │
│  • Horas: 500h/mês                    │ CUSTO: R$ 0      │
│  • Crédito: $5/mês                    │                  │
│  • HTTPS: incluído                    │                  │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  BANCO DE DADOS (PostgreSQL - Railway/Render)            │
│  • Storage: 1GB                       │ CUSTO: R$ 0      │
│  • Backups: manuais                   │                  │
└──────────────────────────────────────────────────────────┘

                    TOTAL: R$ 0,00/mês 🎉
```

---

## 📈 Capacidade (Free Tier)

- **Leads/dia**: ~100-200 (depende do rate limit)
- **Leads/mês**: ~3.000-6.000
- **Visitantes/mês**: ilimitado (GitHub Pages)
- **Requisições/dia**: ~5.000 (Railway)

**Quando escalar**: Acima de 10.000 leads/mês

---

## ⏱️ Timeline de Implementação

```
DIA 1 (2-3 horas)
├── Hora 1: Instalar dependências + criar .env
├── Hora 2: Adicionar código backend + testar local
└── Hora 3: Deploy backend + frontend

DIA 2 (1 hora)
├── 30min: Testar integração em produção
└── 30min: Ajustes finais + documentação

PRONTO! 🎉
```

---

## 🎯 Métricas de Sucesso

- ✅ Site no ar: `https://usuario.github.io/site-crm`
- ✅ Backend respondendo: `/api/public/health` → 200 OK
- ✅ Formulário funcional: envio sem erros
- ✅ Lead aparece no CRM: tipo_pessoa = "Lead Site"
- ✅ Logs do backend: "✅ Lead capturado"
- ✅ Email não duplica: validação OK

---

## 🔍 Monitoramento

### Backend (Railway/Render)
```
Metrics
├── CPU: < 10% (normal)
├── RAM: < 100MB (normal)
├── Requests/min: monitorar picos
└── Errors: < 1%
```

### Frontend (GitHub Pages)
```
GitHub Insights → Traffic
├── Visitantes/dia
├── Pageviews
└── Origens (direct, social, search)
```

### CRM
```
SQL Query:
SELECT 
  DATE(id) as data,
  COUNT(*) as leads
FROM cliente
WHERE tipo_pessoa = 'Lead Site'
GROUP BY DATE(id)
ORDER BY data DESC;
```

---

**Versão**: 1.0  
**Atualizado**: 01/02/2026
