"""
Script para adicionar coluna produtos_quantidades na tabela mesa_negocio
"""
from sqlalchemy import create_engine, text
import sys

# Configurações do banco
DATABASE_URI = 'postgresql+psycopg2://postgres:Amovoce123%40@localhost:1222/crm'

def adicionar_coluna():
    try:
        engine = create_engine(DATABASE_URI)
        
        with engine.connect() as conn:
            # Verificar se a coluna já existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='mesa_negocio' 
                AND column_name='produtos_quantidades'
            """))
            
            if result.fetchone():
                print("✅ A coluna 'produtos_quantidades' já existe na tabela 'mesa_negocio'")
                return
            
            # Adicionar a coluna
            print("➕ Adicionando coluna 'produtos_quantidades' na tabela 'mesa_negocio'...")
            conn.execute(text("""
                ALTER TABLE mesa_negocio 
                ADD COLUMN produtos_quantidades JSONB
            """))
            conn.commit()
            
            print("✅ Coluna 'produtos_quantidades' adicionada com sucesso!")
            
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    adicionar_coluna()
