# 🚀 GUIA COMPLETO DE DEPLOY NA LOCAWEB

## 📋 CHECKLIST COMPLETO - TUDO QUE VOCÊ PRECISA

### ✅ 1. REQUISITOS DA LOCAWEB

#### Plano Necessário:
- **Hospedagem Python** (Cloud ou VPS)
- **Banco de dados PostgreSQL** (geralmente incluído)
- **SSL/HTTPS** (importante para WhatsApp e segurança)
- **Domínio próprio** (obrigatório para Z-API funcionar)

#### Especificações Mínimas Recomendadas:
- **RAM**: 2GB mínimo (4GB recomendado)
- **CPU**: 2 cores
- **Storage**: 20GB SSD
- **Python**: 3.10+
- **PostgreSQL**: 12+

---

## 📦 2. ARQUIVOS QUE VOCÊ PRECISA CRIAR/AJUSTAR

### 2.1 `wsgi.py` (Arquivo de entrada)

```python
"""
WSGI Entry Point para Locaweb
"""
import sys
import os

# Adicionar diretório do projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

from CRM import app as application

if __name__ == "__main__":
    application.run()
```

### 2.2 `runtime.txt` (Versão do Python)

```
python-3.10.8
```

### 2.3 `.env` (Variáveis de ambiente - NÃO COMMITAR!)

```bash
# Banco de Dados (fornecido pela Locaweb)
DATABASE_URL=postgresql://usuario:senha@host:5432/nome_banco
SQLALCHEMY_DATABASE_URI=postgresql://usuario:senha@host:5432/nome_banco

# Flask
FLASK_APP=CRM.py
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_muito_longa_e_aleatoria_aqui

# Segurança
WTF_CSRF_ENABLED=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# Upload
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=/home/seu_usuario/public_html/static/uploads

# Email (se usar)
MAIL_SERVER=smtp.locaweb.com.br
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu_email@seudominio.com.br
MAIL_PASSWORD=sua_senha_email

# Logs
LOG_LEVEL=INFO
LOG_FILE=/home/seu_usuario/logs/crm.log
```

### 2.4 `.htaccess` (Configuração Apache - Locaweb usa Apache)

```apache
# Força HTTPS
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Configuração Python
AddHandler wsgi-script .wsgi
Options +ExecCGI
DirectoryIndex wsgi.py

# Headers de segurança
Header always set X-Frame-Options "SAMEORIGIN"
Header always set X-Content-Type-Options "nosniff"
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"

# Proteção de arquivos sensíveis
<FilesMatch "^\.env$">
    Order allow,deny
    Deny from all
</FilesMatch>

<FilesMatch "\.py$">
    Order allow,deny
    Deny from all
</FilesMatch>

# Exceto WSGI
<FilesMatch "wsgi\.py$">
    Order allow,deny
    Allow from all
</FilesMatch>

# Cache para arquivos estáticos
<FilesMatch "\.(jpg|jpeg|png|gif|css|js|ico|svg|woff|woff2|ttf)$">
    Header set Cache-Control "max-age=2592000, public"
</FilesMatch>
```

### 2.5 `passenger_wsgi.py` (Locaweb usa Passenger)

```python
"""
Passenger WSGI para Locaweb
"""
import sys
import os

# Ativar ambiente virtual (ajuste o caminho)
INTERP = os.path.join(os.environ['HOME'], 'virtualenv', 'python3.10', 'bin', 'python3')
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Adicionar projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

# Importar aplicação
from CRM import app as application
```

### 2.6 `requirements.txt` (Já existe - verificar se está completo)

Seu arquivo já está OK! Mas certifique-se de ter:

```
python-dotenv>=1.0.0
gunicorn>=21.0.0
```

---

## 🔧 3. AJUSTES NO CÓDIGO

### 3.1 Criar `config_production.py`

```python
"""
Configurações para ambiente de produção
"""
import os
from datetime import timedelta

class ProductionConfig:
    # Banco de dados
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }
    
    # Segurança
    SECRET_KEY = os.environ.get('SECRET_KEY')
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    
    # Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/tmp/uploads')
    
    # Flask
    DEBUG = False
    TESTING = False
    
    # Logs
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', '/tmp/crm.log')
```

