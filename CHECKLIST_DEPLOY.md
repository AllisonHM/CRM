# 🚀 CHECKLIST DE DEPLOY - LOCAWEB

Use este checklist para garantir que nada foi esquecido no deploy!

---

## 📋 ANTES DO DEPLOY

### Locaweb - Contratação
- [ ] Hospedagem Python contratada
- [ ] PostgreSQL habilitado
- [ ] SSL/HTTPS ativado (Let's Encrypt)
- [ ] Domínio configurado (ex: crm.seudominio.com.br)
- [ ] Credenciais FTP/SSH recebidas

### Preparação Local
- [ ] Código testado localmente
- [ ] Backup do banco local criado
- [ ] Arquivo `.env.production.example` renomeado para `.env`
- [ ] Variáveis de ambiente configuradas no `.env`
- [ ] `SECRET_KEY` gerada (comando: `python -c "import secrets; print(secrets.token_hex(32))"`)
- [ ] Dependências atualizadas em `requirements.txt`

---

## 📤 DURANTE O DEPLOY

### Passo 1: Configurar Banco na Locaweb
- [ ] Banco PostgreSQL criado no painel
- [ ] Credenciais anotadas (host, porta, user, password, database)
- [ ] Credenciais adicionadas ao `.env`

### Passo 2: Upload dos Arquivos
- [ ] Upload via FTP ou Git concluído
- [ ] Arquivos verificados no servidor:
  - [ ] `passenger_wsgi.py`
  - [ ] `.htaccess`
  - [ ] `.env` (com dados de produção)
  - [ ] `CRM.py`
  - [ ] Pastas `templates/` e `static/`
  - [ ] `requirements.txt`
  - [ ] `config_production.py`
  - [ ] `setup_database_producao.py`

### Passo 3: Ambiente Virtual
- [ ] Ambiente virtual criado: `python3.10 -m venv virtualenv/python3.10`
- [ ] Ambiente ativado: `source virtualenv/python3.10/bin/activate`
- [ ] pip atualizado: `pip install --upgrade pip`
- [ ] Dependências instaladas: `pip install -r requirements.txt`

### Passo 4: Configurar Diretórios
- [ ] Diretório `logs/` criado: `mkdir -p ~/public_html/logs`
- [ ] Diretório `uploads/` criado: `mkdir -p ~/public_html/static/uploads/canais`
- [ ] Permissões ajustadas: `chmod 755 ~/public_html/static/uploads -R`
- [ ] Diretório `tmp/` criado: `mkdir -p ~/public_html/tmp`

### Passo 5: Banco de Dados
- [ ] Script executado: `python setup_database_producao.py`
- [ ] Tabelas criadas com sucesso
- [ ] Índices aplicados
- [ ] Estrutura verificada

### Passo 6: Usuário Inicial
- [ ] Super admin criado: `python criar_usuario_crm.py`
- [ ] Email e senha anotados

### Passo 7: Reiniciar Aplicação
- [ ] Arquivo restart criado: `touch ~/public_html/tmp/restart.txt`
- [ ] Ou reiniciado via painel Locaweb

---

## ✅ APÓS O DEPLOY

### Testes Básicos
- [ ] Site carrega: `https://crm.seudominio.com.br`
- [ ] HTTPS ativo (cadeado verde no navegador)
- [ ] Login funciona com usuário criado
- [ ] Dashboard carrega sem erros
- [ ] Menu lateral funciona

### Testes de Funcionalidades
- [ ] Criar cliente funciona
- [ ] Listar clientes mostra dados
- [ ] Upload de arquivo funciona
- [ ] WhatsApp envia mensagem (testar!)
- [ ] WhatsApp envia arquivo/PDF (testar!)
- [ ] Logs sendo gravados: `tail -f ~/public_html/logs/crm.log`

### Testes de Performance
- [ ] Tempo de carregamento < 3 segundos
- [ ] Queries rápidas (índices funcionando)
- [ ] Upload de arquivos funciona

### Segurança
- [ ] HTTPS obrigatório (HTTP redireciona para HTTPS)
- [ ] Arquivo `.env` não acessível via navegador
- [ ] Arquivos `.py` não acessíveis (exceto `passenger_wsgi.py`)
- [ ] Headers de segurança presentes (verificar com: developer tools → Network)
- [ ] CSRF protection ativa

---

## 🔧 CONFIGURAÇÕES OPCIONAIS

### Backup Automático
- [ ] Script de backup criado: `~/backup_diario.sh`
- [ ] Cron configurado: `crontab -e`
- [ ] Teste de backup executado

### Monitoramento
- [ ] Logs monitorados: `tail -f ~/public_html/logs/crm.log`
- [ ] Passenger logs verificados: `tail -f ~/passenger_logs/error.log`
- [ ] Uptime monitoring configurado (opcional)

### Email
- [ ] SMTP Locaweb configurado no `.env`
- [ ] Teste de envio de email realizado
- [ ] Recuperação de senha testada

---

## 🚨 EM CASO DE PROBLEMAS

### Site não carrega
```bash
# Ver logs do Passenger
tail -50 ~/passenger_logs/error.log

# Reiniciar aplicação
touch ~/public_html/tmp/restart.txt

# Verificar permissões
ls -la ~/public_html/passenger_wsgi.py
```

### Erro 502 Bad Gateway
```bash
# Verificar Python
python --version

# Reinstalar dependências
pip install -r requirements.txt --upgrade

# Ver logs de erro
tail -100 ~/passenger_logs/error.log
```

### Banco não conecta
```bash
# Testar conexão
psql -h pgsql.locaweb.com.br -U usuario -d database

# Verificar .env
cat .env | grep DATABASE_URL
```

### Upload não funciona
```bash
# Verificar permissões
chmod 755 ~/public_html/static/uploads -R

# Criar diretório se não existe
mkdir -p ~/public_html/static/uploads/canais
```

---

## 📞 CONTATOS IMPORTANTES

- **Suporte Locaweb**: 0800 054 4040
- **Painel**: painel.locaweb.com.br
- **Docs Python Locaweb**: ajuda.locaweb.com.br

---

## ✅ DEPLOY CONCLUÍDO!

Quando todos os itens estiverem marcados, seu CRM está no ar! 🎉

**Próximos passos**:
1. Testar com usuários reais
2. Monitorar logs diariamente (primeira semana)
3. Configurar backups automáticos
4. Preparar API para app mobile

---

**Data do deploy**: ___/___/______  
**URL**: https://_________________  
**Usuário admin**: _________________  
**Banco**: _________________
