# ⚡ INSTALAÇÃO RÁPIDA - INTEGRAÇÃO SITE → CRM

## 🎯 Objetivo
Adicionar API pública para captar leads do site institucional no CRM existente.

---

## 📦 PASSO 1: INSTALAR DEPENDÊNCIAS

```bash
pip install flask-cors flask-limiter python-dotenv
```

---

## 🔧 PASSO 2: ADICIONAR CÓDIGO AO CRM.py

Abrir [CRM.py](CRM.py) e adicionar **antes** da linha `if __name__ == '__main__':`:

```python
# =============================================
# COPIAR TODO CONTEÚDO DE api_publica_leads.py
# =============================================
```

Ou adicionar no início do arquivo:

```python
from api_publica_leads import *
```

---

## 🔐 PASSO 3: CRIAR ARQUIVO .env

Na raiz do projeto CRM, criar arquivo `.env`:

```env
API_KEY_SITE=minha-chave-secreta-123
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5000
USUARIO_CRM_LEADS=1
```

**⚠️ IMPORTANTE**: 
- Trocar `minha-chave-secreta-123` por uma chave forte
- Gerar: `python -c "import secrets; print(secrets.token_urlsafe(32))"`

---

## 🎨 PASSO 4: CONFIGURAR FRONTEND

Editar [site/script.js](site/script.js), linhas 6-7:

```javascript
const API_CONFIG = {
    baseURL: 'http://localhost:5000', // ← URL do backend
    apiKey: 'minha-chave-secreta-123', // ← Mesma do .env
    // ...
};
```

---

## 🧪 PASSO 5: TESTAR LOCALMENTE

### Terminal 1 - Backend

```bash
cd "c:\Users\Allison\Desktop\CRM completo\CRM"
python CRM.py
```

### Terminal 2 - Frontend

```bash
cd "c:\Users\Allison\Desktop\CRM completo\CRM\site"
python -m http.server 3000
```

### Navegador

1. Abrir: http://localhost:3000
2. Preencher formulário
3. Enviar
4. Verificar console (F12) - deve mostrar "✅ API CRM está online"
5. Verificar backend - deve mostrar "✅ Lead capturado"
6. Acessar CRM → Clientes → Ver novo lead

---

## ✅ CHECKLIST RÁPIDO

- [ ] Dependências instaladas
- [ ] Código adicionado ao CRM.py
- [ ] Arquivo .env criado
- [ ] script.js configurado com URL e API Key
- [ ] Backend rodando (localhost:5000)
- [ ] Frontend rodando (localhost:3000)
- [ ] Formulário testado
- [ ] Lead aparece no CRM

---

## 🚀 PRÓXIMO PASSO: DEPLOY

Após testar localmente, seguir [GUIA_DEPLOY_SITE_CRM.md](GUIA_DEPLOY_SITE_CRM.md) para publicar.

---

## 🆘 PROBLEMAS?

### Erro: ModuleNotFoundError

```bash
pip install flask-cors flask-limiter python-dotenv
```

### Erro: API Key inválida

Verificar se `.env` e `script.js` usam a **mesma chave**.

### Erro: CORS

Adicionar `http://localhost:3000` ao `ALLOWED_ORIGINS` no `.env`.

### Lead não aparece no CRM

1. Verificar logs do backend
2. Verificar console do navegador (F12)
3. Ver resposta da API (Network tab)

---

## 📝 MAIS INFORMAÇÕES

- **Documentação Técnica**: [INTEGRACAO_SITE_CRM.md](INTEGRACAO_SITE_CRM.md)
- **Guia de Deploy**: [GUIA_DEPLOY_SITE_CRM.md](GUIA_DEPLOY_SITE_CRM.md)
- **README**: [README_INTEGRACAO.md](README_INTEGRACAO.md)

---

**Tempo estimado**: 15-30 minutos  
**Status**: ✅ Pronto para instalar
