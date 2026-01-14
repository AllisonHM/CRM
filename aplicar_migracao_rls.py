"""
Script de migração automática para RLS
Aplica todas as mudanças necessárias no banco de dados
"""
import psycopg2
from psycopg2 import sql
import sys
import os
from datetime import datetime

# Configurações do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 1222,
    'database': 'crm',
    'user': 'postgres',
    'password': 'Amovoce123@'
}

def criar_backup():
    """Cria backup do banco antes da migração"""
    print("📦 Criando backup do banco de dados...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backup_antes_rls_{timestamp}.sql'
    
    comando = f'pg_dump -h {DB_CONFIG["host"]} -p {DB_CONFIG["port"]} -U {DB_CONFIG["user"]} -d {DB_CONFIG["database"]} > {backup_file}'
    
    # No Windows, precisa do SET PGPASSWORD
    os.environ['PGPASSWORD'] = DB_CONFIG['password']
    result = os.system(comando)
    
    if result == 0:
        print(f"✅ Backup criado: {backup_file}")
        return True
    else:
        print(f"❌ Erro ao criar backup. Continue? (s/n)")
        resposta = input().lower()
        return resposta == 's'

def conectar():
    """Conecta ao banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ Conectado ao banco de dados")
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)

def executar_sql(conn, sql_commands, nome_etapa):
    """Executa comandos SQL"""
    print(f"\n{'='*60}")
    print(f"🔧 {nome_etapa}")
    print(f"{'='*60}")
    
    cursor = conn.cursor()
    
    try:
        # Separa comandos por ';' e executa um por um
        for comando in sql_commands.split(';'):
            comando = comando.strip()
            if comando and not comando.startswith('--'):
                try:
                    cursor.execute(comando)
                    print(f"✓ {comando[:80]}...")
                except Exception as e:
                    # Alguns erros são esperados (ex: IF NOT EXISTS)
                    if 'already exists' in str(e) or 'duplicate' in str(e):
                        print(f"⚠ Já existe: {comando[:50]}...")
                    else:
                        print(f"❌ Erro: {e}")
                        print(f"   Comando: {comando[:100]}")
        
        conn.commit()
        print(f"✅ {nome_etapa} - Concluído")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Erro em {nome_etapa}: {e}")
        raise
    finally:
        cursor.close()

def verificar_rls(conn):
    """Verifica se RLS foi ativado"""
    print(f"\n{'='*60}")
    print("🔍 Verificando RLS...")
    print(f"{'='*60}")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tablename, rowsecurity 
        FROM pg_tables 
        WHERE schemaname = 'public' 
          AND tablename IN ('cliente', 'mesa_negocio', 'ocorrencia', 
                           'whatsapp_mensagem', 'produto', 'planner_evento',
                           'chatbot_regra', 'movimentacao')
        ORDER BY tablename
    """)
    
    resultados = cursor.fetchall()
    
    print("\nTabela                 | RLS Ativo")
    print("-" * 40)
    for tabela, rls_ativo in resultados:
        status = "✅ SIM" if rls_ativo else "❌ NÃO"
        print(f"{tabela:20} | {status}")
    
    cursor.close()

