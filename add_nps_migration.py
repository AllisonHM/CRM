import sqlite3
from datetime import datetime

# Conectar ao banco de dados
conn = sqlite3.connect('instance/crm.db')
cursor = conn.cursor()

try:
    # Adicionar campos de NPS
    cursor.execute("ALTER TABLE cliente ADD COLUMN nps_nota INTEGER")
    cursor.execute("ALTER TABLE cliente ADD COLUMN nps_data DATETIME")
    cursor.execute("ALTER TABLE cliente ADD COLUMN nps_comentario TEXT")
    cursor.execute("ALTER TABLE cliente ADD COLUMN aguardando_nps BOOLEAN DEFAULT 0")
    
    conn.commit()
    print("✅ Campos de NPS adicionados com sucesso!")
    
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("⚠️ Campos já existem no banco de dados")
    else:
        print(f"❌ Erro: {e}")
        
finally:
    conn.close()
