"""
Script para adicionar campos de integração Meta Graph API na tabela parametrizacao
"""
import psycopg2


def get_db_connection():
    """Obtém conexão com o banco de dados"""
    return psycopg2.connect(
        database='crm',
        user='postgres',
        password='Amovoce123@',
        host='localhost',
        port=1222
    )


def add_meta_columns_parametrizacao():
    """Adiciona colunas de integração Meta Graph API"""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        print("=" * 70)
        print("ADICIONANDO COLUNAS META GRAPH API EM PARAMETRIZACAO")
        print("=" * 70 + "\n")

        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'parametrizacao'
            AND column_name IN (
                'meta_graph_access_token',
                'meta_graph_verify_token',
                'meta_graph_app_id',
                'meta_graph_phone_number_id'
            );
        """)
        existing_columns = {row[0] for row in cur.fetchall()}

        colunas = [
            ('meta_graph_access_token', 'TEXT'),
            ('meta_graph_verify_token', 'VARCHAR(255)'),
            ('meta_graph_app_id', 'VARCHAR(120)'),
            ('meta_graph_phone_number_id', 'VARCHAR(120)')
        ]

        for nome_coluna, tipo_sql in colunas:
            if nome_coluna in existing_columns:
                print(f"⚠️  Coluna '{nome_coluna}' já existe, pulando...")
                continue

            print(f"Adicionando coluna '{nome_coluna}'...")
            cur.execute(f"""
                ALTER TABLE parametrizacao
                ADD COLUMN {nome_coluna} {tipo_sql} NULL;
            """)
            print(f"✅ Coluna '{nome_coluna}' adicionada!")

        conn.commit()
        print("\n" + "=" * 70)
        print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 70)

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Erro ao adicionar colunas: {e}")
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == '__main__':
    add_meta_columns_parametrizacao()
