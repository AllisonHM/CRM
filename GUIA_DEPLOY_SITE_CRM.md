# 🚀 GUIA DE DEPLOY - INTEGRAÇÃO SITE → CRM
## Deploy 100% Gratuito (Frontend + Backend)

---

## 📋 PRÉ-REQUISITOS

- Conta GitHub (gratuita)
- Git instalado localmente
- Python 3.8+ (para testes locais)
- Conta Railway/Render/Fly.io (gratuita)

---

## 🎨 PARTE 1: DEPLOY DO FRONTEND (SITE)

### Opção A: GitHub Pages (Recomendado - Mais Simples)

#### Passo 1: Criar Repositório

```bash
# Na pasta do site
cd "c:\Users\Allison\Desktop\CRM completo\CRM\site"

# Inicializar git
git init

# Adicionar arquivos
git add .

# Commit inicial
git commit -m "Initial commit: Site institucional CRM"
```

#### Passo 2: Criar Repositório no GitHub

1. Ir em github.com → New Repository
2. Nome: `site-crm` (ou qualquer nome)
3. Público ou Privado (ambos funcionam)
4. NÃO inicializar com README
5. Criar repositório

#### Passo 3: Push para GitHub

```bash
# Conectar ao repositório remoto
git remote add origin https://github.com/seu-usuario/site-crm.git

# Renomear branch para main
git branch -M main

# Push
git push -u origin main
```

#### Passo 4: Ativar GitHub Pages

1. No repositório → Settings → Pages
2. Source: Deploy from a branch
3. Branch: `main` → `/ (root)`
4. Save

**Site estará disponível em**: `https://seu-usuario.github.io/site-crm/`

⏱️ Tempo: 5-10 minutos para primeira publicação

#### Passo 5: Configurar URL da API

Editar `script.js`:

```javascript
const API_CONFIG = {
    baseURL: 'https://seu-backend.railway.app', // URL do backend (Parte 2)
    apiKey: 'sua-chave-secreta', // Mesma do .env do backend
    // ...
};
```

Commit e push:

```bash
git add script.js
git commit -m "Atualizar URL da API"
git push
```

---

### Opção B: Netlify (Alternativa)

#### Via Interface Web (Drag & Drop)

1. Criar conta em netlify.com
2. Arrastar pasta `site/` para área de upload
3. Aguardar deploy (30 segundos)
4. Site disponível em `https://random-name.netlify.app`
5. Configurar domínio personalizado (opcional)

#### Via Netlify CLI

```bash
# Instalar CLI
npm install -g netlify-cli

# Na pasta do site
cd site/

# Login
netlify login

# Deploy
netlify deploy --prod

# Seguir instruções
```

---

### Opção C: Vercel

```bash
# Instalar Vercel CLI
npm i -g vercel

# Na pasta do site
cd site/

# Deploy
vercel

# Seguir instruções (pressionar Enter para aceitar padrões)
```

---

## 🔧 PARTE 2: DEPLOY DO BACKEND (CRM)

### Opção A: Railway (Recomendado)

#### Passo 1: Preparar Projeto

**Criar `requirements.txt` na raiz do CRM:**

```txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Flask-SocketIO==5.3.5
Flask-Migrate==4.0.5
Flask-CORS==4.0.0
Flask-Limiter==3.5.0
psycopg2-binary==2.9.9
python-dotenv==1.0.0
requests==2.31.0
Werkzeug==3.0.1
```

**Criar `Procfile` na raiz:**

```
web: python CRM.py
```

**Criar `runtime.txt` (opcional):**

```
python-3.11.0
```

#### Passo 2: Adicionar Código ao CRM.py

Adicionar este código **antes** de `if __name__ == '__main__'`:

```python
# Importar código da API pública
# (copiar todo conteúdo de api_publica_leads.py)
```

Ou importar:

```python
from api_publica_leads import *
```

#### Passo 3: Criar Repositório Git

```bash
# Na raiz do projeto CRM
git init
git add .
git commit -m "Deploy: Backend CRM com API pública"

# Criar repositório no GitHub
# Adicionar remote e push
git remote add origin https://github.com/seu-usuario/crm-backend.git
git push -u origin main
```

#### Passo 4: Deploy no Railway

