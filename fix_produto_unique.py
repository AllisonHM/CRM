"""
Script para corrigir a constraint unique da tabela produto
Permite que usuários diferentes tenham produtos com o mesmo nome
"""
import sqlite3
import os

db_path = os.path.join('instance', 'crm.db')

if not os.path.exists(db_path):
    print(f"❌ Banco de dados não encontrado em: {db_path}")
    exit(1)

print(f"📂 Conectando ao banco: {db_path}")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    print("\n🔍 Verificando estrutura atual da tabela produto...")
    cursor.execute("PRAGMA table_info(produto)")
    columns = cursor.fetchall()
    
    print("📋 Colunas atuais:")
    for col in columns:
        print(f"   - {col[1]}: {col[2]}")
    
    # Verifica constraints existentes
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='produto'")
    table_sql = cursor.fetchone()[0]
    print(f"\n📄 SQL atual da tabela:\n{table_sql}\n")
    
    # Criar tabela temporária
    print("🔧 Criando nova estrutura da tabela...")
    cursor.execute("""
        CREATE TABLE produto_new (
            id INTEGER PRIMARY KEY,
            usuario_crm_id INTEGER,
            nome VARCHAR(200) NOT NULL,
            descricao TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 0,
            ultima_movimentacao_data DATETIME,
            ultima_movimentacao_descricao VARCHAR(255),
            FOREIGN KEY (usuario_crm_id) REFERENCES usuario_crm(id),
            UNIQUE (usuario_crm_id, nome)
        )
    """)
    
    # Copiar dados
    print("📦 Copiando dados para nova tabela...")
    cursor.execute("""
        INSERT INTO produto_new 
        SELECT id, usuario_crm_id, nome, descricao, quantidade, 
               ultima_movimentacao_data, ultima_movimentacao_descricao
        FROM produto
    """)
    
    # Remover tabela antiga
    print("🗑️ Removendo tabela antiga...")
    cursor.execute("DROP TABLE produto")
    
    # Renomear nova tabela
    print("✏️ Renomeando nova tabela...")
    cursor.execute("ALTER TABLE produto_new RENAME TO produto")
    
    # Commit
    conn.commit()
    print("\n✅ Migração concluída com sucesso!")
    
    # Verificar nova estrutura
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='produto'")
    new_table_sql = cursor.fetchone()[0]
    print(f"\n📄 Nova estrutura da tabela:\n{new_table_sql}\n")
    
except Exception as e:
    print(f"\n❌ Erro durante migração: {e}")
    conn.rollback()
    raise
finally:
    conn.close()

print("\n✨ Agora cada usuário pode ter produtos com o mesmo nome independentemente!")