def verificar_policies(conn):
    """Verifica se as policies foram criadas"""
    print(f"\n{'='*60}")
    print("🔍 Verificando Políticas RLS...")
    print(f"{'='*60}")
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tablename, COUNT(*) as num_policies
        FROM pg_policies
        WHERE schemaname = 'public'
        GROUP BY tablename
        ORDER BY tablename
    """)
    
    resultados = cursor.fetchall()
    
    print("\nTabela                 | Policies")
    print("-" * 40)
    for tabela, num in resultados:
        print(f"{tabela:20} | {num}")
    
    cursor.close()

def main():
    print("="*60)
    print("🚀 MIGRAÇÃO PARA MULTI-TENANT COM RLS")
    print("="*60)
    print()
    print("Este script vai:")
    print("1. Criar backup do banco atual")
    print("2. Adicionar colunas usuario_crm_id faltantes")
    print("3. Criar função current_tenant_id()")
    print("4. Criar roles app_user e app_admin")
    print("5. Ativar RLS em todas as tabelas")
    print("6. Criar políticas RLS")
    print()
    print("⚠️  IMPORTANTE: Certifique-se de que ninguém está usando o sistema!")
    print()
    
    resposta = input("Deseja continuar? (s/n): ").lower()
    if resposta != 's':
        print("❌ Migração cancelada")
        return
    
    # Criar backup
    if not criar_backup():
        print("❌ Migração cancelada - backup falhou")
        return
    
    # Conectar
    conn = conectar()
    
    try:
        # Etapa 1: Função current_tenant_id
        sql_funcao = """
        CREATE OR REPLACE FUNCTION current_tenant_id() RETURNS INTEGER AS $$
        BEGIN
            RETURN NULLIF(current_setting('app.current_tenant', true), '')::INTEGER;
        EXCEPTION
            WHEN OTHERS THEN
                RETURN NULL;
        END;
        $$ LANGUAGE plpgsql STABLE
        """
        executar_sql(conn, sql_funcao, "ETAPA 1: Criar função current_tenant_id()")
        
        # Etapa 2: Adicionar colunas e índices
        sql_colunas = """
        ALTER TABLE mesa_negocio ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
        ALTER TABLE ocorrencia ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
        ALTER TABLE whatsapp_mensagem ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
        ALTER TABLE produto ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
        ALTER TABLE planner_evento ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
        ALTER TABLE chatbot_regra ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
        ALTER TABLE movimentacao ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER REFERENCES usuario_crm(id);
        
        CREATE INDEX IF NOT EXISTS idx_cliente_tenant ON cliente(usuario_crm_id);
        CREATE INDEX IF NOT EXISTS idx_mesa_tenant ON mesa_negocio(usuario_crm_id);
        CREATE INDEX IF NOT EXISTS idx_ocorrencia_tenant ON ocorrencia(usuario_crm_id);
        CREATE INDEX IF NOT EXISTS idx_whatsapp_tenant ON whatsapp_mensagem(usuario_crm_id);
        CREATE INDEX IF NOT EXISTS idx_produto_tenant ON produto(usuario_crm_id);
        CREATE INDEX IF NOT EXISTS idx_planner_tenant ON planner_evento(usuario_crm_id);
        CREATE INDEX IF NOT EXISTS idx_chatbot_tenant ON chatbot_regra(usuario_crm_id);
        CREATE INDEX IF NOT EXISTS idx_movimentacao_tenant ON movimentacao(usuario_crm_id)
        """
        executar_sql(conn, sql_colunas, "ETAPA 2: Adicionar colunas e índices")
        
        # Etapa 3: Preencher usuario_crm_id baseado em relacionamentos
        print("\n🔧 ETAPA 3: Preencher usuario_crm_id em tabelas relacionadas")
        cursor = conn.cursor()
        
        # Mesa de Negócio (via cliente)
        cursor.execute("""
            UPDATE mesa_negocio m
            SET usuario_crm_id = c.usuario_crm_id
            FROM cliente c
            WHERE m.cliente_id = c.id AND m.usuario_crm_id IS NULL
        """)
        print(f"✓ Mesa de Negócio: {cursor.rowcount} registros atualizados")
        
        # Ocorrência (via cliente)
        cursor.execute("""
            UPDATE ocorrencia o
            SET usuario_crm_id = c.usuario_crm_id
            FROM cliente c
            WHERE o.cliente_id = c.id AND o.usuario_crm_id IS NULL
        """)
        print(f"✓ Ocorrência: {cursor.rowcount} registros atualizados")
        
        conn.commit()
        cursor.close()
        print("✅ ETAPA 3 - Concluído")
        
        # Etapa 4: Criar roles
        sql_roles = """
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_user') THEN
                CREATE ROLE app_user LOGIN PASSWORD 'crm_app_user_2026!';
            END IF;
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_admin') THEN
                CREATE ROLE app_admin LOGIN PASSWORD 'crm_app_admin_2026!';
            END IF;
        END
        $$;
        
        GRANT CONNECT ON DATABASE crm TO app_user, app_admin;
        GRANT USAGE ON SCHEMA public TO app_user, app_admin;
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user, app_admin;
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user, app_admin
        """
        executar_sql(conn, sql_roles, "ETAPA 4: Criar roles")
        
        # Etapa 5: Ativar RLS
        sql_ativar_rls = """
        ALTER TABLE cliente ENABLE ROW LEVEL SECURITY;
        ALTER TABLE cliente FORCE ROW LEVEL SECURITY;
        ALTER TABLE mesa_negocio ENABLE ROW LEVEL SECURITY;
        ALTER TABLE mesa_negocio FORCE ROW LEVEL SECURITY;
        ALTER TABLE ocorrencia ENABLE ROW LEVEL SECURITY;
        ALTER TABLE ocorrencia FORCE ROW LEVEL SECURITY;
        ALTER TABLE whatsapp_mensagem ENABLE ROW LEVEL SECURITY;
        ALTER TABLE whatsapp_mensagem FORCE ROW LEVEL SECURITY;
        ALTER TABLE produto ENABLE ROW LEVEL SECURITY;
        ALTER TABLE produto FORCE ROW LEVEL SECURITY;
        ALTER TABLE planner_evento ENABLE ROW LEVEL SECURITY;
        ALTER TABLE planner_evento FORCE ROW LEVEL SECURITY;
        ALTER TABLE chatbot_regra ENABLE ROW LEVEL SECURITY;
        ALTER TABLE chatbot_regra FORCE ROW LEVEL SECURITY;
        ALTER TABLE movimentacao ENABLE ROW LEVEL SECURITY;
        ALTER TABLE movimentacao FORCE ROW LEVEL SECURITY
        """
        executar_sql(conn, sql_ativar_rls, "ETAPA 5: Ativar RLS")
        
        # Etapa 6: Criar policies (para cada tabela)
        tabelas = ['cliente', 'mesa_negocio', 'ocorrencia', 'whatsapp_mensagem', 
                   'produto', 'planner_evento', 'chatbot_regra', 'movimentacao']
        
        print(f"\n{'='*60}")
        print("🔧 ETAPA 6: Criar Políticas RLS")
        print(f"{'='*60}")
        
        cursor = conn.cursor()
        for tabela in tabelas:
            print(f"\n📋 Criando políticas para: {tabela}")
            
            # DROP policies existentes
            cursor.execute(f"DROP POLICY IF EXISTS policy_{tabela}_select ON {tabela}")
            cursor.execute(f"DROP POLICY IF EXISTS policy_{tabela}_insert ON {tabela}")
            cursor.execute(f"DROP POLICY IF EXISTS policy_{tabela}_update ON {tabela}")
            cursor.execute(f"DROP POLICY IF EXISTS policy_{tabela}_delete ON {tabela}")
            
            # CREATE novas policies
            cursor.execute(f"""
                CREATE POLICY policy_{tabela}_select ON {tabela}
                    FOR SELECT
                    USING (usuario_crm_id = current_tenant_id() OR usuario_crm_id IS NULL)
            """)
            
            cursor.execute(f"""
                CREATE POLICY policy_{tabela}_insert ON {tabela}
                    FOR INSERT
                    WITH CHECK (usuario_crm_id = current_tenant_id())
            """)
            
            cursor.execute(f"""
                CREATE POLICY policy_{tabela}_update ON {tabela}
                    FOR UPDATE
                    USING (usuario_crm_id = current_tenant_id())
                    WITH CHECK (usuario_crm_id = current_tenant_id())
            """)
            
            cursor.execute(f"""
                CREATE POLICY policy_{tabela}_delete ON {tabela}
                    FOR DELETE
                    USING (usuario_crm_id = current_tenant_id())
            """)
            
            print(f"✓ {tabela}: 4 políticas criadas")
        
        conn.commit()
        cursor.close()
        print("✅ ETAPA 6 - Concluído")
        
        # Verificações finais
        verificar_rls(conn)
        verificar_policies(conn)
        
        print(f"\n{'='*60}")
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print(f"{'='*60}")
        print("\n📝 Próximos passos:")
        print("1. Reinicie a aplicação CRM")
        print("2. Faça login e teste o acesso aos dados")
        print("3. Verifique que cada tenant vê apenas seus dados")
        print("4. Teste criação, edição e exclusão de registros")
        print()
        print("💾 Backup salvo. Se houver problemas, execute:")
        print("   psql -h localhost -p 1222 -U postgres -d crm < backup_antes_rls_*.sql")
        print()
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE MIGRAÇÃO: {e}")
        print("⚠️  O banco pode estar em estado inconsistente")
        print("💾 Restaure o backup se necessário")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
