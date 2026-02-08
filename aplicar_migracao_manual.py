"""Script para aplicar migração manual das novas colunas e tabelas"""
import psycopg2

# Conectar ao banco
conn = psycopg2.connect(
    dbname="crm",
    user="postgres",
    password="Amovoce123@",
    host="localhost",
    port="1222"
)
conn.autocommit = True
cursor = conn.cursor()

print("🔧 Aplicando migração...")

# Adicionar coluna data_fechamento
try:
    cursor.execute("""
        ALTER TABLE mesa_negocio 
        ADD COLUMN IF NOT EXISTS data_fechamento DATE;
    """)
    print("✅ Coluna data_fechamento adicionada")
except Exception as e:
    print(f"⚠️ Erro ao adicionar data_fechamento: {e}")

# Criar tabela tarefa
try:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tarefa (
            id SERIAL PRIMARY KEY,
            usuario_crm_id INTEGER REFERENCES usuario_crm(id),
            cliente_id INTEGER REFERENCES cliente(id),
            mesa_negocio_id INTEGER REFERENCES mesa_negocio(id),
            titulo VARCHAR(200) NOT NULL,
            descricao TEXT,
            prioridade VARCHAR(20) NOT NULL DEFAULT 'Normal',
            status VARCHAR(20) NOT NULL DEFAULT 'Pendente',
            data_vencimento DATE,
            hora_vencimento TIME,
            lembrete_em TIMESTAMP,
            lembrete_enviado BOOLEAN NOT NULL DEFAULT FALSE,
            criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
            concluido_em TIMESTAMP
        );
    """)
    print("✅ Tabela tarefa criada")
except Exception as e:
    print(f"⚠️ Erro ao criar tabela tarefa: {e}")

cursor.close()
conn.close()

print("✅ Migração concluída!")
