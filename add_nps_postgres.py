import psycopg2
import os

# Configuração do banco (ajuste conforme seu .env ou configuração)
DATABASE_URL = 'postgresql://postgres:Amovoce123%40@localhost:1222/crm'

try:
    # Conectar ao PostgreSQL
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Adicionar campos de NPS
    print("Adicionando campos de NPS...")
    
    try:
        cursor.execute("ALTER TABLE cliente ADD COLUMN nps_nota INTEGER")
        print("✅ Campo nps_nota adicionado")
    except psycopg2.errors.DuplicateColumn:
        print("⚠️ Campo nps_nota já existe")
    
    try:
        cursor.execute("ALTER TABLE cliente ADD COLUMN nps_data TIMESTAMP")
        print("✅ Campo nps_data adicionado")
    except psycopg2.errors.DuplicateColumn:
        print("⚠️ Campo nps_data já existe")
    
    try:
        cursor.execute("ALTER TABLE cliente ADD COLUMN nps_comentario TEXT")
        print("✅ Campo nps_comentario adicionado")
    except psycopg2.errors.DuplicateColumn:
        print("⚠️ Campo nps_comentario já existe")
    
    try:
        cursor.execute("ALTER TABLE cliente ADD COLUMN aguardando_nps BOOLEAN DEFAULT FALSE")
        print("✅ Campo aguardando_nps adicionado")
    except psycopg2.errors.DuplicateColumn:
        print("⚠️ Campo aguardando_nps já existe")
    
    conn.commit()
    print("\n🎉 Migração concluída com sucesso!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    print("\nVerifique:")
    print("1. Se o PostgreSQL está rodando")
    print("2. Se a DATABASE_URL está correta")
    print("3. Se você tem permissões para alterar a tabela")
    
finally:
    if 'conn' in locals():
        cursor.close()
        conn.close()