1. Ir em railway.app → Login com GitHub
2. New Project → Deploy from GitHub repo
3. Selecionar repositório `crm-backend`
4. Aguardar build automático

#### Passo 5: Configurar Variáveis de Ambiente

No Railway:
1. Projeto → Settings → Variables
2. Adicionar:

```
API_KEY_SITE=minhaChaveSecreta123
ALLOWED_ORIGINS=https://seu-usuario.github.io
USUARIO_CRM_LEADS=1
SQLALCHEMY_DATABASE_URI=postgresql://...
```

#### Passo 6: Obter URL do Backend

1. Railway → Settings → Domains
2. Generate Domain
3. Copiar URL: `https://seu-projeto.railway.app`

---

### Opção B: Render

#### Passo 1: Preparar Projeto (igual Railway)

#### Passo 2: Deploy no Render

1. Ir em render.com → Criar conta
2. New → Web Service
3. Conectar GitHub → Selecionar repositório
4. Configurações:
   - Name: `crm-backend`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python CRM.py`
5. Environment Variables (adicionar):
   ```
   API_KEY_SITE=...
   ALLOWED_ORIGINS=...
   USUARIO_CRM_LEADS=1
   ```
6. Create Web Service

**Free Tier**: Aplicação hiberna após 15min inatividade (primeira request demora ~30s)

---

### Opção C: Fly.io

```bash
# Instalar flyctl
# Windows (PowerShell):
iwr https://fly.io/install.ps1 -useb | iex

# Login
fly auth login

# Na raiz do CRM
fly launch

# Seguir wizard:
# - App name: crm-backend
# - Region: São Paulo (gru)
# - PostgreSQL: Yes (criar banco gratuito)

# Configurar secrets
fly secrets set API_KEY_SITE=minhaChave123
fly secrets set ALLOWED_ORIGINS=https://seu-site.github.io
fly secrets set USUARIO_CRM_LEADS=1

# Deploy
fly deploy
```

---

## 🔗 PARTE 3: CONECTAR FRONTEND ↔ BACKEND

### Passo 1: Atualizar script.js do Site

```javascript
const API_CONFIG = {
    baseURL: 'https://seu-backend.railway.app', // ← URL obtida no deploy
    apiKey: 'minhaChaveSecreta123', // ← Mesma do .env
    // ...
};
```

### Passo 2: Atualizar ALLOWED_ORIGINS no Backend

No Railway/Render/Fly.io:

```
ALLOWED_ORIGINS=https://seu-usuario.github.io,https://seu-site.netlify.app
```

### Passo 3: Testar Integração

1. Acessar site: `https://seu-usuario.github.io/site-crm/`
2. Preencher formulário
3. Enviar
4. Verificar se lead aparece no CRM

---

## 🧪 PARTE 4: TESTES LOCAIS (ANTES DO DEPLOY)

### Backend

```bash
# Instalar dependências
pip install -r requirements.txt

# Criar .env
cp .env.example .env
# Editar .env com suas configurações

# Rodar servidor
python CRM.py

# Servidor em: http://localhost:5000
```

### Frontend

**Opção 1: Abrir direto no navegador**

```bash
# Windows
start site/index.html
```

**Opção 2: Servidor HTTP simples**

```bash
# Com Python
cd site/
python -m http.server 3000

# Ou com Node.js
npx http-server site/ -p 3000

# Acessar: http://localhost:3000
```

### Testar Integração Local

1. Backend rodando em `http://localhost:5000`
2. Frontend em `http://localhost:3000` ou arquivo local
3. Editar `script.js`:
   ```javascript
   baseURL: 'http://localhost:5000'
   ```
4. Preencher formulário → Enviar
5. Verificar console do navegador (F12)
6. Verificar logs do backend
7. Verificar banco de dados

---

## 🔐 PARTE 5: SEGURANÇA E BOAS PRÁTICAS

### 1. Gerar API Key Forte

```bash
# Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Resultado: algo como
# K7_xNq9Ld2Rf8uHmPv4Yt6Wz1Bc3Gj5Ak8Mn0Qs2Te7
```

### 2. Não Comitar .env

**Criar `.gitignore`:**

```
.env
__pycache__/
*.pyc
instance/
```

### 3. Habilitar HTTPS

