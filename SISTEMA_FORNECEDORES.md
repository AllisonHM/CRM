# 📦 Sistema de Gerenciamento de Fornecedores

## 🚀 Instalação e Configuração

### 1. Criar a tabela no banco de dados

Execute o script de migração:

```powershell
& "C:\Users\Allison\Desktop\CRM completo\CRM\.venv\Scripts\python.exe" add_fornecedores_table.py
```

### 2. Iniciar o servidor CRM

```powershell
& "C:\Users\Allison\Desktop\CRM completo\CRM\.venv\Scripts\python.exe" CRM.py
```

### 3. Acessar o sistema

Acesse: `http://127.0.0.1:5000/produtos`

Clique no botão **"Fornecedores"** ao lado do campo de busca.

---

## 📋 Funcionalidades

### ✅ Cadastro Completo de Fornecedores

O sistema permite registrar:

#### **Dados Básicos**
- Nome / Razão Social (obrigatório)
- Nome Fantasia
- CNPJ / CPF
- Inscrição Estadual

#### **Contato**
- Email
- Telefone
- Celular
- Site

#### **Endereço Completo**
- CEP
- Logradouro, Número, Complemento
- Bairro, Cidade, Estado

#### **Informações Comerciais**
- Produtos/Serviços fornecidos
- Prazo de entrega
- Condições de pagamento

#### **Dados Bancários**
- Banco
- Agência
- Conta
- Chave PIX

#### **Contato Principal**
- Nome do contato
- Cargo
- Telefone
- Email

#### **Avaliação e Status**
- Avaliação (1 a 5 estrelas)
- Status (Ativo, Inativo, Bloqueado)
- Observações

---

### 🔍 Filtros e Busca

- **Busca por texto**: Nome, CNPJ, Cidade
- **Filtro por Status**: Ativo, Inativo, Bloqueado
- **Filtro por Avaliação**: 1 a 5 estrelas

---

### 📊 Estatísticas em Tempo Real

O sistema exibe automaticamente:
- Total de fornecedores
- Quantos estão ativos
- Quantos estão inativos
- Média de avaliação

---

### 🎯 Ações Disponíveis

Para cada fornecedor você pode:

1. **👁️ Visualizar**: Ver todos os dados em um modal de leitura
2. **✏️ Editar**: Modificar qualquer informação
3. **🗑️ Excluir**: Remover o fornecedor (com confirmação)

---

## 🎨 Interface

- **Design moderno e responsivo**: Com Bootstrap 5
- **Cards interativos**: Com efeito hover
- **Badges coloridos**: Para status (Ativo/Inativo/Bloqueado)
- **Ícones intuitivos**: Bootstrap Icons
- **Modal em fullscreen**: Para cadastro/edição completa
- **Grid responsivo**: Adapta-se a diferentes tamanhos de tela

---

## 🔐 Segurança

- Sistema integrado com autenticação do CRM
- Multi-tenant: Cada usuário vê apenas seus fornecedores
- Validações de permissão usando `@permission_required('produtos')`

---

## 🗄️ Estrutura do Banco de Dados

### Tabela: `fornecedor`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | Integer | Chave primária
| usuario_crm_id | Integer | FK para usuario_crm
| nome | String(200) | Nome/Razão Social (obrigatório)
| nome_fantasia | String(200) | Nome Fantasia
| cnpj_cpf | String(20) | CNPJ ou CPF
| inscricao_estadual | String(50) | IE
| email | String(200) | Email
| telefone | String(50) | Telefone
| celular | String(50) | Celular
| site | String(200) | Website
| cep | String(10) | CEP
| logradouro | String(200) | Rua/Av
| numero | String(20) | Número
| complemento | String(100) | Complemento
| bairro | String(100) | Bairro
| cidade | String(100) | Cidade
| estado | String(2) | UF
| produtos_servicos | Text | Descrição
| prazo_entrega | String(100) | Prazo médio
| prazo_pagamento | String(100) | Condições
| banco | String(100) | Banco
| agencia | String(20) | Agência
| conta | String(30) | Conta
| pix | String(100) | Chave PIX
| contato_nome | String(100) | Nome do contato
| contato_cargo | String(100) | Cargo
| contato_telefone | String(50) | Telefone
| contato_email | String(200) | Email
| avaliacao | Integer | 1-5 estrelas
| status | String(20) | Ativo/Inativo/Bloqueado
| observacoes | Text | Observações
| data_cadastro | DateTime | Data de criação
| ultima_atualizacao | DateTime | Última modificação

---

## 🔗 Rotas da API

### GET `/fornecedores`
Lista todos os fornecedores (HTML)

### GET `/api/fornecedores`
Retorna lista em JSON

### POST `/api/fornecedores/add`
Cria novo fornecedor

### GET `/api/fornecedores/<id>`
Retorna dados de um fornecedor

### PUT `/api/fornecedores/<id>`
Atualiza fornecedor

### DELETE `/api/fornecedores/<id>`
Exclui fornecedor

---

## 💡 Dicas de Uso

1. **Avaliação**: Use para ranquear seus melhores fornecedores
2. **Status Bloqueado**: Para fornecedores temporariamente suspensos
3. **Observações**: Registre histórico de entregas, problemas, etc.
4. **Produtos/Serviços**: Detalhe o que cada fornecedor oferece
5. **Dados Bancários**: Facilita o processo de pagamento

---

## 🐛 Solução de Problemas

### Erro ao acessar a página
- Verifique se executou o script `add_fornecedores_table.py`
- Confirme que o servidor está rodando

### Fornecedores não aparecem
- Verifique se está logado no sistema
- Confirme que tem permissão para o módulo "produtos"

### Erro ao salvar
- Verifique se o campo "Nome" está preenchido (obrigatório)
- Confira a conexão com o banco de dados

---

## 📝 Changelog

### Versão 1.0 (22/02/2026)
- ✅ Sistema completo de CRUD de fornecedores
- ✅ Interface moderna e responsiva
- ✅ Filtros e busca avançada
- ✅ Estatísticas em tempo real
- ✅ Multi-tenant (isolamento por usuário)
- ✅ Validações e segurança
- ✅ Modal de visualização detalhada
- ✅ Integração com sistema de produtos

---

## 🎯 Próximas Melhorias (Sugestões)

- [ ] Histórico de compras por fornecedor
- [ ] Anexo de documentos (contratos, certidões)
- [ ] Relatórios em PDF/Excel
- [ ] Integração com produtos (vincular fornecedor ao produto)
- [ ] Dashboard de performance de fornecedores
- [ ] Alertas de vencimento de documentos
- [ ] Chat/mensagens com fornecedores

---

## 📞 Suporte

Para problemas ou dúvidas:
1. Verifique este README
2. Consulte os logs do servidor
3. Entre em contato com o suporte técnico

---

**Desenvolvido para CRM Multi-Tenant** 🚀
