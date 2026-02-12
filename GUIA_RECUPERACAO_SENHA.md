# 📧 GUIA DE CONFIGURAÇÃO DO SISTEMA DE RECUPERAÇÃO DE SENHA

## 🎯 O que foi implementado?

Sistema completo de recuperação de senha por email com as seguintes funcionalidades:

1. ✅ Página "Esqueci minha senha"
2. ✅ Geração de token único e seguro
3. ✅ Envio de email com link de recuperação
4. ✅ Validação de token com expiração (1 hora)
5. ✅ Página para redefinir senha
6. ✅ Segurança: não revela se o email existe no sistema

---

## 📝 Arquivos Modificados/Criados

### 1. **models.py**
- Adicionados campos `reset_token` e `reset_token_expira` ao modelo `UsuarioCRM`

### 2. **CRM.py**
- Instalado e configurado Flask-Mail
- Criada função `enviar_email_recuperacao()`
- Criada rota `/esqueci-senha`
- Criada rota `/resetar-senha/<token>`

### 3. **Templates HTML**
- `templates/login.html` - Adicionado link "Esqueci minha senha"
- `templates/esqueci_senha.html` - Formulário para solicitar recuperação
- `templates/resetar_senha.html` - Formulário para definir nova senha

### 4. **Banco de Dados**
- Script `add_reset_password_columns.py` - Migração executada ✅

---

## ⚙️ CONFIGURAÇÃO DO EMAIL (OBRIGATÓRIO)

### Opção 1: Gmail (Recomendado)

#### Passo 1: Criar Senha de App no Gmail

1. Acesse: https://myaccount.google.com/security
2. Ative a **Verificação em duas etapas** (se ainda não tiver)
3. Procure por **"Senhas de app"**
4. Clique em **"Criar nova senha de app"**
5. Nome: "CRM System"
6. Copie a senha gerada (16 caracteres)

#### Passo 2: Configurar no CRM.py

No arquivo `CRM.py`, localize as linhas (aproximadamente linha 30):

```python
# ------------------- CONFIGURAÇÕES DE EMAIL -------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'  # ⬅️ ALTERE AQUI
app.config['MAIL_PASSWORD'] = 'sua_senha_app'  # ⬅️ COLE A SENHA DE APP AQUI
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@gmail.com'  # ⬅️ ALTERE AQUI
```

**Substitua:**
- `seu_email@gmail.com` pelo seu email do Gmail
- `sua_senha_app` pela senha de app gerada (cole sem espaços)

### Opção 2: Outlook/Hotmail

```python
app.config['MAIL_SERVER'] = 'smtp.office365.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu_email@outlook.com'
app.config['MAIL_PASSWORD'] = 'sua_senha'
app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@outlook.com'
```

### Opção 3: Outros Provedores

**Yahoo:**
```python
MAIL_SERVER = 'smtp.mail.yahoo.com'
MAIL_PORT = 587
```

**SendGrid (profissional):**
```python
MAIL_SERVER = 'smtp.sendgrid.net'
MAIL_PORT = 587
MAIL_USERNAME = 'apikey'
MAIL_PASSWORD = 'sua_api_key'
```

---

## 🔐 Como Funciona?

### 1. Usuário Esqueceu a Senha

1. Usuário acessa `/login`
2. Clica em "Esqueci minha senha"
3. Insere seu email
4. Sistema gera token único e envia email

### 2. Fluxo de Recuperação

```
Usuário → Esqueci Senha → Insere Email → Token Gerado
                                              ↓
                                        Email Enviado
                                              ↓
                                    Usuário Clica no Link
                                              ↓
                                    Insere Nova Senha
                                              ↓
                                    Senha Redefinida ✅
```

### 3. Segurança Implementada

✅ Token único e aleatório (32 bytes)
✅ Expiração de 1 hora
✅ Token invalidado após uso
✅ Hash de senha (nunca armazenada em texto puro)
✅ Não revela se email existe (proteção contra enumeração)

