# CRM Completo

Sistema de CRM (Customer Relationship Management) desenvolvido com Flask.

## Funcionalidades

- Gerenciamento de clientes
- Mesas de negócio
- Ocorrências
- Canais de comunicação
- Whatsapp integrado
- Chat bot
- Análise de clientes
- Planejamento
- Gestão de produtos

## Requisitos

- Python 3.7+
- Flask
- SQLAlchemy
- Alembic (para migrações)

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual: `python -m venv .venv`
3. Ative o ambiente: `.venv\Scripts\activate`
4. Instale as dependências: `pip install -r requirements.txt`
5. Configure o banco de dados com Alembic: `alembic upgrade head`

## Executar a aplicação

```bash
python CRM.py
```

## Estrutura do Projeto

- `CRM.py` - Arquivo principal da aplicação
- `models.py` - Modelos de dados
- `routes.py` - Rotas da aplicação
- `database.py` - Configuração do banco de dados
- `tasks.py` - Tarefas assíncronas
- `templates/` - Templates HTML
- `migrations/` - Scripts de migração do banco de dados
