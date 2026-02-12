"""Script para verificar nullability das colunas usuario_crm_id"""
import psycopg2

conn = psycopg2.connect(
    database='crm',
    user='postgres',
    password='Amovoce123@',
    host='localhost',
    port=1222
)

cur = conn.cursor()

cur.execute("""
    SELECT table_name, column_name, is_nullable 
    FROM information_schema.columns 
    WHERE column_name = 'usuario_crm_id' 
    AND table_schema = 'public' 
    ORDER BY table_name;
""")

print("\n" + "=" * 80)
print("VERIFICANDO NULLABILITY DAS COLUNAS usuario_crm_id")
print("=" * 80 + "\n")

print(f"{'Tabela':<30} {'Coluna':<20} {'Nullable':<10}")
print("-" * 80)

for row in cur.fetchall():
    table, column, nullable = row
    status = "✅ YES" if nullable == 'YES' else "⚠️  NO"
    print(f"{table:<30} {column:<20} {status:<10}")

print("=" * 80)

conn.close()
