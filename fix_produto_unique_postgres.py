"""
Script para corrigir constraint UNIQUE da tabela produto no PostgreSQL
Remove a constraint antiga (nome) e adiciona a nova (usuario_crm_id, nome)
"""
import psycopg2
from urllib.parse import urlparse, unquote
import os

# Pega a URL do banco de dados do CRM.py
DATABASE_URL = 'postgresql://postgres:Amovoce123@localhost:1222/crm'

print("=" * 80)
print("CORRECAO DE CONSTRAINT - TABELA PRODUTO (PostgreSQL)")
print("=" * 80)
print(f"\nConectando ao banco: localhost:1222/crm")

conn = None
cursor = None

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    print("\nVerificando constraints existentes...")
    cursor.execute("""
        SELECT conname, contype 
        FROM pg_constraint 
        WHERE conrelid = 'produto'::regclass
        ORDER BY conname
    """)
    
    constraints = cursor.fetchall()
    print(f"Constraints encontradas ({len(constraints)}):")
    for c in constraints:
        tipo_map = {'p': 'PRIMARY KEY', 'u': 'UNIQUE', 'f': 'FOREIGN KEY', 'c': 'CHECK'}
        print(f"   - {c[0]}: {tipo_map.get(c[1], c[1])}")
    
    # Verifica se existe a constraint antiga produto_nome_key
    cursor.execute("""
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'produto_nome_key' 
        AND conrelid = 'produto'::regclass
    """)
    
    tem_constraint_antiga = cursor.fetchone() is not None
    
    if tem_constraint_antiga:
        print("\n⚠️ Encontrada constraint antiga 'produto_nome_key' (UNIQUE apenas no nome)")
        print("🗑️ Removendo constraint antiga...")
        cursor.execute("ALTER TABLE produto DROP CONSTRAINT IF EXISTS produto_nome_key CASCADE")
        print("   ✅ Constraint antiga removida!")
    else:
        print("\n✅ Constraint antiga já foi removida ou não existe")
    
    # Verifica se já existe a nova constraint
    cursor.execute("""
        SELECT 1 FROM pg_constraint 
        WHERE conname IN ('uq_produto_usuario_nome', 'produto_usuario_crm_id_nome_key')
        AND conrelid = 'produto'::regclass
    """)
    
    tem_constraint_nova = cursor.fetchone() is not None
    
    if not tem_constraint_nova:
        print("\n🔧 Criando nova constraint UNIQUE (usuario_crm_id, nome)...")
        cursor.execute("""
            ALTER TABLE produto 
            ADD CONSTRAINT uq_produto_usuario_nome 
            UNIQUE (usuario_crm_id, nome)
        """)
        print("   ✅ Nova constraint criada!")
    else:
        print("\n✅ Nova constraint já existe!")
    
    # Commit das mudanças
    conn.commit()
    
    # Verifica resultado final
    print("\n📋 Constraints finais na tabela produto:")
    cursor.execute("""
        SELECT conname, contype 
        FROM pg_constraint 
        WHERE conrelid = 'produto'::regclass
        ORDER BY conname
    """)
    
    constraints_final = cursor.fetchall()
    for c in constraints_final:
        tipo_map = {'p': 'PRIMARY KEY', 'u': 'UNIQUE', 'f': 'FOREIGN KEY', 'c': 'CHECK'}
        print(f"   - {c[0]}: {tipo_map.get(c[1], c[1])}")
    
    print("\n" + "=" * 80)
    print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    print("\n✨ Agora cada usuário pode ter produtos com o mesmo nome independentemente!")
    
except psycopg2.Error as e:
    print(f"\n❌ Erro PostgreSQL: {e}")
    if conn:
        conn.rollback()
except Exception as e:
    print(f"\n❌ Erro: {e}")
finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()
