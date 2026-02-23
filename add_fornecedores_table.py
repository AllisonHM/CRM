"""
Script para adicionar a tabela de fornecedores ao banco de dados
"""
from database_rls import db, init_db
from models import Fornecedor
from CRM import app

def criar_tabela_fornecedores():
    """Cria a tabela de fornecedores no banco de dados"""
    with app.app_context():
        print("🔧 Iniciando criação da tabela de fornecedores...")
        
        try:
            # Cria todas as tabelas que não existem
            db.create_all()
            print("✅ Tabela 'fornecedor' criada com sucesso!")
            print("✅ Sistema de fornecedores pronto para uso!")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabela: {e}")
            return False
        
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("CRIAÇÃO DA TABELA DE FORNECEDORES")
    print("=" * 60)
    
    if criar_tabela_fornecedores():
        print("\n✅ Migração concluída com sucesso!")
        print("Você já pode usar o sistema de fornecedores.")
    else:
        print("\n❌ Erro na migração. Verifique os logs acima.")
