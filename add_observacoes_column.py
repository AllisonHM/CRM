"""
Script para adicionar a coluna observacoes na tabela cliente
"""
import psycopg2

# Configurações do banco de dados
DB_CONFIG = {
    'host': 'localhost',
    'port': 1222,
    'database': 'crm',
    'user': 'postgres',
    'password': 'Amovoce123@'
}

def adicionar_coluna_observacoes():
    try:
        # Conectar ao banco
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='cliente' AND column_name='observacoes'
        """)
        
        if cursor.fetchone():
            print("✅ Coluna 'observacoes' já existe!")
        else:
            # Adicionar a coluna
            cursor.execute("""
                ALTER TABLE cliente 
                ADD COLUMN observacoes TEXT
            """)
            conn.commit()
            print("✅ Coluna 'observacoes' adicionada com sucesso!")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao adicionar coluna: {e}")

if __name__ == "__main__":
    adicionar_coluna_observacoes()
