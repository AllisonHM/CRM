"""
Script para corrigir a constraint de foreign key da tabela parametrizacao
para adicionar CASCADE na deleção
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

def fix_cascade():
    """Corrige a constraint para adicionar CASCADE"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        print("Iniciando correção da constraint de parametrizacao...")
        
        # 1. Primeiro, vamos descobrir o nome da constraint atual
        cur.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'parametrizacao' 
            AND constraint_type = 'FOREIGN KEY'
            AND constraint_name LIKE '%usuario_crm_id%';
        """)
        
        result = cur.fetchone()
        if result:
            constraint_name = result[0]
            print(f"Constraint encontrada: {constraint_name}")
            
            # 2. Remove a constraint antiga
            print(f"Removendo constraint antiga...")
            cur.execute(f"""
                ALTER TABLE parametrizacao 
                DROP CONSTRAINT {constraint_name};
            """)
            print("Constraint antiga removida!")
        else:
            print("Buscando constraint por nome padrão...")
            # Tenta com o nome padrão do SQLAlchemy
            try:
                cur.execute("""
                    ALTER TABLE parametrizacao 
                    DROP CONSTRAINT parametrizacao_usuario_crm_id_fkey;
                """)
                print("Constraint padrão removida!")
            except:
                print("Não foi possível encontrar constraint existente, continuando...")
        
        # 3. Adiciona a nova constraint com CASCADE
        print("Adicionando nova constraint com CASCADE...")
        cur.execute("""
            ALTER TABLE parametrizacao 
            ADD CONSTRAINT parametrizacao_usuario_crm_id_fkey 
            FOREIGN KEY (usuario_crm_id) 
            REFERENCES usuario_crm(id) 
            ON DELETE CASCADE;
        """)
        
        conn.commit()
        print("✅ Constraint de parametrizacao corrigida com sucesso!")
        print("Agora a parametrização será deletada automaticamente quando o usuário for deletado.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao corrigir constraint: {e}")
        raise
    
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("CORREÇÃO DA CONSTRAINT DE PARAMETRIZACAO")
    print("=" * 60)
    fix_cascade()
