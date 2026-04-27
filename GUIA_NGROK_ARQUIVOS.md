# 🌐 Guia: Como Enviar Arquivos pelo CRM com Ngrok

## 🔍 **O Problema**

A Z-API (e qualquer API externa) **não consegue acessar URLs de localhost** como:
- `http://localhost:5000/static/uploads/...`
- `http://127.0.0.1:5000/static/uploads/...`

Isso acontece porque estas URLs só existem **no seu computador**, não são acessíveis pela internet.

---

## ✅ **Solução: Usar Ngrok**

O **Ngrok** cria uma URL pública temporária que redireciona para seu localhost.

### **Passo 1: Instalar Ngrok**

1. Acesse: https://ngrok.com/download
2. Baixe a versão para Windows
3. Extraia o arquivo `ngrok.exe` em uma pasta (ex: `C:\ngrok\`)
4. (Opcional) Crie uma conta gratuita em https://dashboard.ngrok.com/signup

### **Passo 2: Conectar sua Conta (Opcional mas Recomendado)**

1. Faça login em https://dashboard.ngrok.com
2. Copie seu **Authtoken**
3. Execute no terminal:
```bash
cd C:\ngrok
.\ngrok authtoken SEU_TOKEN_AQUI
```

### **Passo 3: Iniciar o Ngrok**

**No terminal do PowerShell:**

```bash
cd C:\ngrok
.\ngrok http 5000
```

Você verá algo assim:

```
ngrok

Session Status                online
Account                       seu_email@gmail.com
Version                       3.x.x
Region                        United States (us)
Latency                       45ms
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://abc123.ngrok-free.app -> http://localhost:5000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

🎯 **A linha importante é:**
```
Forwarding    https://abc123.ngrok-free.app -> http://localhost:5000
```

### **Passo 4: Acessar o CRM pela URL do Ngrok**

1. **Copie** a URL pública (ex: `https://abc123.ngrok-free.app`)
2. **Feche** o navegador onde o CRM está aberto
3. **Abra** o navegador e acesse: `https://abc123.ngrok-free.app`
4. Faça login normalmente
5. Acesse a tela de **Canais**
6. **Envie um arquivo PDF**

✅ Agora a Z-API consegue acessar a URL pública!

---

## 🔧 **Automatizar com Arquivo .bat**

Crie um arquivo `INICIAR_NGROK.bat` na pasta do CRM:

```batch
@echo off
echo Iniciando Ngrok...
cd C:\ngrok
start cmd /k ngrok http 5000
echo.
echo Ngrok iniciado!
echo Copie a URL publica e acesse no navegador
pause
```

Execute este arquivo **antes** de iniciar o CRM.

---

## 📋 **Checklist Completo**

1. ✅ Ngrok instalado e configurado
2. ✅ Execute `ngrok http 5000`
3. ✅ Copie a URL pública (ex: `https://abc123.ngrok-free.app`)
4. ✅ Acesse o CRM pela URL do Ngrok
5. ✅ Envie arquivo PDF na tela de Canais
6. ✅ Arquivo chega no WhatsApp!

---

## ⚠️ **Observações Importantes**

### **Ngrok Gratuito:**
- ✅ Ilimitado localmente
- ⚠️ URL muda a cada reinicialização
- ⚠️ Limite de 40 conexões/minuto
- ⚠️ Banner "Visit Site" em navegadores

### **Ngrok Pago (a partir de $8/mês):**
- ✅ URL fixa (subdomínio personalizado)
- ✅ Sem limite de conexões
- ✅ Sem banner

### **Alternativa: Hospedar em Servidor Público**

Se não quiser usar Ngrok, você pode:
- Hospedar o CRM em servidor VPS (AWS, DigitalOcean, etc.)
- Configurar domínio próprio
- Usar HTTPS com certificado SSL

---

## 🐛 **Solução de Problemas**

### **"Failed to load resource: 404"**
✅ **Solução:** Certifique-se de acessar o CRM pela URL do Ngrok, não por `localhost`

### **"Arquivo salvo, mas não enviado"**
✅ **Solução:** Verifique se o Ngrok está rodando e se a URL é pública

### **"Ngrok não funciona"**
1. Verifique se o CRM está rodando em `localhost:5000`
2. Tente reiniciar o Ngrok
3. Verifique se a porta 5000 está livre

---

## 📞 **Testando**

Após configurar o Ngrok:

1. Acesse: `https://SEU_NGROK.ngrok-free.app/canais`
2. Selecione uma conversa
3. Clique no ícone de anexo (📎)
4. Escolha um PDF pequeno (até 5MB)
5. Clique em "Enviar"
6. Verifique seu WhatsApp!

---

## 🎉 **Pronto!**

Agora o envio de arquivos funcionará perfeitamente!
