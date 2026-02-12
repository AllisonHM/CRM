# -*- coding: utf-8 -*-
"""
Script para corrigir constraint UNIQUE da tabela produto no PostgreSQL
"""
import psycopg2

DATABASE_URL = 'postgresql://postgres:Amovoce123@localhost:1222/crm'

print("="   * 80)
print("CORRECAO DE CONSTRAINT - TABELA PRODUTO")
print("=" * 80)

conn = None
cursor = None

try:
    print("\nConectando ao banco PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    print("Conectado com sucesso!")
    
    print("\nVerificando constraints existentes...")
    cursor.execute("""
        SELECT conname, contype 
        FROM pg_constraint 
        WHERE conrelid = 'produto'::regclass
        ORDER BY conname
    """)
    
    constraints = cursor.fetchall()
    print(f"\nConstraints encontradas: {len(constraints)}")
    for c in constraints:
        tipo_map = {'p': 'PRIMARY KEY', 'u': 'UNIQUE', 'f': 'FOREIGN KEY', 'c': 'CHECK'}
        print(f"  - {c[0]}: {tipo_map.get(c[1], c[1])}")
    
    # Verifica se existe a constraint antiga produto_nome_key
    cursor.execute("""
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'produto_nome_key' 
        AND conrelid = 'produto'::regclass
    """)
    
    tem_constraint_antiga = cursor.fetchone() is not None
    
    if tem_constraint_antiga:
        print("\nRemovendo constraint antiga 'produto_nome_key'...")
        cursor.execute("ALTER TABLE produto DROP CONSTRAINT IF EXISTS produto_nome_key CASCADE")
        print("Constraint antiga removida!")
    else:
        print("\nConstraint antiga ja foi removida ou nao existe")
    
    # Verifica se já existe a nova constraint
    cursor.execute("""
        SELECT 1 FROM pg_constraint 
        WHERE conname IN ('uq_produto_usuario_nome', 'produto_usuario_crm_id_nome_key')
        AND conrelid = 'produto'::regclass
    """)
    
    tem_constraint_nova = cursor.fetchone() is not None
    
    if not tem_constraint_nova:
        print("\nCriando nova constraint UNIQUE (usuario_crm_id, nome)...")
        cursor.execute("""
            ALTER TABLE produto 
            ADD CONSTRAINT uq_produto_usuario_nome 
            UNIQUE (usuario_crm_id, nome)
        """)
        print("Nova constraint criada!")
    else:
        print("\nNova constraint ja existe!")
    
    # Commit das mudanças
    conn.commit()
    
    # Verifica resultado final
    print("\nConstraints finais na tabela produto:")
    cursor.execute("""
        SELECT conname, contype 
        FROM pg_constraint 
        WHERE conrelid = 'produto'::regclass
        ORDER BY conname
    """)
    
    constraints_final = cursor.fetchall()
    for c in constraints_final:
        tipo_map = {'p': 'PRIMARY KEY', 'u': 'UNIQUE', 'f': 'FOREIGN KEY', 'c': 'CHECK'}
        print(f"  - {c[0]}: {tipo_map.get(c[1], c[1])}")
    
    print("\n" + "=" * 80)
    print("MIGRACAO CONCLUIDA COM SUCESSO!")
    print("=" * 80)
    print("\nAgora cada usuario pode ter produtos com o mesmo nome!")
    
except psycopg2.Error as e:
    print(f"\nErro PostgreSQL: {e}")
    if conn:
        conn.rollback()
except Exception as e:
    print(f"\nErro: {e}")
    import traceback
    traceback.print_exc()
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
