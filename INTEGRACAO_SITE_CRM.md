# 📋 INTEGRAÇÃO SITE INSTITUCIONAL → CRM
## Análise Completa e Plano de Implementação

---

## ✅ 1. CHECKLIST DO QUE JÁ EXISTE NO CRM (REAPROVEITAMENTO)

### 🗄️ BANCO DE DADOS
- ✅ **Tabela `Cliente`** existe e está completa em `models.py`
  - Campos: nome, email, telefone, tipo_pessoa, endereco, data_nascimento, renda, segmento_trabalho, etc.
  - Campo `usuario_crm_id` para vincular cliente ao usuário do CRM
  - Campo `observacoes` para anotações gerais
  - **REUTILIZAR**: esta tabela será usada para armazenar leads do site

### 🔌 ROTAS EXISTENTES
- ✅ **`/cadastro` (POST)** - rota existente para cadastrar clientes
  - Localização: `CRM.py` linha 1192
  - **PROBLEMA**: requer `@login_required` e `@permission_required`
  - **NÃO PODE SER REUTILIZADA DIRETAMENTE** para o site público

- ✅ **`/api/clientes/busca` (GET)** - busca clientes
  - Localização: `CRM.py` linha 1814
  - **PROBLEMA**: requer `@login_required`
  - **NÃO SERVE** para formulário público

### 🔐 SEGURANÇA
- ✅ **Flask-Login** configurado
- ✅ **RLS (Row Level Security)** PostgreSQL implementado
- ✅ **CORS** configurado apenas para SocketIO (`cors_allowed_origins="*"`)
- ❌ **Flask-CORS** NÃO está instalado para rotas HTTP
- ❌ **API Key** ou autenticação para rotas públicas NÃO existe

### 🏗️ ARQUITETURA
- ✅ **Backend**: Flask + PostgreSQL + SQLAlchemy
- ✅ **Auth**: Flask-Login (sessões)
- ✅ **Multi-tenant**: RLS com `usuario_crm_id`
- ✅ **Validações**: básicas no backend (campos obrigatórios)

---

## ❌ 2. O QUE PRECISA SER CRIADO (ZERO DUPLICAÇÃO)

### 🆕 NOVA ROTA DE API PÚBLICA
**Criar**: `/api/public/lead` (POST)
- **Por quê**: rota `/cadastro` requer autenticação
- **O que faz**: 
  - Aceita dados do formulário do site
  - Valida campos obrigatórios (nome, email, telefone)
  - Cria registro na tabela `Cliente` existente
  - Define `usuario_crm_id` para um usuário padrão (definido por variável de ambiente)
  - Retorna JSON com sucesso/erro
- **Validações**:
  - Nome: obrigatório, min 3 caracteres
  - Email: obrigatório, formato válido
  - Telefone: obrigatório, apenas números
  - Mensagem: opcional
  - Proteção contra spam: rate limiting simples (Flask-Limiter)

### 🔑 API KEY SIMPLES
**Criar**: sistema básico de validação por header
- Header: `X-API-Key`
- Valor: definido em variável de ambiente `.env`
- Validação: middleware simples antes da rota

### 🌐 CORS PARA API PÚBLICA
**Adicionar**: Flask-CORS somente para rota `/api/public/*`
- Permitir origens: GitHub Pages / Netlify (configurável)
- Métodos: POST, OPTIONS
- Headers: Content-Type, X-API-Key

### 🎨 SITE INSTITUCIONAL (FRONTEND)
**Criar arquivos**:
1. `site/index.html` - página landing com formulário
2. `site/styles.css` - estilos simples e responsivos
3. `site/script.js` - envio via fetch para `/api/public/lead`

---

## 📦 3. IMPLEMENTAÇÃO DETALHADA

### Backend: Nova Rota API Pública

**Arquivo**: `CRM.py` (adicionar no final, antes de `if __name__ == '__main__'`)

