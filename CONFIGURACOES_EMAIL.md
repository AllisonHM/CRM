# 📧 CONFIGURAÇÕES DE EMAIL PARA DIFERENTES PROVEDORES

## 🎯 Copie e cole no CRM.py (linha ~30)

---

## 1️⃣ GMAIL (Recomendado) ✅

### Como configurar:

1. Vá para: https://myaccount.google.com/security
2. Ative "Verificação em duas etapas"
3. Clique em "Senhas de app"
4. Crie uma senha de app para "CRM System"
5. Copie a senha gerada (16 caracteres, sem espaços)

### Configuração:

```python
# ------------------- CONFIGURAÇÕES DE EMAIL -------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'  # Seu Gmail
app.config['MAIL_PASSWORD'] = 'xxxx xxxx xxxx xxxx'  # Senha de app (cole sem espaços)
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@gmail.com'
```

**Alternativa com SSL:**
```python
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'xxxx xxxx xxxx xxxx'
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@gmail.com'
```

---

## 2️⃣ OUTLOOK / HOTMAIL

```python
# ------------------- CONFIGURAÇÕES DE EMAIL -------------------
app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@outlook.com'  # ou @hotmail.com
app.config['MAIL_PASSWORD'] = 'sua_senha'  # Senha normal da conta
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@outlook.com'
```

---

## 3️⃣ YAHOO MAIL

### Como configurar:

1. Vá para: https://login.yahoo.com/account/security
2. Gere uma senha de app
3. Use essa senha na configuração

```python
# ------------------- CONFIGURAÇÕES DE EMAIL -------------------
app.config['MAIL_SERVER'] = 'smtp.mail.yahoo.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@yahoo.com'
app.config['MAIL_PASSWORD'] = 'senha_de_app'  # Senha de app do Yahoo
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@yahoo.com'
```

---

## 4️⃣ SENDGRID (Profissional)

### Como configurar:

1. Crie conta em: https://sendgrid.com
2. Vá em Settings > API Keys
3. Crie uma API Key
4. Copie a key

```python
# ------------------- CONFIGURAÇÕES DE EMAIL -------------------
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'  # Literalmente "apikey"
app.config['MAIL_PASSWORD'] = 'SG.xxxxxxxxxxxxxxxx'  # Sua API Key
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@seudominio.com'
```

**Vantagens:**
- ✅ 100 emails/dia grátis
- ✅ Profissional e confiável
- ✅ Estatísticas e relatórios

---

## 5️⃣ MAILGUN (Profissional)

```python
# ------------------- CONFIGURAÇÕES DE EMAIL -------------------
app.config['MAIL_SERVER'] = 'smtp.mailgun.org'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'postmaster@seu-dominio.mailgun.org'
app.config['MAIL_PASSWORD'] = 'sua_senha_mailgun'
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@seudominio.com'
```

---

## 6️⃣ ZOHO MAIL

```python
# ------------------- CONFIGURAÇÕES DE EMAIL -------------------
app.config['MAIL_SERVER'] = 'smtp.zoho.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@zoho.com'
app.config['MAIL_PASSWORD'] = 'sua_senha'
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@zoho.com'
```

---

## 7️⃣ SMTP PERSONALIZADO (Seu próprio servidor)

```python
# ------------------- CONFIGURAÇÕES DE EMAIL -------------------
app.config['MAIL_SERVER'] = 'mail.seudominio.com'
app.config['MAIL_PORT'] = 587  # ou 465 para SSL
app.config['MAIL_USE_TLS'] = True  # ou False se usar SSL
app.config['MAIL_USE_SSL'] = False  # ou True na porta 465
app.config['MAIL_USERNAME'] = 'seu_email@seudominio.com'
app.config['MAIL_PASSWORD'] = 'sua_senha'
app.config['MAIL_DEFAULT_SENDER'] = 'noreply@seudominio.com'
```

---

## 🧪 TESTE DE CONFIGURAÇÃO

### Código para testar se o email funciona:

Crie um arquivo `testar_email.py`:

```python
from flask import Flask
from flask_mail import Mail, Message

app = Flask(__name__)

# Cole aqui suas configurações de email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'sua_senha_app'
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@gmail.com'

mail = Mail(app)

with app.app_context():
    try:
        msg = Message(
            subject='Teste CRM - Configuração Email',
            recipients=['seu_email@gmail.com']  # Enviar para você mesmo
        )
        msg.body = 'Se você recebeu este email, a configuração está correta!'
        mail.send(msg)
        print('✅ Email enviado com sucesso!')
    except Exception as e:
        print(f'❌ Erro ao enviar email: {e}')
```

Execute:
```bash
python testar_email.py
```

---

## ❌ SOLUÇÃO DE PROBLEMAS COMUNS

### Erro: "SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')"

**Gmail:**
- Use senha de app, não a senha normal
- Ative verificação em 2 etapas primeiro

**Outlook:**
- Tente com SSL na porta 465
- Verifique se a conta não tem restrições

### Erro: "ConnectionRefusedError"

**Solução:**
```python
# Troque para SSL
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
```

### Erro: "TimeoutError"

**Causa:** Firewall bloqueando
**Solução:**
- Desabilite firewall temporariamente para testar
- Adicione exceção para Python no firewall

### Email vai para SPAM

**Soluções:**
1. Use um email profissional (não Gmail pessoal)
2. Configure SPF/DKIM no seu domínio
3. Use serviços profissionais (SendGrid, Mailgun)

---

## 🎯 RECOMENDAÇÃO

Para **desenvolvimento/teste:**
- ✅ Gmail (com senha de app)

Para **produção:**
- ✅ SendGrid (100 emails/dia grátis)
- ✅ Mailgun (bom preço)
- ✅ SMTP próprio (se tiver domínio)

---

## 📝 EXEMPLO COMPLETO NO CRM.py

Localize esta seção no arquivo `CRM.py` (aproximadamente linha 24-30):

```python
app = Flask(__name__)
app.secret_key = "seusegredo"

# ------------------- BANCO COM RLS -------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql+psycopg2://postgres:Amovoce123%40@localhost:1222/crm'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False

# ------------------- CONFIGURAÇÕES DE EMAIL -------------------
# COLE AQUI UMA DAS CONFIGURAÇÕES ACIMA!
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'  # ⬅️ ALTERE
app.config['MAIL_PASSWORD'] = 'sua_senha_app'  # ⬅️ ALTERE
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@gmail.com'  # ⬅️ ALTERE

# Inicializa DB com suporte a RLS
db.init_app(app)
tenant_db.init_app(app)

# ------------------- FLASK-MAIL -------------------
mail = Mail(app)
```

---

✅ **Pronto!** Escolha a configuração que preferir e cole no seu CRM.py!
