"""
Script consolidado para verificar e corrigir constraints CASCADE
no banco de dados CRM
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

def listar_constraints_sem_cascade():
    """Lista todas as constraints de FK sem CASCADE"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        print("\n" + "=" * 70)
        print("VERIFICANDO CONSTRAINTS SEM CASCADE")
        print("=" * 70 + "\n")
        
        cur.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            JOIN information_schema.referential_constraints AS rc
                ON tc.constraint_name = rc.constraint_name
                AND tc.table_schema = rc.constraint_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                AND ccu.table_name = 'usuario_crm'
                AND rc.delete_rule != 'CASCADE'
            ORDER BY tc.table_name;
        """)
        
        results = cur.fetchall()
        
        if not results:
            print("✅ Todas as constraints para usuario_crm já possuem CASCADE!")
        else:
            print(f"⚠️  Encontradas {len(results)} constraint(s) sem CASCADE:\n")
            for row in results:
                table_name, constraint_name, column_name, foreign_table, delete_rule = row
                print(f"  • Tabela: {table_name}")
                print(f"    Constraint: {constraint_name}")
                print(f"    Coluna: {column_name} -> {foreign_table}")
                print(f"    Regra atual: {delete_rule}\n")
        
        return results
        
    finally:
        cur.close()
        conn.close()

def corrigir_constraint(table_name, constraint_name, column_name):
    """Corrige uma constraint específica"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        print(f"Corrigindo constraint '{constraint_name}' da tabela '{table_name}'...")
        
        # Remove a constraint antiga
        cur.execute(f"""
            ALTER TABLE {table_name} 
            DROP CONSTRAINT {constraint_name};
        """)
        
        # Adiciona a nova constraint com CASCADE
        cur.execute(f"""
            ALTER TABLE {table_name} 
            ADD CONSTRAINT {constraint_name} 
            FOREIGN KEY ({column_name}) 
            REFERENCES usuario_crm(id) 
            ON DELETE CASCADE;
        """)
        
        conn.commit()
        print(f"✅ Constraint '{constraint_name}' corrigida com sucesso!\n")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro ao corrigir constraint: {e}\n")
        return False
        
    finally:
        cur.close()
        conn.close()

def verificar_e_corrigir_todas():
    """Verifica e corrige todas as constraints necessárias"""
    print("\n" + "=" * 70)
    print("SISTEMA DE CORREÇÃO DE CONSTRAINTS CASCADE")
    print("=" * 70)
    
    # Lista constraints sem CASCADE
    constraints = listar_constraints_sem_cascade()
    
    if not constraints:
        print("\n✅ Nenhuma correção necessária!")
        return
    
    # Pergunta se deseja corrigir
    print("=" * 70)
    resposta = input("\nDeseja corrigir todas as constraints listadas? (s/n): ")
    
    if resposta.lower() != 's':
        print("Operação cancelada.")
        return
    
    print("\n" + "=" * 70)
    print("APLICANDO CORREÇÕES")
    print("=" * 70 + "\n")
    
    sucesso = 0
    falhas = 0
    
    for table_name, constraint_name, column_name, _, _ in constraints:
        if corrigir_constraint(table_name, constraint_name, column_name):
            sucesso += 1
        else:
            falhas += 1
    
    # Resumo
    print("=" * 70)
    print("RESUMO DAS CORREÇÕES")
    print("=" * 70)
    print(f"✅ Sucesso: {sucesso}")
    print(f"❌ Falhas: {falhas}")
    print(f"📊 Total: {len(constraints)}")
    print("=" * 70)

if __name__ == '__main__':
    verificar_e_corrigir_todas()