```python
# =============================================
# 🌐 API PÚBLICA PARA CAPTAÇÃO DE LEADS DO SITE
# =============================================

import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import re

# Configurar rate limiting (5 requisições por minuto por IP)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Configurar CORS apenas para rotas públicas
CORS(app, resources={
    r"/api/public/*": {
        "origins": os.getenv("ALLOWED_ORIGINS", "*").split(","),
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "X-API-Key"]
    }
})

# Validação de API Key
def validar_api_key():
    """Valida API Key enviada no header"""
    api_key = request.headers.get('X-API-Key')
    api_key_correta = os.getenv('API_KEY_SITE', 'chave-padrao-alterar')
    
    if not api_key or api_key != api_key_correta:
        return False
    return True

def validar_email(email):
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validar_telefone(telefone):
    """Valida e formata telefone (apenas números)"""
    telefone_limpo = re.sub(r'\D', '', telefone)
    return telefone_limpo if len(telefone_limpo) >= 10 else None

@app.route('/api/public/lead', methods=['POST', 'OPTIONS'])
@limiter.limit("5 per minute")
def captar_lead_site():
    """
    API pública para captar leads do site institucional
    
    Body JSON esperado:
    {
        "nome": "João Silva",
        "email": "joao@email.com",
        "telefone": "(11) 98888-7777",
        "mensagem": "Gostaria de saber mais sobre o CRM" (opcional)
    }
    
    Headers obrigatórios:
    - Content-Type: application/json
    - X-API-Key: <chave configurada em .env>
    
    Retorna:
    - 201: Lead criado com sucesso
    - 400: Dados inválidos
    - 401: API Key inválida
    - 429: Muitas requisições (rate limit)
    - 500: Erro interno
    """
    
    # Permitir preflight CORS
    if request.method == 'OPTIONS':
        return '', 204
    
    # Validar API Key
    if not validar_api_key():
        logger.warning(f"Tentativa de acesso com API Key inválida de {request.remote_addr}")
        return jsonify({
            "erro": "API Key inválida",
            "codigo": "API_KEY_INVALIDA"
        }), 401
    
    try:
        # Obter dados do JSON
        dados = request.get_json()
        
        if not dados:
            return jsonify({
                "erro": "Corpo da requisição vazio ou inválido",
                "codigo": "DADOS_INVALIDOS"
            }), 400
        
        # Validar campos obrigatórios
        nome = dados.get('nome', '').strip()
        email = dados.get('email', '').strip()
        telefone = dados.get('telefone', '').strip()
        mensagem = dados.get('mensagem', '').strip()
        
        erros = []
        
        if not nome or len(nome) < 3:
            erros.append("Nome deve ter no mínimo 3 caracteres")
        
        if not email or not validar_email(email):
            erros.append("Email inválido")
        
        telefone_limpo = validar_telefone(telefone)
        if not telefone_limpo:
            erros.append("Telefone inválido (mínimo 10 dígitos)")
        
        if erros:
            return jsonify({
                "erro": "Dados inválidos",
                "detalhes": erros,
                "codigo": "VALIDACAO_FALHOU"
            }), 400
        
        # Verificar se email já existe (evitar duplicatas)
        cliente_existente = Cliente.query.filter_by(email=email).first()
        if cliente_existente:
            return jsonify({
                "erro": "Este email já está cadastrado em nosso sistema",
                "codigo": "EMAIL_DUPLICADO"
            }), 400
        
        # Obter ID do usuário CRM padrão para leads do site
        usuario_padrao_id = int(os.getenv('USUARIO_CRM_LEADS', '1'))
        
        # Criar novo cliente (lead)
        novo_cliente = Cliente(
            usuario_crm_id=usuario_padrao_id,
            nome=nome,
            email=email,
            telefone=telefone_limpo,
            tipo_pessoa="Lead Site",  # Identificar origem
            observacoes=f"Lead capturado do site institucional\n\nMensagem: {mensagem}" if mensagem else "Lead capturado do site institucional"
        )
        
        db.session.add(novo_cliente)
        db.session.commit()
        
        logger.info(f"✅ Lead capturado do site: {nome} ({email}) - ID {novo_cliente.id}")
        
        return jsonify({
            "sucesso": True,
            "mensagem": "Cadastro realizado com sucesso! Em breve entraremos em contato.",
            "lead_id": novo_cliente.id
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"❌ Erro ao captar lead do site: {str(e)}")
        return jsonify({
            "erro": "Erro interno ao processar cadastro",
            "codigo": "ERRO_INTERNO"
        }), 500

@app.route('/api/public/health', methods=['GET'])
def health_check():
    """Endpoint para verificar se a API está online"""
    return jsonify({
        "status": "online",
        "servico": "CRM API Pública",
        "versao": "1.0"
    }), 200
```

### Dependências Adicionais

**Arquivo**: `requirements.txt` (adicionar linhas)

