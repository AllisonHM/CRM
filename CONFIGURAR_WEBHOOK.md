# 🔔 Configurar Webhook para Receber Mensagens no CRM

## ❌ Problema Atual
O CRM está rodando apenas em **localhost** (127.0.0.1:5000) e não é acessível pela internet. O Z-API não consegue enviar mensagens para o seu servidor.

## ✅ Solução: Usar ngrok

### 1️⃣ Instalar o ngrok

1. Acesse: https://ngrok.com/
2. Crie uma conta gratuita
3. Baixe o ngrok para Windows
4. Extraia o arquivo `ngrok.exe` em uma pasta (ex: `C:\ngrok\`)

### 2️⃣ Configurar o Token do ngrok

No terminal (PowerShell), execute:
```powershell
cd C:\ngrok
.\ngrok config add-authtoken SEU_TOKEN_AQUI
```

(O token você pega no painel do ngrok após criar a conta)

### 3️⃣ Expor o CRM para a Internet

Com o CRM rodando em http://127.0.0.1:5000, abra **OUTRO terminal** e execute:

```powershell
cd C:\ngrok
.\ngrok http 5000
```

Você verá algo assim:
```
Session Status    online
Forwarding        https://a1b2-c3d4.ngrok-free.app -> http://localhost:5000
```

**Copie a URL** que aparece (exemplo: `https://a1b2-c3d4.ngrok-free.app`)

### 4️⃣ Configurar o Webhook no Z-API

1. Acesse o painel do Z-API
2. Vá em **Webhooks** ou **Configurações**
3. Configure a URL do webhook:
   ```
   https://SUA_URL_NGROK.ngrok-free.app/webhook/messages
   ```
   
   **Exemplo completo:**
   ```
   https://a1b2-c3d4.ngrok-free.app/webhook/messages
   ```

4. Selecione os eventos:
   - ✅ **Mensagens Recebidas** (ou `message.received`)
   - ✅ **Mensagens de Texto**

5. Salve a configuração

### 5️⃣ Testar o Webhook

Envie uma mensagem WhatsApp para o número da sua instância Z-API. No terminal onde o CRM está rodando, você deve ver:

```
📩 Webhook recebido: {...}
✅ Mensagem emitida para sala: 5547999999999
```

## 🔄 Processo Completo

1. **Terminal 1**: Execute o CRM
   ```powershell
   python CRM.py
   ```

2. **Terminal 2**: Execute o ngrok
   ```powershell
   cd C:\ngrok
   .\ngrok http 5000
   ```

3. **Z-API**: Configure o webhook com a URL do ngrok + `/webhook/messages`

4. **Teste**: Envie uma mensagem WhatsApp e verifique se aparece no CRM

## ⚠️ Importante

- A URL do ngrok **muda** toda vez que você reinicia o ngrok (no plano gratuito)
- Você precisa **atualizar** a URL no Z-API sempre que reiniciar o ngrok
- Mantenha os **dois terminais abertos** (CRM + ngrok) para receber mensagens

## 🎯 URLs Disponíveis no Seu CRM

- `/webhook/messages` - Recebe mensagens do WhatsApp
- `/canais/webhook` - Recebe mensagens (alternativo)

Ambas as URLs funcionam da mesma forma!

## 📱 Configuração Atual do Z-API

```
Instance ID: 3E70C9784E1060A6F423AE9094E04006
Token: E4E83715DE9F517EFB9A28CA
Client Token: Fc5c052a80080460b823a2e506d4d6167S
```

## 🐛 Debug

Para verificar se as mensagens estão chegando, observe o terminal do CRM. Cada webhook recebido exibe:
```
📩 Webhook recebido (raw): {...}
✅ Mensagem emitida para sala: 5547999999999
```

Se não aparecer nada, o webhook não está configurado corretamente no Z-API.
