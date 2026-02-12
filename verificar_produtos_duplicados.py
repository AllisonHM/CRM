"""
Script para verificar e limpar produtos duplicados no banco
"""
import sqlite3
import os

db_path = os.path.join('instance', 'crm.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 Verificando produtos no banco de dados...\n")

# Lista todos os produtos
cursor.execute("""
    SELECT p.id, p.usuario_crm_id, p.nome, p.quantidade, u.nome as usuario_nome
    FROM produto p
    LEFT JOIN usuario_crm u ON p.usuario_crm_id = u.id
    ORDER BY p.usuario_crm_id, p.nome
""")

produtos = cursor.fetchall()

if not produtos:
    print("ℹ️  Nenhum produto cadastrado ainda.")
else:
    print(f"📦 Total de produtos: {len(produtos)}\n")
    print("ID  | Usuário ID | Nome do Produto        | Qtd | Usuário")
    print("-" * 70)
    for p in produtos:
        print(f"{p[0]:<4}| {p[1] or 'NULL':<11}| {p[2]:<23}| {p[3]:<4}| {p[4] or 'N/A'}")

# Verifica duplicados
print("\n🔍 Verificando duplicados (mesmo usuário + mesmo nome)...")
cursor.execute("""
    SELECT usuario_crm_id, nome, COUNT(*) as total
    FROM produto
    GROUP BY usuario_crm_id, nome
    HAVING COUNT(*) > 1
""")

duplicados = cursor.fetchall()

if duplicados:
    print(f"\n⚠️  Encontrados {len(duplicados)} registros duplicados:")
    for d in duplicados:
        print(f"   - Usuário ID {d[0]}: '{d[1]}' ({d[2]} vezes)")
        
    resposta = input("\n❓ Deseja remover as duplicatas? (s/n): ").strip().lower()
    if resposta == 's':
        for d in duplicados:
            usuario_id, nome, _ = d
            # Manter apenas o primeiro registro
            cursor.execute("""
                DELETE FROM produto 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM produto 
                    WHERE usuario_crm_id = ? AND nome = ?
                )
                AND usuario_crm_id = ? AND nome = ?
            """, (usuario_id, nome, usuario_id, nome))
        
        conn.commit()
        print("\n✅ Duplicatas removidas com sucesso!")
else:
    print("✅ Nenhuma duplicata encontrada!")

conn.close()