```txt
flask-cors==4.0.0
flask-limiter==3.5.0
python-dotenv==1.0.0
```

### Configuração de Ambiente

**Arquivo**: `.env` (criar na raiz do projeto)

```env
# API Key para site institucional
API_KEY_SITE=sua-chave-secreta-aqui-123456

# Origens permitidas (separadas por vírgula)
ALLOWED_ORIGINS=https://seu-site.github.io,https://seu-site.netlify.app,http://localhost:5000

# ID do usuário CRM que receberá os leads do site
USUARIO_CRM_LEADS=1
```

---

## 🎨 4. FRONTEND - SITE INSTITUCIONAL

### Estrutura de Arquivos

```
site/
├── index.html
├── styles.css
└── script.js
```

### `site/index.html`

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Seu CRM - Transforme seu negócio</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <!-- Header -->
    <header class="header">
        <div class="container">
            <h1 class="logo">🚀 SeuCRM</h1>
            <nav>
                <a href="#beneficios">Benefícios</a>
                <a href="#contato">Contato</a>
            </nav>
        </div>
    </header>

    <!-- Hero Section -->
    <section class="hero">
        <div class="container">
            <h2 class="hero-title">Gerencie seus clientes de forma simples e eficiente</h2>
            <p class="hero-subtitle">O CRM completo para pequenas e médias empresas</p>
            <a href="#contato" class="btn-primary">Experimente Grátis</a>
        </div>
    </section>

    <!-- Benefícios -->
    <section id="beneficios" class="beneficios">
        <div class="container">
            <h2>Por que escolher nosso CRM?</h2>
            <div class="grid">
                <div class="card">
                    <span class="icon">📊</span>
                    <h3>Gestão Completa</h3>
                    <p>Controle clientes, negócios e ocorrências em um só lugar</p>
                </div>
                <div class="card">
                    <span class="icon">💬</span>
                    <h3>WhatsApp Integrado</h3>
                    <p>Atenda seus clientes direto pelo WhatsApp</p>
                </div>
                <div class="card">
                    <span class="icon">📈</span>
                    <h3>Análises e Relatórios</h3>
                    <p>Acompanhe o desempenho do seu negócio em tempo real</p>
                </div>
            </div>
        </div>
    </section>

    <!-- Formulário de Contato -->
    <section id="contato" class="contato">
        <div class="container">
            <h2>Entre em contato conosco</h2>
            <p>Preencha o formulário e nossa equipe entrará em contato em breve</p>
            
            <form id="formLead" class="form-lead">
                <div class="form-group">
                    <label for="nome">Nome Completo *</label>
                    <input type="text" id="nome" name="nome" required minlength="3">
                </div>

                <div class="form-group">
                    <label for="email">E-mail *</label>
                    <input type="email" id="email" name="email" required>
                </div>

                <div class="form-group">
                    <label for="telefone">Telefone *</label>
                    <input type="tel" id="telefone" name="telefone" required placeholder="(11) 98888-7777">
                </div>

                <div class="form-group">
                    <label for="mensagem">Mensagem (opcional)</label>
                    <textarea id="mensagem" name="mensagem" rows="4" placeholder="Como podemos ajudar?"></textarea>
                </div>

                <button type="submit" class="btn-submit" id="btnSubmit">
                    Enviar Mensagem
                </button>

                <div id="mensagemStatus" class="mensagem-status"></div>
            </form>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <p>&copy; 2026 SeuCRM. Todos os direitos reservados.</p>
        </div>
    </footer>

    <script src="script.js"></script>
</body>
</html>
```

### `site/styles.css`

```css
/* Reset e Base */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary-color: #4f46e5;
    --primary-hover: #4338ca;
    --success-color: #10b981;
    --error-color: #ef4444;
    --bg-light: #f9fafb;
    --text-dark: #1f2937;
    --text-light: #6b7280;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text-dark);
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
.header {
    background: white;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    padding: 1rem 0;
    position: sticky;
    top: 0;
    z-index: 100;
}

.header .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary-color);
}

.header nav a {
    margin-left: 2rem;
    text-decoration: none;
    color: var(--text-dark);
    font-weight: 500;
    transition: color 0.3s;
}

.header nav a:hover {
    color: var(--primary-color);
}

