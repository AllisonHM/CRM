# ⚡ COMANDOS RÁPIDOS - CANAIS CRM

## 🚀 INICIAR SISTEMA

### Terminal 1 - CRM
```powershell
cd "C:\Users\Allison\Desktop\CRM completo\CRM"
python CRM.py
```

### Terminal 2 - ngrok
```powershell
cd C:\ngrok
ngrok http 5000 --host-header=rewrite
```

---

## 🔧 TESTAR WEBHOOK

### Teste Local
```bash
curl -X POST http://127.0.0.1:5000/webhook/test -H "Content-Type: application/json" -d "{\"phone\":\"5547999471874\",\"text\":{\"message\":\"Teste\"}}"
```

### Teste Real
```bash
curl -X POST http://127.0.0.1:5000/webhook/messages -H "Content-Type: application/json" -d "{\"phone\":\"5547999471874\",\"text\":{\"message\":\"Teste real\"}}"
```

### Ver Requisições ngrok
```
http://127.0.0.1:4040
```

---

## 📝 ATIVAR NOVA TELA

### Opção 1 - Substituir (recomendado)
```powershell
# Backup
copy "templates\canais.html" "templates\canais_backup.html"

# Substituir
copy "templates\canais_novo.html" "templates\canais.html"

# Reiniciar CRM (Ctrl+C e rodar novamente)
```

### Opção 2 - Rota Nova

Adicione em `CRM.py` (procure por `@app.route("/canais")`):

```python
@app.route("/canais_novo")
@login_required
def canais_novo():
    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template("canais_novo.html", clientes=clientes)
```

Acesse: `http://127.0.0.1:5000/canais_novo`

---

## 🔗 CONFIGURAR WEBHOOK NO Z-API

1. Copie URL do ngrok (ex: `https://abc123.ngrok-free.app`)
2. Acesse painel Z-API
3. Webhook: `https://abc123.ngrok-free.app/webhook/messages`
4. Ativar: "Mensagens Recebidas"

---

## 🎯 ACESSAR

- CRM: `http://127.0.0.1:5000`
- Canais Original: `http://127.0.0.1:5000/canais`
- Canais Novo: `http://127.0.0.1:5000/canais_novo` (se criou rota)
- ngrok Inspector: `http://127.0.0.1:4040`

---

## 📚 ARQUIVOS IMPORTANTES

- `DIAGNOSTICO_WEBHOOK.md` - Diagnóstico completo do webhook
- `IMPLEMENTACAO_COMPLETA.md` - Todas as funcionalidades implementadas
- `COMANDOS_RAPIDOS.md` - Este arquivo
- `templates/canais_novo.html` - Nova versão da tela
- `templates/canais.html` - Versão original

---

## ✅ CHECKLIST DE VERIFICAÇÃO

- [ ] CRM rodando (Terminal 1)
- [ ] ngrok rodando (Terminal 2)
- [ ] URL do ngrok copiada
- [ ] Webhook configurado no Z-API
- [ ] Arquivo canais.html substituído (ou rota criada)
- [ ] CRM acessível em http://127.0.0.1:5000
- [ ] Tela Canais acessível
- [ ] Teste de mensagem enviado

---

## 🐛 PROBLEMAS COMUNS

### Erro: ModuleNotFoundError
```powershell
pip install -r requirements.txt
```

### Erro: ngrok não encontrado
```powershell
# Baixe em: https://ngrok.com/download
# Extraia em C:\ngrok\ngrok.exe
```

### Webhook não recebe
1. Ver logs do CRM (Terminal 1)
2. Ver ngrok inspector (http://127.0.0.1:4040)
3. Testar endpoint local
4. Verificar URL no Z-API

### WebSocket não conecta
1. Verificar console do navegador (F12)
2. Limpar cache (Ctrl+Shift+Del)
3. Reiniciar CRM

---

## 📞 CREDENCIAIS Z-API

```
Instance ID: 3E70C9784E1060A6F423AE9094E04006
Token: E4E83715DE9F517EFB9A28CA
Client Token: Fc5c052a80080460b823a2e506d4d6167S
```

---

## 🎉 PRONTO!

Se seguiu todos os passos, seu CRM agora tem:
✅ Webhook funcional
✅ Tela de Canais completa
✅ Todas as funcionalidades do WhatsApp Web
✅ Identidade visual mantida

**Bom uso! 🚀**
