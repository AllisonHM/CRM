# 🚀 README - INTEGRAÇÃO SITE → CRM

## 📖 Visão Geral

Este projeto implementa uma **integração 100% gratuita** entre um site institucional simples e o CRM existente, permitindo captação de leads sem duplicar código, tabelas ou lógicas.

---

## ✨ Características

- ✅ **Sem duplicação**: reutiliza tabela `Cliente` e estrutura existente
- ✅ **100% gratuito**: frontend (GitHub Pages) + backend (Railway/Render)
- ✅ **Seguro**: API Key, rate limiting, validações
- ✅ **Simples**: HTML/CSS/JS puro (sem frameworks complexos)
- ✅ **Responsivo**: funciona em desktop e mobile
- ✅ **Rápido**: deploy em menos de 1 hora

---

## 📁 Estrutura de Arquivos

```
CRM/
├── site/                          # Frontend (site institucional)
│   ├── index.html                 # Página principal
│   ├── styles.css                 # Estilos
│   └── script.js                  # Lógica de envio
│
├── api_publica_leads.py           # Código da API pública (adicionar ao CRM.py)
├── .env.example                   # Exemplo de variáveis de ambiente
├── requirements_integracao.txt    # Dependências adicionais
│
├── INTEGRACAO_SITE_CRM.md         # Documentação completa da integração
├── GUIA_DEPLOY_SITE_CRM.md        # Passo a passo de deploy
└── README_INTEGRACAO.md           # Este arquivo
```

---

## 🎯 O Que Foi Criado

### ✅ Reaproveitado do CRM Existente

- Tabela `Cliente` (models.py)
- Banco PostgreSQL
- Sistema de autenticação
- Validações e logs
- Estrutura Flask

### 🆕 Criado (Mínimo Necessário)

1. **Backend**: 1 rota nova `/api/public/lead`
2. **Segurança**: API Key + CORS + Rate Limiting
3. **Frontend**: 3 arquivos (HTML, CSS, JS)
4. **Config**: Arquivo `.env` para variáveis

---

## 🚀 Início Rápido

### Passo 1: Instalar Dependências

```bash
pip install flask-cors flask-limiter python-dotenv
```

### Passo 2: Configurar Ambiente

```bash
# Criar .env na raiz do CRM
cp .env.example .env

# Editar .env:
# API_KEY_SITE=sua-chave-secreta-123
# ALLOWED_ORIGINS=http://localhost:3000
# USUARIO_CRM_LEADS=1
```

### Passo 3: Adicionar Código ao Backend

Copiar todo conteúdo de `api_publica_leads.py` e adicionar ao `CRM.py` (antes do `if __name__ == '__main__'`).

### Passo 4: Testar Localmente

```bash
# Terminal 1: Backend
python CRM.py

# Terminal 2: Frontend
cd site/
python -m http.server 3000

# Acessar: http://localhost:3000
```

### Passo 5: Preencher Formulário

1. Abrir `http://localhost:3000`
2. Preencher nome, email, telefone
3. Enviar
4. Verificar se lead aparece no CRM

---

## 📚 Documentação Completa

- **Análise Técnica**: [INTEGRACAO_SITE_CRM.md](INTEGRACAO_SITE_CRM.md)
  - Checklist de reaproveitamento
  - Código completo (backend + frontend)
  - Validações e segurança
  - Perguntas frequentes

- **Guia de Deploy**: [GUIA_DEPLOY_SITE_CRM.md](GUIA_DEPLOY_SITE_CRM.md)
  - Deploy do frontend (GitHub Pages)
  - Deploy do backend (Railway/Render/Fly.io)
  - Configuração de domínios
  - Troubleshooting

---

## 🔐 Segurança

### ✅ Implementado

- **API Key**: autenticação simples via header `X-API-Key`
- **Rate Limiting**: 5 requisições/minuto por IP
- **CORS**: restrito a origens configuradas
- **Validações**: nome, email, telefone no backend
- **Sanitização**: regex para email e telefone
- **Logs**: todas tentativas de acesso registradas

### ⚠️ Recomendações