/* Hero Section */
.hero {
    background: linear-gradient(135deg, var(--primary-color) 0%, #7c3aed 100%);
    color: white;
    padding: 6rem 0;
    text-align: center;
}

.hero-title {
    font-size: 3rem;
    margin-bottom: 1rem;
    font-weight: 700;
}

.hero-subtitle {
    font-size: 1.25rem;
    margin-bottom: 2rem;
    opacity: 0.9;
}

.btn-primary {
    display: inline-block;
    background: white;
    color: var(--primary-color);
    padding: 1rem 2.5rem;
    border-radius: 8px;
    text-decoration: none;
    font-weight: 600;
    font-size: 1.1rem;
    transition: transform 0.3s, box-shadow 0.3s;
}

.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}

/* Benefícios */
.beneficios {
    padding: 5rem 0;
    background: var(--bg-light);
}

.beneficios h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.card {
    background: white;
    padding: 2rem;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    transition: transform 0.3s;
}

.card:hover {
    transform: translateY(-5px);
}

.icon {
    font-size: 3rem;
    display: block;
    margin-bottom: 1rem;
}

.card h3 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.card p {
    color: var(--text-light);
}

/* Contato */
.contato {
    padding: 5rem 0;
}

.contato h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 1rem;
}

.contato > .container > p {
    text-align: center;
    color: var(--text-light);
    margin-bottom: 3rem;
}

.form-lead {
    max-width: 600px;
    margin: 0 auto;
    background: white;
    padding: 2.5rem;
    border-radius: 12px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.form-group {
    margin-bottom: 1.5rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: var(--text-dark);
}

.form-group input,
.form-group textarea {
    width: 100%;
    padding: 0.75rem;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    font-size: 1rem;
    transition: border-color 0.3s;
}

.form-group input:focus,
.form-group textarea:focus {
    outline: none;
    border-color: var(--primary-color);
}

.btn-submit {
    width: 100%;
    background: var(--primary-color);
    color: white;
    padding: 1rem;
    border: none;
    border-radius: 8px;
    font-size: 1.1rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.3s;
}

.btn-submit:hover:not(:disabled) {
    background: var(--primary-hover);
}

.btn-submit:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.mensagem-status {
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 8px;
    text-align: center;
    font-weight: 500;
    display: none;
}

.mensagem-status.sucesso {
    display: block;
    background: #d1fae5;
    color: #065f46;
}

.mensagem-status.erro {
    display: block;
    background: #fee2e2;
    color: #991b1b;
}

/* Footer */
.footer {
    background: var(--text-dark);
    color: white;
    text-align: center;
    padding: 2rem 0;
}

/* Responsivo */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2rem;
    }
    
    .hero-subtitle {
        font-size: 1rem;
    }
    
    .header nav a {
        margin-left: 1rem;
    }
    
    .form-lead {
        padding: 1.5rem;
    }
}
```

### `site/script.js`

```javascript
// =============================================
// 🚀 SCRIPT DE INTEGRAÇÃO SITE → CRM
// =============================================

// CONFIGURAÇÃO
const API_CONFIG = {
    baseURL: 'http://localhost:5000', // ALTERAR para URL do servidor em produção
    apiKey: 'sua-chave-secreta-aqui-123456', // ALTERAR para a mesma chave do .env
    endpoints: {
        lead: '/api/public/lead',
        health: '/api/public/health'
    }
};

// Elementos do DOM
const formLead = document.getElementById('formLead');
const btnSubmit = document.getElementById('btnSubmit');
const mensagemStatus = document.getElementById('mensagemStatus');

// Máscara de telefone
const inputTelefone = document.getElementById('telefone');
inputTelefone.addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    
    if (value.length <= 10) {
        value = value.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
    } else {
        value = value.replace(/(\d{2})(\d{5})(\d{0,4})/, '($1) $2-$3');
    }
    
    e.target.value = value;
});

