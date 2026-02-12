# 🚨 PROBLEMA: "Erro ao enviar email"

## ❓ Por que isso acontece?

O sistema de recuperação de senha **está funcionando**, mas o email não foi configurado ainda!

As configurações no [CRM.py](CRM.py#L35-L37) ainda estão assim:

```python
app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'  # ⬅️ Valor padrão
app.config['MAIL_PASSWORD'] = 'sua_senha_app'  # ⬅️ Valor padrão
```

---

## ✅ SOLUÇÃO RÁPIDA (2 opções)

### 🎯 Opção 1: Script Automático (RECOMENDADO)

Execute este comando no terminal:

```bash
python configurar_email_interativo.py
```

O script vai:
1. ✅ Perguntar qual provedor você usa (Gmail, Outlook, etc)
2. ✅ Solicitar suas credenciais
3. ✅ Testar se funciona
4. ✅ Gerar o código pronto para você colar no CRM.py

**Vantagem:** Já testa se está funcionando antes de você configurar!

---

### 🛠️ Opção 2: Configuração Manual

#### Para Gmail:

1. **Criar Senha de App:**
   - Acesse: https://myaccount.google.com/security
   - Ative "Verificação em duas etapas"
   - Procure "Senhas de app"
   - Crie uma senha para "CRM System"
   - Copie a senha gerada (16 caracteres)

2. **Editar CRM.py (linhas 35-37):**
   ```python
   app.config['MAIL_USERNAME'] = 'seu_email@gmail.com'  # ⬅️ SEU EMAIL AQUI
   app.config['MAIL_PASSWORD'] = 'xxxx xxxx xxxx xxxx'  # ⬅️ SENHA DE APP
   app.config['MAIL_DEFAULT_SENDER'] = 'seu_email@gmail.com'  # ⬅️ SEU EMAIL
   ```

3. **Reiniciar o servidor Flask**

---

#### Para Outlook/Hotmail:

**Editar CRM.py (linhas 33-37):**
```python
app.config['MAIL_SERVER'] = 'smtp.office365.com'  # ⬅️ Mudar servidor
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'seu@outlook.com'  # ⬅️ SEU EMAIL
app.config['MAIL_PASSWORD'] = 'sua_senha'  # ⬅️ Senha normal da conta
app.config['MAIL_DEFAULT_SENDER'] = 'seu@outlook.com'
```

---

## 🧪 Como Testar Depois

1. Reinicie o servidor Flask
2. Acesse: http://localhost:5000/login
3. Clique em "Esqueci minha senha"
4. Digite um email cadastrado
5. Verifique sua caixa de entrada (e SPAM)

---

## 📊 Melhorias que Fiz

1. ✅ Sistema agora detecta quando email não está configurado
2. ✅ Mensagens de erro mais claras
3. ✅ Logs detalhados no console
4. ✅ Script interativo para facilitar configuração
5. ✅ Validação antes de tentar enviar email

---

## 🆘 Se Ainda Não Funcionar

Rode o servidor e tente novamente. Agora você verá mensagens mais claras:

- ⚠️ "Sistema de email não configurado" = Configure as credenciais
- ❌ "Credenciais inválidas" = Verifique email/senha
- ❌ "Não foi possível conectar" = Problema de internet/firewall

Os erros detalhados aparecerão no console do Flask!

---

## 🚀 Recomendação

Use o script automático:

```bash
python configurar_email_interativo.py
```

É mais rápido, testa tudo e gera o código pronto! 🎯
