"""
Script para debug - verificar estrutura de usuários e produtos
"""
import sqlite3
import os

db_path = os.path.join('instance', 'crm.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("🔍 DEBUG: USUÁRIOS E PRODUTOS")
print("=" * 80)

# Lista todos os usuários
print("\n👥 USUÁRIOS CADASTRADOS:")
print("-" * 80)
cursor.execute("""
    SELECT id, nome, email, tipo_usuario, usuario_pai_id
    FROM usuario_crm
    ORDER BY id
""")

usuarios = cursor.fetchall()
print(f"Total: {len(usuarios)} usuários\n")
print("ID  | Nome                  | Email                    | Tipo         | Pai ID")
print("-" * 80)
for u in usuarios:
    print(f"{u[0]:<4}| {u[1]:<22}| {u[2]:<25}| {u[3]:<13}| {u[4] or '-'}")

# Lista todos os produtos
print("\n\n📦 PRODUTOS CADASTRADOS:")
print("-" * 80)
cursor.execute("""
    SELECT p.id, p.usuario_crm_id, p.nome, p.descricao, p.quantidade, u.nome as usuario_nome, u.tipo_usuario
    FROM produto p
    LEFT JOIN usuario_crm u ON p.usuario_crm_id = u.id
    ORDER BY p.usuario_crm_id, p.nome
""")

produtos = cursor.fetchall()
if not produtos:
    print("ℹ️  Nenhum produto cadastrado ainda.")
else:
    print(f"Total: {len(produtos)} produtos\n")
    print("ID  | Usuário | Nome Produto      | Qtd | Dono (Nome/Tipo)")
    print("-" * 80)
    for p in produtos:
        print(f"{p[0]:<4}| {p[1] or 'NULL':<8}| {p[2]:<18}| {p[4]:<4}| {p[5] or 'N/A'} ({p[6] or 'N/A'})")

# Verifica structure da tabela produto
print("\n\n🔧 ESTRUTURA DA TABELA PRODUTO:")
print("-" * 80)
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='produto'")
table_sql = cursor.fetchone()
if table_sql:
    print(table_sql[0])

# Testa inserção
print("\n\n🧪 TESTE DE INSERÇÃO:")
print("-" * 80)
print("Testando se podemos inserir produtos com mesmo nome em usuários diferentes...\n")

# Pega IDs de diferentes usuários
cursor.execute("SELECT id, nome, tipo_usuario FROM usuario_crm LIMIT 3")
test_users = cursor.fetchall()

for user in test_users:
    user_id, user_nome, user_tipo = user
    test_produto_nome = "PRODUTO_TESTE_DEBUG"
    
    # Verifica se já existe
    cursor.execute("SELECT id FROM produto WHERE usuario_crm_id = ? AND nome = ?", (user_id, test_produto_nome))
    existe = cursor.fetchone()
    
    if existe:
        print(f"   ✓ Usuário {user_id} ({user_nome}) já tem produto '{test_produto_nome}'")
    else:
        print(f"   • Usuário {user_id} ({user_nome}): pode criar produto '{test_produto_nome}'")

conn.close()

print("\n" + "=" * 80)
print("✅ Debug concluído!")
print("=" * 80)
