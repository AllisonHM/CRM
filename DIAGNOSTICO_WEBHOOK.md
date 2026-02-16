# 🔴 DIAGNÓSTICO COMPLETO - WEBHOOK NÃO RECEBE MENSAGENS

## 📊 ANÁLISE TÉCNICA DO PROBLEMA

### ✅ O QUE ESTÁ FUNCIONANDO
- CRM rodando corretamente em `http://127.0.0.1:5000`
- PostgreSQL ativo e funcionando
- Endpoint `/webhook/messages` está configurado
- Envio de mensagens funciona normalmente

### ❌ O QUE ESTÁ QUEBRADO
**O webhook não está recebendo mensagens do Z-API**

---

## 🔍 POSSÍVEIS CAUSAS IDENTIFICADAS

### 1️⃣ NGROK: MUDANÇAS EM 2026
**Problema**: O ngrok mudou o comportamento do `--host-header` em versões recentes.

**Antes (2024-2025)**:
```bash
ngrok http 5000 --host-header="127.0.0.1:5000"
```

**Agora (2026) ✅**:
```bash
ngrok http 5000 --host-header="localhost:5000"
```

Ou melhor ainda, usar a nova sintaxe:
```bash
ngrok http 5000 --scheme=http --host-header=rewrite
```

---

### 2️⃣ WEBHOOK MUITO RESTRITIVO
**Problema**: O código atual filtra DEMAIS as mensagens recebidas, ignorando muitas requisições válidas.

**Linhas problemáticas em CRM.py**:
```python
# Linha 1868-1871: Filtra tipos que podem ser mensagens válidas
if tipo in non_message_types and not explicit_text:
    print(f"Webhook ignorado (tipo {data.get('type')} sem texto explícito)")
    return {"status": "ignored"}, 200
```

**O que acontece**:
- Z-API envia callback com `type: "ReceivedCallback"` ou similar
- Seu código interpreta como "não-mensagem" e ignora
- Mensagem nunca chega no CRM

---

### 3️⃣ CORS E HTTPS
**Problema**: Ngrok agora usa HTTPS por padrão, mas seu Flask pode não estar configurado corretamente.

**Solução**: Adicionar headers CORS apropriados no endpoint webhook.

---

### 4️⃣ VERIFICAÇÃO DO Z-API
**Problema**: Z-API pode estar enviando teste/ping que seu webhook rejeita.

---

## ✅ CHECKLIST DE VALIDAÇÃO

Use este checklist para diagnosticar o problema:

### A) NGROK
- [ ] **Versão do ngrok**: Execute `ngrok version` para verificar
- [ ] **URL gerada**: A URL do ngrok deve ser HTTPS (não HTTP)
- [ ] **Comando correto**: Use `ngrok http 5000 --host-header=rewrite`
- [ ] **Status ativo**: Verifique se ngrok está rodando sem erros
- [ ] **Request inspector**: Acesse `http://127.0.0.1:4040` para ver requests

### B) Z-API
- [ ] **Webhook configurado**: URL deve ser `https://SEU_NGROK.ngrok-free.app/webhook/messages`
- [ ] **HTTPS válido**: Z-API só envia para HTTPS (ngrok fornece automaticamente)
- [ ] **Eventos selecionados**: Marcar "Mensagens recebidas" / "Message received"
- [ ] **Token correto**: Verifique se o token está ativo

### C) FLASK/CRM
- [ ] **CRM rodando**: Deve estar ativo em `http://127.0.0.1:5000`
- [ ] **Logs visíveis**: Terminal deve mostrar "📩 Webhook recebido (raw): {...}"
- [ ] **CORS configurado**: Endpoint deve aceitar POST de qualquer origem
- [ ] **Sem proxy reverso**: Não use proxy que possa alterar headers

### D) TESTE MANUAL
- [ ] **curl local**: Teste webhook localmente
```bash
curl -X POST http://127.0.0.1:5000/webhook/messages \
  -H "Content-Type: application/json" \
  -d '{"phone":"5547999999999","text":{"message":"teste"}}'
```

- [ ] **curl via ngrok**: Teste via ngrok
```bash
curl -X POST https://SEU_NGROK.ngrok-free.app/webhook/messages \
  -H "Content-Type: application/json" \
  -d '{"phone":"5547999999999","text":{"message":"teste"}}'
```