- Railway/Render/Fly.io: **automático** ✅
- GitHub Pages: **automático** ✅

### 4. Monitorar Rate Limit

Ver logs do backend:
- Railway: Logs em tempo real no dashboard
- Render: View Logs
- Fly.io: `fly logs`

### 5. Backup do Banco

**PostgreSQL no Railway:**

```bash
# Instalar CLI
npm i -g @railway/cli

# Login
railway login

# Conectar ao projeto
railway link

# Backup
railway run pg_dump $DATABASE_URL > backup.sql
```

---

## 📊 PARTE 6: MONITORAMENTO

### Backend

**Railway/Render:**
- Dashboard → Metrics
- CPU, RAM, Requests por minuto

**Fly.io:**
```bash
fly status
fly logs
```

### Frontend

**GitHub Pages:**
- GitHub Insights → Traffic (visitantes)

**Netlify:**
- Dashboard → Analytics

### Leads Capturados

No CRM, acessar:
- Clientes → Filtrar por "Lead Site"
- Observações: verá data/hora de captura

---

## 🆘 TROUBLESHOOTING

### Erro: CORS

**Sintoma**: No console do navegador:
```
Access to fetch at '...' from origin '...' has been blocked by CORS policy
```

**Solução**:
1. Verificar `ALLOWED_ORIGINS` no backend
2. Adicionar origem do frontend:
   ```
   ALLOWED_ORIGINS=https://seu-site.github.io,http://localhost:3000
   ```
3. Reiniciar backend

---

### Erro: API Key Inválida

**Sintoma**: Resposta 401 "API Key inválida"

**Solução**:
1. Verificar `script.js`: `apiKey` igual ao `API_KEY_SITE` do backend
2. Verificar `.env` do backend
3. Railway: Variables → Verificar valor

---

### Erro: Email Duplicado

**Sintoma**: Resposta 400 "Email já cadastrado"

**Solução**:
- Email já existe no banco
- Verificar no CRM → Clientes
- Normal e esperado (evita duplicatas)

---

### Backend Hiberna (Render Free)

**Sintoma**: Primeira request demora 30+ segundos

**Solução**:
- Normal no free tier do Render
- Alternativas:
  - Upgrade para plano pago ($7/mês)
  - Usar Railway (free tier melhor)
  - Usar Fly.io (free tier com 3 VMs)

---

### Site Não Atualiza

**GitHub Pages**:
- Aguardar 2-5 minutos após push
- Verificar Actions → Pages build
- Limpar cache do navegador (Ctrl+Shift+R)

**Netlify**:
- Deploy é instantâneo (~30s)
- Verificar Deploys → Ver logs

---

## 📝 CHECKLIST FINAL

### Backend
- [ ] Código da API pública adicionado ao CRM.py
- [ ] Dependências instaladas
- [ ] .env configurado
- [ ] Push para GitHub
- [ ] Deploy no Railway/Render/Fly.io
- [ ] Variáveis de ambiente configuradas
- [ ] URL do backend obtida
- [ ] Testado rota `/api/public/health`

### Frontend
- [ ] Arquivos criados (HTML, CSS, JS)
- [ ] `script.js` atualizado com URL do backend
- [ ] `script.js` atualizado com API Key
- [ ] Push para GitHub
- [ ] GitHub Pages ativado
- [ ] URL do site obtida

### Integração
- [ ] ALLOWED_ORIGINS atualizado no backend
- [ ] Testado formulário → backend
- [ ] Lead aparece no CRM
- [ ] Console sem erros

---

## 🎉 CONCLUSÃO

Após seguir este guia:

✅ **Frontend**: Site em `https://seu-usuario.github.io`  
✅ **Backend**: API em `https://seu-projeto.railway.app`  
✅ **Integração**: Funcionando ponta a ponta  
✅ **Custo**: R$ 0,00 (100% gratuito)  
✅ **HTTPS**: Automático em ambos  
✅ **Escalável**: Suporta centenas de leads/mês  

---

**Suporte**: Em caso de dúvidas, revisar os logs do backend e console do navegador (F12).

**Próximos Passos**:
1. Testar em produção
2. Divulgar site
3. Monitorar primeiros leads
4. Adicionar Google Analytics (opcional)
5. Configurar domínio personalizado (opcional)