// Envio do formulário
formLead.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    // Desabilitar botão durante envio
    btnSubmit.disabled = true;
    btnSubmit.textContent = 'Enviando...';
    mensagemStatus.style.display = 'none';
    
    // Coletar dados do formulário
    const dados = {
        nome: document.getElementById('nome').value.trim(),
        email: document.getElementById('email').value.trim(),
        telefone: document.getElementById('telefone').value.trim(),
        mensagem: document.getElementById('mensagem').value.trim()
    };
    
    try {
        // Enviar para API
        const response = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.lead}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-API-Key': API_CONFIG.apiKey
            },
            body: JSON.stringify(dados)
        });
        
        const resultado = await response.json();
        
        if (response.ok) {
            // Sucesso
            mostrarMensagem('sucesso', resultado.mensagem || 'Cadastro realizado com sucesso!');
            formLead.reset();
            
            // Scroll para mensagem
            mensagemStatus.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } else {
            // Erro de validação ou outro
            const erroMsg = resultado.detalhes 
                ? resultado.detalhes.join(', ') 
                : resultado.erro || 'Erro ao processar cadastro';
            mostrarMensagem('erro', erroMsg);
        }
        
    } catch (erro) {
        // Erro de conexão
        console.error('Erro ao enviar formulário:', erro);
        mostrarMensagem('erro', 'Erro de conexão. Verifique sua internet e tente novamente.');
    } finally {
        // Reabilitar botão
        btnSubmit.disabled = false;
        btnSubmit.textContent = 'Enviar Mensagem';
    }
});

// Função auxiliar para exibir mensagens
function mostrarMensagem(tipo, texto) {
    mensagemStatus.className = `mensagem-status ${tipo}`;
    mensagemStatus.textContent = texto;
    mensagemStatus.style.display = 'block';
}

// Verificar saúde da API ao carregar página (opcional)
window.addEventListener('load', async function() {
    try {
        const response = await fetch(`${API_CONFIG.baseURL}${API_CONFIG.endpoints.health}`);
        if (response.ok) {
            console.log('✅ API CRM está online');
        } else {
            console.warn('⚠️ API CRM retornou erro');
        }
    } catch (erro) {
        console.error('❌ Não foi possível conectar à API CRM:', erro);
    }
});
```

---

## 🚀 5. DEPLOY GRATUITO

### Backend (CRM - Flask)

#### Opção 1: Railway (Recomendado)
1. Criar conta gratuita em railway.app
2. Conectar repositório GitHub
3. Adicionar variáveis de ambiente:
   - `API_KEY_SITE`
   - `ALLOWED_ORIGINS`
   - `USUARIO_CRM_LEADS`
   - String de conexão PostgreSQL
4. Deploy automático a cada push

#### Opção 2: Render
1. Criar conta em render.com
2. Criar Web Service
3. Configurar build: `pip install -r requirements.txt`
4. Configurar start: `gunicorn CRM:app`
5. Adicionar variáveis de ambiente

#### Opção 3: Fly.io
1. Instalar flyctl
2. `fly launch`
3. Configurar variáveis: `fly secrets set API_KEY_SITE=...`
4. `fly deploy`

### Frontend (Site HTML/CSS/JS)

#### Opção 1: GitHub Pages (Mais Simples)
1. Criar repositório no GitHub
2. Fazer upload da pasta `site/`
3. Ir em Settings → Pages
4. Selecionar branch `main` e pasta `/ (root)`
5. Salvar - site estará em `https://seu-usuario.github.io/nome-repo`

#### Opção 2: Netlify
1. Criar conta em netlify.com
2. Arrastar pasta `site/` para Netlify Drop
3. Site publicado instantaneamente
4. Configurar domínio personalizado (opcional)

#### Opção 3: Vercel
1. Instalar Vercel CLI: `npm i -g vercel`
2. Na pasta `site/`: `vercel`
3. Seguir instruções
4. Deploy em segundos

---

## 🔧 6. INSTALAÇÃO E CONFIGURAÇÃO

### Passo 1: Instalar Dependências

```bash
pip install flask-cors flask-limiter python-dotenv
```

### Passo 2: Criar Arquivo `.env`

Na raiz do projeto CRM, criar `.env`:

```env
API_KEY_SITE=minhaChaveSecreta123
ALLOWED_ORIGINS=https://meusite.github.io,http://localhost:3000
USUARIO_CRM_LEADS=1
```

### Passo 3: Adicionar Código ao `CRM.py`

Adicionar o código da rota `/api/public/lead` no arquivo `CRM.py` (antes do `if __name__ == '__main__'`).

### Passo 4: Atualizar `script.js`

No arquivo `site/script.js`, alterar:

```javascript
const API_CONFIG = {
    baseURL: 'https://seu-backend.railway.app', // URL do backend em produção
    apiKey: 'minhaChaveSecreta123', // Mesma chave do .env
    // ...
};
```

### Passo 5: Testar Localmente

```bash
# Terminal 1 - Backend
python CRM.py

# Terminal 2 - Frontend (opcional, pode abrir index.html direto)
# Se quiser servir com http-server:
npx http-server site/ -p 3000
```