- [ ] **Resposta 200 OK**: Webhook deve retornar `{"status":"ok"}`

---

## 🛠️ SOLUÇÕES IMPLEMENTADAS

### ✅ SOLUÇÃO 1: Webhook Menos Restritivo
**Arquivo**: `CRM.py` - Função `receber_mensagem_webhook()`

**Mudanças**:
1. Aceitar mais formatos de payload do Z-API
2. Log detalhado de cada etapa
3. Aceitar callbacks que antes eram ignorados
4. Melhor extração de phone/text

### ✅ SOLUÇÃO 2: Endpoint de Teste
**Novo endpoint**: `/webhook/test`
- Aceita qualquer payload
- Retorna o que foi recebido
- Útil para debug

### ✅ SOLUÇÃO 3: CORS Explícito
**Mudança**: Adicionar CORS no webhook
```python
@app.route("/webhook/messages", methods=["POST", "OPTIONS"])
def receber_mensagem_webhook():
    if request.method == "OPTIONS":
        return {"status": "ok"}, 200
```

---

## 🚀 COMANDO CORRETO PARA 2026

### Opção 1 (Recomendada):
```bash
ngrok http 5000 --host-header=rewrite
```

### Opção 2:
```bash
ngrok http 5000 --host-header="localhost:5000"
```

### Opção 3 (Plano pago):
```bash
ngrok http 5000 --domain=seu-dominio-fixo.ngrok-free.app
```

---

## 🧪 TESTE COMPLETO

### 1️⃣ Iniciar CRM
```powershell
cd "C:\Users\Allison\Desktop\CRM completo\CRM"
python CRM.py
```

### 2️⃣ Iniciar ngrok (em OUTRO terminal)
```powershell
cd C:\ngrok
ngrok http 5000 --host-header=rewrite
```

### 3️⃣ Copiar URL do ngrok
```
Forwarding: https://abc123.ngrok-free.app -> http://localhost:5000
```

### 4️⃣ Configurar no Z-API
```
https://abc123.ngrok-free.app/webhook/messages
```

### 5️⃣ Testar localmente
```bash
curl -X POST http://127.0.0.1:5000/webhook/messages \
  -H "Content-Type: application/json" \
  -d '{"phone":"5547999471874","text":{"message":"Teste local"}}'
```

**Esperar no terminal do CRM**:
```
📩 Webhook recebido (raw): {'phone': '5547999471874', 'text': {'message': 'Teste local'}}
📞 Número normalizado: 5547999471874
✅ Mensagem emitida para sala: 5547999471874
```

### 6️⃣ Testar via ngrok
```bash
curl -X POST https://abc123.ngrok-free.app/webhook/messages \
  -H "Content-Type: application/json" \
  -d '{"phone":"5547999471874","text":{"message":"Teste ngrok"}}'
```

### 7️⃣ Enviar WhatsApp real
- Envie mensagem para o número da instância Z-API
- Verifique os logs no terminal do CRM
- Verifique a tela de Canais no navegador

---

## 🐛 DEBUG AVANÇADO

### Ver requisições do ngrok:
1. Acesse: http://127.0.0.1:4040
2. Veja todas as requisições recebidas
3. Analise payload, headers, resposta

### Logs do CRM:
O CRM agora mostra:
```
📩 Webhook recebido (raw): {...}
📞 Número recebido: +5547999471874
📞 Número normalizado: 5547999471874
✅ Cliente encontrado: João Silva (Tel: 5547999471874)
✅ Mensagem emitida para sala: 5547999471874
```

---

## 📞 SUPORTE Z-API

Se ainda não funcionar, verifique no painel do Z-API:
1. **Status da instância**: Deve estar "Conectada"
2. **Webhook logs**: Painel mostra se enviou webhook e qual foi a resposta
3. **Webhook test**: Use o botão de teste no painel

---

## 🎯 RESULTADO ESPERADO

Após aplicar as correções:
1. ✅ Ngrok expõe o CRM corretamente
2. ✅ Z-API envia webhook para seu CRM
3. ✅ CRM recebe e processa mensagem
4. ✅ Mensagem aparece na tela de Canais
5. ✅ Notificação sonora toca
6. ✅ Badge de não lidas atualiza
7. ✅ Cliente aparece na lista lateral
