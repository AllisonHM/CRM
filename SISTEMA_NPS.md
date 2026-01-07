# 📊 Sistema de NPS Automatizado - Documentação

## O que foi implementado

Sistema completo de **Net Promoter Score (NPS)** com pesquisa automatizada via WhatsApp após fechamento de negócio.

---

## 🎯 Como funciona

### 1. Envio Automático da Pesquisa

Quando uma **Mesa de Negócio** é marcada como **"Ganha"**:
- ✅ Sistema envia automaticamente mensagem de NPS via WhatsApp
- 📱 Cliente recebe: "De 0 a 10, o quanto você recomendaria nossa empresa?"
- 🎯 Cliente é marcado como "aguardando_nps = True"

### 2. Processamento da Resposta

Quando o cliente responde com um número de 0 a 10:
- 🤖 Sistema identifica automaticamente a resposta
- 💾 Registra a nota no banco de dados
- 📊 Classifica o cliente em:
  - **Promotor** (9-10) 🌟
  - **Neutro** (7-8) 😊
  - **Detrator** (0-6) 😔
- 💬 Envia mensagem de agradecimento personalizada

### 3. Mensagens de Agradecimento

**Promotores (9-10):**
```
Obrigado pela nota 10! 🌟
Ficamos muito felizes em saber que você recomendaria nossa empresa!
Seu feedback é muito importante para nós. 💙
```

**Neutros (7-8):**
```
Obrigado pela nota 8! 😊
Estamos sempre buscando melhorar. Se tiver alguma sugestão,
ficaremos felizes em ouvir!
```

**Detratores (0-6):**
```
Obrigado pela nota 5. 😔
Lamentamos não ter atendido suas expectativas.
Poderia nos dizer o que podemos melhorar?
Seu feedback é muito importante para nós.
```

---

## 📈 Página de Análise de NPS

Acesse: **Menu → ⭐ NPS**

### Cards de Resumo:
1. **NPS Score** - Valor calculado (% Promotores - % Detratores)
2. **Promotores** - Quantidade e percentual (9-10)
3. **Neutros** - Quantidade e percentual (7-8)
4. **Detratores** - Quantidade e percentual (0-6)

### Gráficos:
1. **Distribuição de Notas** - Barras mostrando quantidade de cada nota (0 a 10)
2. **Evolução do NPS** - Linha temporal dos últimos 30 dias

### Tabela de Respostas:
- Lista todos os clientes que responderam
- Mostra: Nome, Telefone, Nota, Categoria, Data
- Link para detalhes do cliente

---

## 🗃️ Banco de Dados

### Novos campos na tabela `cliente`:

```sql
nps_nota INTEGER          -- Nota de 0 a 10
nps_data DATETIME         -- Data/hora da resposta
nps_comentario TEXT       -- Comentário adicional (futuro)
aguardando_nps BOOLEAN    -- Flag de aguardando resposta
```

---

## 📊 Cálculo do NPS

```
NPS = % Promotores - % Detratores

Exemplo:
- 50 clientes responderam
- 30 deram nota 9-10 (Promotores) = 60%
- 10 deram nota 7-8 (Neutros) = 20%
- 10 deram nota 0-6 (Detratores) = 20%

NPS = 60% - 20% = 40
```

### Classificação:
- **75 a 100** = Excelente 🌟
- **50 a 74** = Muito Bom 👍
- **0 a 49** = Razoável 😐
- **Negativo** = Crítico ⚠️

---

## 🔄 Fluxo Completo

```
1. Mesa marcada como "Ganha"
   ↓
2. Sistema envia pesquisa via WhatsApp
   ↓
3. Cliente responde com número 0-10
   ↓
4. Sistema identifica resposta automaticamente
   ↓
5. Registra nota no banco
   ↓
6. Classifica em Promotor/Neutro/Detrator
   ↓
7. Envia mensagem de agradecimento
   ↓
8. Atualiza dashboard de NPS
```

---

## 🎨 Cores e Badges

- **Promotor** (9-10): Verde `bg-success` com 🌟
- **Neutro** (7-8): Amarelo `bg-warning` com 😊
- **Detrator** (0-6): Vermelho `bg-danger` com 😔

---

## 🚀 Próximas Melhorias Possíveis

1. **Comentários**: Permitir que cliente adicione comentário após a nota
2. **Alertas**: Notificação em tempo real quando detrator responde
3. **Relatórios**: Exportar dados de NPS para Excel/PDF
4. **Filtros**: Filtrar NPS por período, vendedor, produto
5. **Pesquisa Periódica**: Enviar NPS automaticamente a cada X meses
6. **WhatsApp Template**: Usar templates oficiais do WhatsApp Business

---

## 📝 Teste Manual

1. Crie uma Mesa de Negócio para um cliente
2. Marque a situação como "Ganha"
3. Verifique se cliente recebeu mensagem no WhatsApp
4. Responda com um número de 0 a 10
5. Verifique se a nota foi registrada
6. Acesse Menu → ⭐ NPS para ver os resultados

---

## ✅ Arquivos Modificados

- `models.py` - Adicionados campos de NPS
- `CRM.py` - Funções de envio e processamento
- `templates/nps.html` - Página de análise
- `templates/base.html` - Link no menu
- `add_nps_migration.py` - Script de migração do banco

---

**Sistema pronto para uso! 🎉**