- [ ] Usar HTTPS em produção (automático no Railway/Render)
- [ ] Rotacionar API Key periodicamente
- [ ] Não comitar `.env` no Git (adicionar ao `.gitignore`)
- [ ] Monitorar logs para detectar abusos
- [ ] Adicionar reCAPTCHA (opcional) para evitar bots

---

## 📊 Tecnologias

### Backend
- Flask (já existente)
- Flask-CORS
- Flask-Limiter
- PostgreSQL (já existente)

### Frontend
- HTML5
- CSS3 (variáveis CSS, Grid, Flexbox)
- JavaScript Vanilla (fetch API)

### Deploy
- Frontend: GitHub Pages (gratuito)
- Backend: Railway/Render/Fly.io (free tier)

---

## 🧪 Testes

### Testar API Diretamente

```bash
# Health check
curl https://seu-backend.railway.app/api/public/health

# Enviar lead (substitua valores)
curl -X POST https://seu-backend.railway.app/api/public/lead \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sua-chave-secreta" \
  -d '{
    "nome": "João Teste",
    "email": "joao@teste.com",
    "telefone": "11988887777",
    "mensagem": "Teste de integração"
  }'
```

---

## 📈 Monitoramento

### Ver Leads no CRM

1. Login no CRM
2. Menu → Clientes
3. Filtrar por tipo: "Lead Site"
4. Ver observações para data/hora de captura

### Logs do Backend

**Railway**: Dashboard → Logs  
**Render**: View Logs  
**Fly.io**: `fly logs`

---

## 🆘 Problemas Comuns

### 1. Erro CORS

**Solução**: Verificar `ALLOWED_ORIGINS` no `.env` do backend

### 2. API Key Inválida

**Solução**: Garantir que `script.js` e `.env` usam a mesma chave

### 3. Email Duplicado

**Solução**: Normal - email já existe no banco (prevenção de duplicatas)

### 4. Backend Hiberna (Render)

**Solução**: Normal no free tier - primeira request demora ~30s

---

## 💰 Custos

### Free Tier (Plano Gratuito)

| Serviço | Limite Free | Custo |
|---------|------------|-------|
| GitHub Pages | 100GB/mês | R$ 0 |
| Railway | 500h/mês + $5 crédito | R$ 0 |
| Render | 750h/mês | R$ 0 |
| Fly.io | 3 VMs + 160GB | R$ 0 |

**Total**: R$ 0,00/mês 🎉

### Quando Escalar

- Render: $7/mês (sem hibernação)
- Railway: $5/mês (após crédito)
- Domínio próprio: ~R$ 40/ano (opcional)

---

## 🎯 Próximos Passos

1. [ ] Testar integração localmente
2. [ ] Deploy do backend (Railway/Render)
3. [ ] Deploy do frontend (GitHub Pages)
4. [ ] Configurar variáveis de ambiente
5. [ ] Testar ponta a ponta em produção
6. [ ] Divulgar site
7. [ ] Monitorar primeiros leads

---

## 📝 Notas Importantes

### Não Fazer

❌ Criar tabela `Lead` separada (já existe `Cliente`)  
❌ Duplicar rotas de cadastro  
❌ Usar frameworks pagos  
❌ Comitar `.env` no Git  

### Fazer

✅ Reutilizar estrutura existente  
✅ Seguir padrões do projeto  
✅ Documentar mudanças  
✅ Testar antes de deploy  

---

## 📞 Suporte

Em caso de dúvidas:

1. Revisar [INTEGRACAO_SITE_CRM.md](INTEGRACAO_SITE_CRM.md) (documentação técnica)
2. Revisar [GUIA_DEPLOY_SITE_CRM.md](GUIA_DEPLOY_SITE_CRM.md) (deploy)
3. Verificar logs do backend
4. Verificar console do navegador (F12)

---

## 📄 Licença

Este código segue a mesma licença do projeto CRM principal.

---

## 🎉 Conclusão

Integração completa, gratuita e sem duplicações entre site institucional e CRM.

**Tempo de implementação**: 2-3 horas  
**Custo**: R$ 0,00  
**Resultado**: Captação automática de leads  

---

**Versão**: 1.0  
**Data**: 01/02/2026  
**Status**: ✅ Pronto para uso