### 3.2 Modificar `CRM.py` para usar config de produção

No início do arquivo `CRM.py`, adicione:

```python
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# ... seu código existente ...

# Antes de app.run(), adicione:
if os.environ.get('FLASK_ENV') == 'production':
    from config_production import ProductionConfig
    app.config.from_object(ProductionConfig)
```

---

## 📊 4. PREPARAR BANCO DE DADOS

### 4.1 Exportar dados locais (se necessário)

```bash
# Exportar dados do PostgreSQL local
pg_dump -U seu_usuario -d nome_banco -f backup_dados.sql

# Ou apenas a estrutura
pg_dump -U seu_usuario -d nome_banco --schema-only -f backup_estrutura.sql
```

### 4.2 Script para criar estrutura no servidor

Criar `setup_database_producao.py`:

```python
"""
Script para criar estrutura do banco em produção
"""
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente de produção
load_dotenv('.env.production')

from database_rls import db
from CRM import app

def criar_estrutura():
    """Cria todas as tabelas no banco de produção"""
    with app.app_context():
        print("🗄️  Criando estrutura do banco de dados...")
        db.create_all()
        print("✅ Estrutura criada com sucesso!")
        
        # Aplicar índices
        print("📊 Aplicando índices de performance...")
        from aplicar_indices import aplicar_indices
        aplicar_indices()
        print("✅ Índices aplicados!")

if __name__ == '__main__':
    criar_estrutura()
```

---

## 🌐 5. PASSOS DO DEPLOY NA LOCAWEB

### PASSO 1: Contratar Hospedagem

