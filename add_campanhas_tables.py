"""
Script para adicionar as tabelas de Campanhas ao banco de dados.

Este script cria:
- Tabela 'campanha' para gerenciar campanhas de marketing/vendas
- Tabela 'lead_campanha' para gerenciar leads dentro de cada campanha
- Índices para otimização de consultas

Uso:
    python add_campanhas_tables.py
"""

from database_rls import db
from CRM import app
from models import Campanha, LeadCampanha
from sqlalchemy import text, inspect

def verificar_tabela_existe(table_name):
    """Verifica se uma tabela já existe no banco de dados."""
    inspector = inspect(db.engine)
    return table_name in inspector.get_table_names()

def criar_tabelas_campanhas():
    """Cria as tabelas de campanhas no banco de dados."""
    with app.app_context():
        print("\n" + "="*60)
        print("CRIAÇÃO DE TABELAS: MÓDULO DE CAMPANHAS")
        print("="*60 + "\n")
        
        # Verificar se as tabelas já existem
        campanha_existe = verificar_tabela_existe('campanha')
        lead_existe = verificar_tabela_existe('lead_campanha')
        
        if campanha_existe and lead_existe:
            print("⚠️  As tabelas 'campanha' e 'lead_campanha' já existem!")
            resposta = input("Deseja recriá-las? ATENÇÃO: Isso apagará todos os dados! (s/N): ")
            if resposta.lower() != 's':
                print("❌ Operação cancelada pelo usuário.")
                return
            
            # Dropar tabelas existentes
            print("\n🗑️  Removendo tabelas antigas...")
            db.session.execute(text('DROP TABLE IF EXISTS lead_campanha CASCADE'))
            db.session.execute(text('DROP TABLE IF EXISTS campanha CASCADE'))
            db.session.commit()
            print("✅ Tabelas antigas removidas.")
        
        try:
            print("\n📊 Criando tabelas de campanhas...")
            
            # Criar tabelas usando SQLAlchemy
            Campanha.__table__.create(db.engine, checkfirst=True)
            LeadCampanha.__table__.create(db.engine, checkfirst=True)
            
            print("✅ Tabela 'campanha' criada com sucesso!")
            print("✅ Tabela 'lead_campanha' criada com sucesso!")
            
            # Verificar criação
            print("\n🔍 Verificando estrutura das tabelas...")
            
            inspector = inspect(db.engine)
            
            # Colunas da tabela campanha
            colunas_campanha = inspector.get_columns('campanha')
            print(f"\n📋 Tabela 'campanha' ({len(colunas_campanha)} colunas):")
            for col in colunas_campanha:
                print(f"   • {col['name']}: {col['type']}")
            
            # Colunas da tabela lead_campanha
            colunas_lead = inspector.get_columns('lead_campanha')
            print(f"\n📋 Tabela 'lead_campanha' ({len(colunas_lead)} colunas):")
            for col in colunas_lead:
                print(f"   • {col['name']}: {col['type']}")
            
            # Índices
            print("\n🔍 Verificando índices criados...")
            indices_campanha = inspector.get_indexes('campanha')
            indices_lead = inspector.get_indexes('lead_campanha')
            
            print(f"\n📊 Índices da tabela 'campanha': {len(indices_campanha)}")
            for idx in indices_campanha:
                print(f"   • {idx['name']}: {idx['column_names']}")
            
            print(f"\n📊 Índices da tabela 'lead_campanha': {len(indices_lead)}")
            for idx in indices_lead:
                print(f"   • {idx['name']}: {idx['column_names']}")
            
            print("\n" + "="*60)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*60)
            
            print("\n📝 Próximos passos:")
            print("   1. Acesse /mesas_negocio no CRM")
            print("   2. Clique na aba 'Campanhas'")
            print("   3. Crie sua primeira campanha!")
            
        except Exception as e:
            print(f"\n❌ ERRO ao criar tabelas: {e}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    criar_tabelas_campanhas()
