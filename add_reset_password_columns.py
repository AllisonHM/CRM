"""
Script para adicionar campos de recuperação de senha na tabela usuario_crm
"""
import psycopg2

def get_db_connection():
    """Obtém conexão com o banco de dados"""
    return psycopg2.connect(
        database='crm',
        user='postgres',
        password='Amovoce123@',
        host='localhost',
        port=1222
    )

def add_reset_columns():
    """Adiciona colunas de recuperação de senha"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        print("=" * 70)
        print("ADICIONANDO COLUNAS DE RECUPERAÇÃO DE SENHA")
        print("=" * 70 + "\n")
        
        # Verifica se as colunas já existem
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'usuario_crm' 
            AND column_name IN ('reset_token', 'reset_token_expira');
        """)
        
        existing_columns = [row[0] for row in cur.fetchall()]
        
        # Adiciona reset_token se não existir
        if 'reset_token' not in existing_columns:
            print("Adicionando coluna 'reset_token'...")
            cur.execute("""
                ALTER TABLE usuario_crm 
                ADD COLUMN reset_token VARCHAR(255) NULL;
            """)
            print("✅ Coluna 'reset_token' adicionada!")
        else:
            print("⚠️  Coluna 'reset_token' já existe, pulando...")
        
        # Adiciona reset_token_expira se não existir
        if 'reset_token_expira' not in existing_columns:
            print("Adicionando coluna 'reset_token_expira'...")
            cur.execute("""
                ALTER TABLE usuario_crm 
                ADD COLUMN reset_token_expira TIMESTAMP NULL;
            """)
            print("✅ Coluna 'reset_token_expira' adicionada!")
        else:
            print("⚠️  Coluna 'reset_token_expira' já existe, pulando...")
        
        conn.commit()
        print("\n" + "=" * 70)
        print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 70)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro ao adicionar colunas: {e}")
        raise
    
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    add_reset_columns()
