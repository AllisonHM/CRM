"""
Script para criar a tabela facebook_pages no banco de dados PostgreSQL.

Execução:
    python add_facebook_pages_table.py
"""

import psycopg2


def get_db_connection():
    """Obtém conexão com o banco de dados."""
    return psycopg2.connect(
        database="crm",
        user="postgres",
        password="Amovoce123@",
        host="localhost",
        port=1222,
    )


def criar_tabela_facebook_pages():
    """Cria a tabela facebook_pages caso ela ainda não exista."""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        print("=" * 70)
        print("CRIANDO TABELA facebook_pages")
        print("=" * 70 + "\n")

        # Verifica se a tabela já existe
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'facebook_pages';
        """)

        if cur.fetchone():
            print("⚠️  Tabela 'facebook_pages' já existe, pulando criação...")
        else:
            print("Criando tabela 'facebook_pages'...")
            cur.execute("""
                CREATE TABLE facebook_pages (
                    id                  SERIAL PRIMARY KEY,
                    usuario_crm_id      INTEGER NOT NULL
                                        REFERENCES usuario_crm(id) ON DELETE CASCADE,
                    page_id             VARCHAR(100) NOT NULL,
                    page_name           VARCHAR(255) NOT NULL,
                    page_access_token   TEXT NOT NULL,
                    instagram_id        VARCHAR(100) NULL,
                    created_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    updated_at          TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),

                    -- Garante unicidade por par (usuário, página)
                    CONSTRAINT uq_fb_page_usuario UNIQUE (usuario_crm_id, page_id)
                );
            """)
            print("✅ Tabela 'facebook_pages' criada!")

        # Índice para acelerar consultas por usuario_crm_id
        cur.execute("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'facebook_pages'
            AND indexname = 'ix_facebook_pages_usuario_crm_id';
        """)
        if not cur.fetchone():
            print("Criando índice ix_facebook_pages_usuario_crm_id...")
            cur.execute("""
                CREATE INDEX ix_facebook_pages_usuario_crm_id
                ON facebook_pages(usuario_crm_id);
            """)
            print("✅ Índice criado!")
        else:
            print("⚠️  Índice já existe, pulando...")

        conn.commit()
        print("\n" + "=" * 70)
        print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 70)

    except Exception as exc:
        conn.rollback()
        print(f"\n❌ Erro ao criar tabela: {exc}")
        raise

    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    criar_tabela_facebook_pages()
