# 📦 ARQUIVOS CRIADOS PARA DEPLOY NA LOCAWEB

Este documento lista todos os arquivos criados para facilitar seu deploy.

---

## ✅ ARQUIVOS ESSENCIAIS (OBRIGATÓRIOS)

### 1. `passenger_wsgi.py` ⭐ OBRIGATÓRIO
**O que é:** Arquivo de entrada da aplicação no servidor Locaweb  
**Para que serve:** O Passenger (servidor web da Locaweb) usa este arquivo para iniciar o CRM  
**O que fazer:** 
- Upload para a raiz do site (`~/public_html/`)
- Ajustar caminho do virtualenv se necessário
- Permissão: `chmod 755 passenger_wsgi.py`

---

### 2. `.env` ⭐ OBRIGATÓRIO (NÃO COMMITAR NO GIT!)
**O que é:** Arquivo com variáveis de ambiente  
**Para que serve:** Armazena senhas, URLs do banco, chaves secretas  
**O que fazer:**
1. Copiar `.env.production.example` e renomear para `.env`
2. Preencher com dados reais da Locaweb:
   - `DATABASE_URL` (fornecido pela Locaweb)
   - `SECRET_KEY` (gerar com: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `UPLOAD_FOLDER` (caminho no servidor)
   - `DOMAIN` (seu domínio completo)
3. Upload para raiz
4. Permissão: `chmod 600 .env` (apenas você pode ler)

**⚠️ IMPORTANTE:** Adicionar `.env` ao `.gitignore` para não expor senhas!

---

### 3. `.htaccess` ⭐ OBRIGATÓRIO
**O que é:** Configuração do Apache (servidor web da Locaweb)  
**Para que serve:**
- Força HTTPS (segurança)
- Configura headers de segurança
- Protege arquivos sensíveis (.env, .py)
- Cache de arquivos estáticos

**O que fazer:**
- Upload para raiz (`~/public_html/`)
- Ajustar caminho do virtualenv na linha `PassengerPython`
- Permissão: `chmod 644 .htaccess`

---

### 4. `config_production.py` ⭐ OBRIGATÓRIO
**O que é:** Configurações específicas para produção  
**Para que serve:** 
- Configurações de segurança (HTTPS, CSRF)
- Pool de conexões do banco
- Limites de upload
- Logs

**O que fazer:**
- Upload para raiz
- Integrar no `CRM.py` (adicionar no início):
```python
import os
if os.environ.get('FLASK_ENV') == 'production':
    from config_production import ProductionConfig
    app.config.from_object(ProductionConfig)
```

---

### 5. `runtime.txt` (Opcional mas recomendado)
**O que é:** Especifica versão do Python  
**Para que serve:** Garante que o servidor use Python 3.10  
**O que fazer:**
- Upload para raiz
- Conteúdo: `python-3.10.8`

---

## 📚 GUIAS E DOCUMENTAÇÃO

### 6. `GUIA_DEPLOY_LOCAWEB.md` 📖
**O que é:** Guia completo e detalhado de deploy  
**Conteúdo:**
- Requisitos da Locaweb
- Passo a passo completo
- Arquivos necessários
- Configuração do banco
- Troubleshooting
- Preparação para app mobile

**Quando usar:** Ler ANTES de começar o deploy

---

### 7. `CHECKLIST_DEPLOY.md` ✅
**O que é:** Checklist interativo  
**Conteúdo:**
- Lista de verificação antes do deploy
- Lista de verificação durante deploy
- Lista de verificação após deploy
- Testes essenciais

**Quando usar:** Marcar cada item conforme faz o deploy

---

### 8. `PLANEJAMENTO_APP_MOBILE.md` 📱
**O que é:** Guia de planejamento para app mobile  
**Conteúdo:**
- Recomendação: web primeiro ou app primeiro?
- Comparação de frameworks (Flutter, React Native, Ionic)
- Cronograma estimado
- Custos
- O que precisa no backend

**Quando usar:** Após deploy web, para planejar o app

---

### 9. `comandos_locaweb.sh` 💻
**O que é:** Comandos úteis do dia a dia  
**Conteúdo:**
- Ver logs
- Reiniciar aplicação
- Backup do banco
- Verificar status
- Troubleshooting

**Quando usar:** Referência rápida para gerenciar o servidor

---

## 🔧 SCRIPTS AUXILIARES

### 10. `setup_database_producao.py` 🗄️
**O que é:** Script para criar estrutura do banco em produção  
**Para que serve:**
- Cria todas as tabelas
- Aplica índices de performance
- Verifica estrutura

**Quando usar:**
```bash
# Após fazer upload, executar:
cd ~/public_html
source ~/virtualenv/python3.10/bin/activate
python setup_database_producao.py
```

---

### 11. `aplicar_indices.py` 📊
**O que é:** Script para criar índices de performance  
**Para que serve:** Otimiza queries do banco (até 80% mais rápido)

**Quando usar:**
```bash
# Após criar banco, executar:
python aplicar_indices.py
```

---

### 12. `.env.production.example` 📝
**O que é:** Exemplo de arquivo `.env`  
**Para que serve:** Template para criar seu `.env` real

**O que fazer:**
1. Copiar: `cp .env.production.example .env`
2. Editar `.env` com dados reais
3. NUNCA fazer commit de `.env` (apenas do `.example`)

---

## 📋 ESTRUTURA DE DIRETÓRIOS NO SERVIDOR

Após deploy completo, sua estrutura será:

```
~/public_html/
├── .env                          ⚠️  SEGREDO (não commitar)
├── .htaccess                     ✅ Configuração Apache
├── passenger_wsgi.py             ✅ Entrada da aplicação
├── config_production.py          ✅ Config produção
├── runtime.txt                   ✅ Versão Python
├── CRM.py                        ✅ Aplicação principal
├── database_rls.py               ✅ Banco de dados
├── models.py                     ✅ Models
├── routes.py                     ✅ Rotas (se usar)
├── setup_database_producao.py    🔧 Script inicial
├── aplicar_indices.py            🔧 Otimização
├── criar_usuario_crm.py          🔧 Criar admin
├── requirements.txt              📦 Dependências
│
├── config/                       📁 Configurações
│   ├── constants.py
│   └── __init__.py
│
├── utils/                        📁 Utilitários
│   ├── validators.py
│   ├── exceptions.py
│   ├── logger.py
│   └── __init__.py
│
├── services/                     📁 Lógica de negócio
│   ├── cliente_service.py
│   ├── mesa_service.py
│   ├── whatsapp_service.py
│   └── __init__.py
│
├── templates/                    📁 HTML
│   ├── menu.html
│   ├── canais.html
│   ├── detalhe_cliente.html
│   └── ...
│
├── static/                       📁 Arquivos estáticos
│   ├── css/
│   ├── js/
│   ├── images/
│   └── uploads/                  📁 Arquivos enviados
│       └── canais/
│
├── logs/                         📁 Logs (criar)
│   └── crm.log
│
└── tmp/                          📁 Temp (criar)
    └── restart.txt               🔄 Toque para reiniciar
```

---

## 🚀 ORDEM DE EXECUÇÃO (RESUMO)

### 1️⃣ ANTES DO DEPLOY (Local)
```bash
# 1. Gerar SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# 2. Criar .env com dados de produção
cp .env.production.example .env
# Editar .env com dados da Locaweb

# 3. Testar localmente
python CRM.py
```

### 2️⃣ UPLOAD PARA SERVIDOR
```bash
# Via FTP, Git ou rsync
# Fazer upload de TODOS os arquivos
```

### 3️⃣ NO SERVIDOR (SSH)
```bash
# 1. Criar ambiente virtual
cd ~
python3.10 -m venv virtualenv/python3.10
source virtualenv/python3.10/bin/activate

# 2. Instalar dependências
cd ~/public_html
pip install -r requirements.txt

# 3. Criar estrutura do banco
python setup_database_producao.py

# 4. Criar usuário admin
python criar_usuario_crm.py

# 5. Ajustar permissões
chmod 755 ~/public_html
chmod 755 passenger_wsgi.py
chmod 600 .env
chmod 755 static/uploads -R

# 6. Criar diretórios
mkdir -p logs tmp static/uploads/canais

# 7. Reiniciar aplicação
touch tmp/restart.txt
```

### 4️⃣ TESTAR
```
Acessar: https://crm.seudominio.com.br
```

---

## ✅ ARQUIVOS QUE VOCÊ JÁ TEM (NÃO PRECISA CRIAR)

- ✅ `CRM.py` - Aplicação principal
- ✅ `database_rls.py` - Conexão com banco
- ✅ `models.py` - Models do banco
- ✅ `requirements.txt` - Dependências
- ✅ `templates/` - Todos os HTML
- ✅ `static/` - CSS, JS, imagens
- ✅ `config/constants.py` - Constantes
- ✅ `utils/validators.py` - Validadores
- ✅ `utils/exceptions.py` - Exceções
- ✅ `utils/logger.py` - Logger
- ✅ `services/` - Todos os services
- ✅ `tests/` - Testes unitários

---

## ❌ ARQUIVOS QUE NÃO DEVEM IR PARA PRODUÇÃO

- ❌ `.env.local` - Configuração local
- ❌ `*.pyc` - Cache Python
- ❌ `__pycache__/` - Cache
- ❌ `.git/` - Repositório Git
- ❌ `venv/` ou `.venv/` - Ambiente virtual local
- ❌ `*.log` - Logs locais
- ❌ `backup_*.sql` - Backups locais
- ❌ `.vscode/` - Configurações do editor
- ❌ `.idea/` - Configurações do PyCharm

Adicionar ao `.gitignore`:
```
.env
*.pyc
__pycache__/
.venv/
venv/
*.log
backup_*.sql
.vscode/
.idea/
```

---

## 🆘 AJUDA RÁPIDA

### Site não carrega?
1. Ver logs: `tail -50 ~/passenger_logs/error.log`
2. Verificar .env: `cat .env | grep DATABASE_URL`
3. Reiniciar: `touch ~/public_html/tmp/restart.txt`

### Erro de banco?
1. Testar conexão: `psql -h HOST -U USER -d DATABASE`
2. Verificar tabelas: `psql ... -c '\dt'`
3. Recriar estrutura: `python setup_database_producao.py`

### Upload não funciona?
1. Criar diretório: `mkdir -p ~/public_html/static/uploads/canais`
2. Permissões: `chmod 755 ~/public_html/static/uploads -R`

---

## 📞 SUPORTE

- **Locaweb**: 0800 054 4040
- **Painel**: painel.locaweb.com.br
- **Docs**: ajuda.locaweb.com.br

---

## ✅ RESUMO - ARQUIVOS ESSENCIAIS

| Arquivo | Obrigatório | O que fazer |
|---------|-------------|-------------|
| `passenger_wsgi.py` | ✅ SIM | Upload + chmod 755 |
| `.env` | ✅ SIM | Criar com dados reais + chmod 600 |
| `.htaccess` | ✅ SIM | Upload + ajustar paths |
| `config_production.py` | ✅ SIM | Upload + integrar no CRM.py |
| `runtime.txt` | ⚠️  Recomendado | Upload |
| `setup_database_producao.py` | ✅ SIM | Upload + executar |
| `GUIA_DEPLOY_LOCAWEB.md` | 📖 Leitura | Ler antes de começar |
| `CHECKLIST_DEPLOY.md` | ✅ Checklist | Marcar durante deploy |

**Total de arquivos novos criados:** 12  
**Arquivos obrigatórios:** 5  
**Tempo estimado de deploy:** 4-8 horas (primeiro deploy)

---

**Tudo pronto para o deploy! 🚀**