1. Acesse **painel.locaweb.com.br**
2. Contrate plano com **Python + PostgreSQL**
3. Ative o **SSL/HTTPS** (geralmente grátis com Let's Encrypt)
4. Configure seu **domínio** (ex: crm.seudominio.com.br)

### PASSO 2: Configurar Banco de Dados

1. No painel Locaweb, vá em **Banco de Dados → PostgreSQL**
2. Crie um novo banco:
   - Nome: `crm_producao`
   - Usuário: (será criado automaticamente)
   - Senha: (anote!)
3. Anote as credenciais:
   - Host: `pgsql.locaweb.com.br` (ou similar)
   - Porta: `5432`
   - Database: `crm_producao`
   - User: `seu_usuario`
   - Password: `sua_senha`

### PASSO 3: Acessar via SSH

```bash
# Conectar via SSH (dados fornecidos pela Locaweb)
ssh seu_usuario@seu_dominio.com.br

# Ou usar o terminal do painel
```

### PASSO 4: Criar Ambiente Virtual

```bash
# No servidor
cd ~
python3.10 -m venv virtualenv/python3.10
source virtualenv/python3.10/bin/activate

# Atualizar pip
pip install --upgrade pip
```

### PASSO 5: Fazer Upload dos Arquivos

**Opção A: Via FTP (FileZilla)**

1. Conecte via FTP nas credenciais da Locaweb
2. Faça upload de:
   - Todos os arquivos `.py`
   - Pasta `templates/`
   - Pasta `static/`
   - `requirements.txt`
   - `.env` (configurado com dados de produção)
   - `passenger_wsgi.py`
   - `.htaccess`

**Opção B: Via Git (recomendado)**

```bash
# No servidor
cd ~/public_html
git clone https://seu-repositorio.git .

# Ou fazer upload via rsync
rsync -avz --exclude='.git' --exclude='*.pyc' \
  /caminho/local/CRM/ usuario@servidor:~/public_html/
```

### PASSO 6: Instalar Dependências

```bash
# No servidor, com venv ativado
cd ~/public_html
source ~/virtualenv/python3.10/bin/activate
pip install -r requirements.txt
```

### PASSO 7: Configurar Variáveis de Ambiente

```bash
# Editar .env com dados de produção
nano .env

# Adicionar as variáveis corretas (DATABASE_URL, SECRET_KEY, etc.)
```

### PASSO 8: Criar Estrutura do Banco

```bash
# Com venv ativado
python setup_database_producao.py

# Ou via Flask-Migrate
export FLASK_APP=CRM.py
flask db upgrade
python aplicar_indices.py
```

### PASSO 9: Criar Usuário Admin Inicial

```bash
python criar_usuario_crm.py
```

### PASSO 10: Configurar Permissões

```bash
# Ajustar permissões
chmod 755 ~/public_html
chmod 644 ~/public_html/*.py
chmod 755 ~/public_html/passenger_wsgi.py

# Criar diretórios necessários
mkdir -p ~/public_html/logs
mkdir -p ~/public_html/static/uploads/canais
chmod 755 ~/public_html/static/uploads -R
```

### PASSO 11: Reiniciar Aplicação

```bash
# Criar/tocar arquivo restart.txt (Passenger)
touch ~/public_html/tmp/restart.txt

# Ou via painel da Locaweb:
# Aplicações → Reiniciar Aplicação Python
```

### PASSO 12: Testar!

Acesse: `https://crm.seudominio.com.br`

---

## 🔍 6. VERIFICAÇÕES PÓS-DEPLOY

### Checklist de Teste:

- [ ] Site carrega sem erros
- [ ] Login funciona
- [ ] Banco de dados conecta
- [ ] HTTPS está ativo (cadeado verde)
- [ ] Upload de arquivos funciona
- [ ] WhatsApp envia mensagens (com URL pública!)
- [ ] Logs estão sendo gravados
- [ ] Sessões funcionam
- [ ] Emails são enviados (se configurado)

### Comandos de Diagnóstico:

```bash
# Ver logs da aplicação
tail -f ~/public_html/logs/crm.log

# Ver logs do Passenger
tail -f ~/passenger_logs/error.log

# Testar conectividade do banco
psql -h pgsql.locaweb.com.br -U seu_usuario -d crm_producao -c "SELECT 1"

# Verificar processos Python
ps aux | grep python
```

---

## ⚠️ 7. PROBLEMAS COMUNS E SOLUÇÕES

### Problema 1: "502 Bad Gateway"

**Causa**: Erro no código Python ou dependências faltando

**Solução**:
```bash
# Ver logs
tail -50 ~/passenger_logs/error.log

# Reinstalar dependências
pip install -r requirements.txt --upgrade
touch ~/public_html/tmp/restart.txt
```

### Problema 2: "Database connection failed"

**Causa**: Credenciais erradas ou banco não criado

**Solução**:
```bash
# Verificar .env
cat .env | grep DATABASE_URL

# Testar conexão
psql -h HOST -U USER -d DATABASE

# Verificar se tabelas existem
psql -h HOST -U USER -d DATABASE -c "\dt"
```

### Problema 3: "Permission denied" em uploads

**Causa**: Permissões de diretório

**Solução**:
```bash
chmod 755 ~/public_html/static/uploads -R
chown seu_usuario:seu_usuario ~/public_html/static/uploads -R
```

### Problema 4: WhatsApp não envia arquivos

**Causa**: Z-API precisa de URL pública (não funciona com localhost)

**Solução**:
- ✅ Agora vai funcionar! Seu domínio público permite que a Z-API acesse os arquivos
- Certifique-se de que a pasta uploads está acessível publicamente

### Problema 5: Sessões não persistem

**Causa**: SECRET_KEY mudando a cada restart

**Solução**:
```bash
# Gerar SECRET_KEY fixa
python -c "import secrets; print(secrets.token_hex(32))"

# Adicionar ao .env
echo "SECRET_KEY=chave_gerada_acima" >> .env
```

---

## 🔐 8. SEGURANÇA ESSENCIAL

### 8.1 Arquivos que NÃO DEVEM estar acessíveis:

```apache
# Adicionar ao .htaccess
<FilesMatch "^(\.env|\.git|backup.*\.sql|.*\.pyc)$">
    Order allow,deny
    Deny from all
</FilesMatch>
```

### 8.2 Firewall e IPs (painel Locaweb):

- Permitir apenas portas 80, 443
- Bloquear acessos suspeitos
- Habilitar proteção DDoS (se disponível)

### 8.3 Backup Automático:

```bash
# Criar script de backup
nano ~/backup_diario.sh
```

Conteúdo:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -h HOST -U USER -d DATABASE > ~/backups/crm_$DATE.sql
find ~/backups -name "crm_*.sql" -mtime +7 -delete  # Remove backups com +7 dias
```

```bash
# Tornar executável
chmod +x ~/backup_diario.sh

# Adicionar ao cron (diário às 3AM)
crontab -e
# Adicionar linha:
0 3 * * * /home/seu_usuario/backup_diario.sh
```

---

## 📱 9. PREPARAR PARA O APP MOBILE (FUTURO)

Agora que vai subir na internet, você está pronto para criar o app! Mas primeiro:

### 9.1 Criar API REST (recomendado)

O app mobile vai precisar de endpoints API. Crie `api_routes.py`:

```python
"""
API REST para App Mobile
"""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from services import ClienteService, MesaService
from utils import ValidationError

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

@api_bp.route('/clientes', methods=['GET'])
@login_required
def listar_clientes():
    """Lista clientes paginados"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        
        clientes, total = ClienteService.listar_clientes(
            usuario_crm_id=current_user.get_usuario_principal_id(),
            page=page,
            per_page=per_page
        )
        
        return jsonify({
            'success': True,
            'data': [c.to_dict() for c in clientes],
            'total': total,
            'page': page,
            'per_page': per_page
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Adicionar mais endpoints...
```

Registrar no `CRM.py`:
```python
from api_routes import api_bp
app.register_blueprint(api_bp)
```

### 9.2 Habilitar CORS (para app consumir a API)

```bash
pip install flask-cors
```

No `CRM.py`:
```python
from flask_cors import CORS

# Permitir apenas seu app
CORS(app, resources={
    r"/api/*": {
        "origins": ["capacitor://localhost", "ionic://localhost", "http://localhost:*"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

---

## 🎯 10. CRONOGRAMA RECOMENDADO

### Semana 1: Deploy do Backend
- [ ] Contratar Locaweb
- [ ] Configurar domínio e SSL
- [ ] Fazer deploy do CRM
- [ ] Testar todas as funcionalidades
- [ ] Criar backups automáticos

### Semana 2: Preparar APIs
- [ ] Criar endpoints REST
- [ ] Documentar API (Swagger)
- [ ] Testar APIs com Postman
- [ ] Habilitar CORS

### Semana 3-4: Desenvolver App
- [ ] Escolher framework (React Native, Flutter, Ionic)
- [ ] Criar protótipos
- [ ] Integrar com API
- [ ] Testar em dispositivos

### Semana 5: Launch
- [ ] Deploy app nas lojas (Google Play / App Store)
- [ ] Monitoramento
- [ ] Ajustes finais

---

## 📞 SUPORTE LOCAWEB

- **Telefone**: 0800 054 4040
- **Chat**: painel.locaweb.com.br
- **Documentação Python**: ajuda.locaweb.com.br

---

## ✅ RESUMO - O QUE VOCÊ PRECISA FAZER

1. **Contratar**: Hospedagem Python + PostgreSQL na Locaweb
2. **Criar arquivos**: `.env`, `passenger_wsgi.py`, `.htaccess`
3. **Upload**: Enviar código via FTP ou Git
4. **Configurar**: Banco de dados e variáveis de ambiente
5. **Instalar**: Dependências no servidor
6. **Migrar**: Estrutura e dados do banco
7. **Testar**: Todas as funcionalidades
8. **Monitorar**: Logs e performance

**Tempo estimado**: 4-8 horas para primeiro deploy

**Custo estimado Locaweb**: R$ 50-150/mês (plano Python + PostgreSQL)

---

## 🚀 PRÓXIMO PASSO

**RECOMENDAÇÃO**: Suba primeiro na internet!

**Por quê?**
1. ✅ WhatsApp funcionará 100% (Z-API precisa de URL pública)
2. ✅ Você poderá testar com usuários reais
3. ✅ API estará pronta quando criar o app
4. ✅ Backups automáticos protegerão dados
5. ✅ App mobile consumirá API do servidor (não código duplicado)

Quer que eu crie os arquivos necessários para o deploy agora?