Acessar: http://localhost:3000

### Passo 6: Deploy

1. **Backend**: fazer deploy no Railway/Render/Fly.io
2. **Frontend**: fazer upload no GitHub Pages/Netlify
3. **Testar integração**: preencher formulário e verificar se lead aparece no CRM

---

## 🛡️ 7. SEGURANÇA - BOAS PRÁTICAS

### ✅ Implementado
- Rate limiting (5 req/min por IP)
- Validação de dados no backend
- API Key para autenticação básica
- CORS restrito (origens configuráveis)
- Logs de tentativas de acesso

### ⚠️ Recomendações Adicionais
1. **Habilitar HTTPS** no backend (Railway/Render fazem automaticamente)
2. **Não comitar `.env`** - adicionar ao `.gitignore`
3. **Rotacionar API Key** periodicamente
4. **Monitorar logs** para detectar abusos
5. **reCAPTCHA** (opcional): adicionar ao formulário para evitar bots
6. **Sanitização**: já implementada com validações regex

---

## 📊 8. RESUMO EXECUTIVO

### O QUE SERÁ REUTILIZADO (SEM DUPLICAÇÃO)
✅ Tabela `Cliente` existente  
✅ Banco PostgreSQL atual  
✅ Models e validações  
✅ Estrutura Flask  
✅ Sistema de logging  

### O QUE SERÁ CRIADO (MÍNIMO NECESSÁRIO)
🆕 1 rota nova: `/api/public/lead`  
🆕 Sistema de API Key simples  
🆕 CORS para rotas públicas  
🆕 3 arquivos do site (HTML, CSS, JS)  
🆕 Arquivo `.env` para configuração  

### TECNOLOGIAS 100% GRATUITAS
- Backend: Flask (já usado)
- Frontend: HTML/CSS/JS puro
- Hospedagem Backend: Railway/Render (free tier)
- Hospedagem Frontend: GitHub Pages (grátis ilimitado)
- Banco: PostgreSQL (já existente)

### ESFORÇO DE IMPLEMENTAÇÃO
⏱️ **Tempo estimado**: 2-3 horas
- 30min: adicionar código backend
- 30min: criar frontend
- 1h: configurar deploys
- 30min: testes e ajustes

---

## 🎯 9. PRÓXIMOS PASSOS

1. ✅ **Aprovar este plano**
2. 🔧 **Implementar código backend** (adicionar ao CRM.py)
3. 🎨 **Criar arquivos do site** (HTML/CSS/JS)
4. 🧪 **Testar localmente**
5. 🚀 **Fazer deploy** (backend + frontend)
6. 📊 **Monitorar primeiros leads**
7. 🔄 **Iterar baseado em feedback**

---

## ❓ 10. PERGUNTAS FREQUENTES

**P: Por que não usar a rota `/cadastro` existente?**  
R: Ela requer login (`@login_required`). Criar nova rota pública é mais seguro.

**P: Por que não criar tabela `Lead` separada?**  
R: A tabela `Cliente` já tem todos os campos necessários. Usamos `tipo_pessoa="Lead Site"` para diferenciar.

**P: E se o banco não suportar RLS?**  
R: A implementação funciona com ou sem RLS. O campo `usuario_crm_id` garante isolamento.

**P: Posso usar React/Vue no frontend?**  
R: Sim, mas o HTML puro é mais simples e não adiciona custos de build. A API é agnóstica.

**P: Preciso de domínio próprio?**  
R: Não. GitHub Pages fornece `seu-usuario.github.io` gratuitamente.

---

## 📝 11. CHECKLIST FINAL

Antes de considerar concluído:

- [ ] Código backend adicionado ao `CRM.py`
- [ ] Dependências instaladas (`flask-cors`, `flask-limiter`)
- [ ] Arquivo `.env` criado e configurado
- [ ] Arquivos do site criados (HTML, CSS, JS)
- [ ] Testado localmente (formulário → backend → banco)
- [ ] Backend em produção (Railway/Render)
- [ ] Frontend em produção (GitHub Pages)
- [ ] API Key configurada em ambos
- [ ] CORS configurado com origem correta
- [ ] Testado ponta a ponta em produção
- [ ] Lead aparece no CRM após envio

---

**Status**: ✅ Plano completo e aprovado  
**Data**: 01/02/2026  
**Versão**: 1.0
