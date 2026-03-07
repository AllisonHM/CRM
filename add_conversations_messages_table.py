"""
Script de migração: cria as tabelas conversations e messages no PostgreSQL.

Execução:
    python add_conversations_messages_table.py
"""

import psycopg2


def get_db_connection():
    return psycopg2.connect(
        database="crm",
        user="postgres",
        password="Amovoce123@",
        host="localhost",
        port=1222,
    )


def criar_tabelas():
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        print("=" * 70)
        print("CRIANDO TABELAS conversations E messages")
        print("=" * 70 + "\n")

        # ── conversations ────────────────────────────────────────────────
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'conversations';
        """)
        if cur.fetchone():
            print("⚠️  Tabela 'conversations' já existe, pulando criação...")
        else:
            print("Criando tabela 'conversations'...")
            cur.execute("""
                CREATE TABLE conversations (
                    id               SERIAL PRIMARY KEY,
                    usuario_crm_id   INTEGER NOT NULL
                                     REFERENCES usuario_crm(id) ON DELETE CASCADE,
                    page_id          VARCHAR(100) NOT NULL,
                    contact_id       VARCHAR(100) NOT NULL,
                    platform         VARCHAR(20) NOT NULL DEFAULT 'facebook',
                    created_at       TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                    last_message_at  TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE INDEX ix_conv_usuario_last
                ON conversations(usuario_crm_id, last_message_at DESC);
            """)
            print("✅ Tabela 'conversations' criada!")

        # ── messages ─────────────────────────────────────────────────────
        cur.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' AND table_name = 'messages';
        """)
        if cur.fetchone():
            print("⚠️  Tabela 'messages' já existe, pulando criação...")
        else:
            print("Criando tabela 'messages'...")
            cur.execute("""
                CREATE TABLE messages (
                    id                   SERIAL PRIMARY KEY,
                    conversation_id      INTEGER NOT NULL
                                         REFERENCES conversations(id) ON DELETE CASCADE,
                    sender_type          VARCHAR(20) NOT NULL DEFAULT 'customer',
                    message_text         TEXT NOT NULL,
                    platform_message_id  VARCHAR(255) NULL UNIQUE,
                    created_at           TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
                );
            """)
            cur.execute("""
                CREATE INDEX ix_msg_conv_created
                ON messages(conversation_id, created_at ASC);
            """)
            print("✅ Tabela 'messages' criada!")

        conn.commit()
        print("\n" + "=" * 70)
        print("MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 70)

    except Exception as exc:
        conn.rollback()
        print(f"\n❌ Erro ao criar tabelas: {exc}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    criar_tabelas()