---

## 🧪 Como Testar?

### Teste 1: Solicitar Recuperação

```bash
1. Acesse: http://localhost:5000/login
2. Clique em "Esqueci minha senha"
3. Digite um email cadastrado
4. Verifique se recebeu o email
```

### Teste 2: Usar Link de Recuperação

```bash
1. Abra o email recebido
2. Clique no link ou copie a URL
3. Defina uma nova senha
4. Tente fazer login com a nova senha
```

### Teste 3: Token Expirado

```bash
1. Solicite recuperação de senha
2. Aguarde 1 hora e 1 minuto
3. Tente usar o link
4. Deve mostrar: "Link de recuperação inválido ou expirado"
```

---

## ❌ Solução de Problemas

### Erro: "SMTPAuthenticationError"

**Causa:** Credenciais de email incorretas

**Solução:**
- Verifique se o email está correto
- Use senha de app (não a senha normal do Gmail)
- Confira se a verificação em 2 etapas está ativa

### Erro: "ConnectionRefusedError"

**Causa:** Firewall ou porta bloqueada

**Solução:**
```python
# Tente usar SSL na porta 465
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
```

### Email não chega

**Verifique:**
1. Pasta de SPAM
2. Configurações de firewall
3. Logs do console para erros
4. Se o email remetente está correto

### Link não funciona

**Verifique:**
1. Se o servidor está rodando na mesma URL
2. Se o token não expirou
3. Se o banco de dados foi atualizado (migração executada)

---

## 🔧 Personalização

### Alterar Tempo de Expiração

No `CRM.py`, linha da função `esqueci_senha`:

```python
# Mudar de 1 hora para 30 minutos
usuario.reset_token_expira = datetime.utcnow() + timedelta(minutes=30)

# Mudar para 24 horas
usuario.reset_token_expira = datetime.utcnow() + timedelta(hours=24)
```

### Customizar Email

No `CRM.py`, função `enviar_email_recuperacao()`:

```python
# Personalize o HTML do email
msg.html = f"""
<html>
    <body style="...">
        <!-- Seu HTML customizado aqui -->
    </body>
</html>
"""
```

---

## 📊 Estrutura do Banco de Dados

### Tabela: usuario_crm

```sql
reset_token VARCHAR(255) NULL
reset_token_expira TIMESTAMP NULL
```

**Comportamento:**
- `reset_token`: Armazena o token gerado
- `reset_token_expira`: Data/hora de expiração
- Ambos são NULL quando não há recuperação em andamento
- São limpos após uso ou expiração

---

## 🚀 Próximos Passos (Opcional)

### Melhorias Sugeridas:

1. **Rate Limiting**
   - Limitar tentativas de recuperação por IP
   - Prevenir abuso do sistema

2. **Log de Atividades**
   - Registrar tentativas de recuperação
   - Alertar o usuário sobre atividades suspeitas

3. **Template de Email Profissional**
   - Logo da empresa
   - Footer personalizado
   - Design responsivo

4. **Notificação de Sucesso**
   - Email confirmando troca de senha
   - Alerta em caso de atividade suspeita

---

## ✅ Checklist de Implementação

- [x] Flask-Mail instalado
- [x] Configurações de SMTP adicionadas
- [x] Campos no banco de dados criados
- [x] Migração executada com sucesso
- [x] Rotas criadas e testadas
- [x] Templates HTML criados
- [x] Link no login adicionado
- [ ] **CONFIGURAR CREDENCIAIS DE EMAIL** ⬅️ **FALTA FAZER**
- [ ] Testar envio de email
- [ ] Testar recuperação completa

---

## 📞 Suporte

Se precisar de ajuda:

1. Verifique os logs do Flask no console
2. Teste as configurações de SMTP
3. Verifique se o banco de dados foi atualizado
4. Confira se todos os templates estão no lugar certo

---

**Desenvolvido em:** 09/02/2026
**Versão:** 1.0
**Status:** ✅ Pronto para configuração
