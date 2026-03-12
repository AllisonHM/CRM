"""
Migration: Adiciona colunas ao WhatsAppMensagem e cria tabela conversa_config.

Colunas adicionadas em whatsapp_mensagem:
  - lida          BOOLEAN NOT NULL DEFAULT FALSE
  - status        VARCHAR(30)
  - tipo_midia    VARCHAR(30)
  - arquivo_url   TEXT

Nova tabela:
  - conversa_config (id, usuario_crm_id, telefone, fixada, arquivada, data_config)

Execução:
    python add_whatsapp_fields_conversaconfig.py
"""

import os
import psycopg2
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

# Lê credenciais do .env
_raw_url = os.getenv('DATABASE_URL', '')


def _parse_db_url(url: str) -> dict:
    """Converte DATABASE_URL em kwargs para psycopg2.connect."""
    # Remove dialeto SQLAlchemy se presente
    url = url.replace('postgresql+psycopg2://', 'postgresql://')
    p = urlparse(url)
    from urllib.parse import unquote
    return {
        'dbname':   p.path.lstrip('/'),
        'user':     unquote(p.username or ''),
        'password': unquote(p.password or ''),
        'host':     p.hostname,
        'port':     p.port or 5432,
    }


def get_connection():
    if not _raw_url:
        raise RuntimeError('DATABASE_URL não definida no .env')
    return psycopg2.connect(**_parse_db_url(_raw_url))


def coluna_existe(cur, tabela: str, coluna: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name   = %s
          AND column_name  = %s
        """,
        (tabela, coluna),
    )
    return cur.fetchone() is not None


def tabela_existe(cur, tabela: str) -> bool:
    cur.execute(
        """
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name   = %s
        """,
        (tabela,),
    )
    return cur.fetchone() is not None


def run():
    conn = get_connection()
    cur = conn.cursor()

    print('=' * 60)
    print('MIGRATION: whatsapp_mensagem + conversa_config')
    print('=' * 60)

    # --- 1. Colunas em whatsapp_mensagem ---
    novas_colunas = [
        ('lida',       'BOOLEAN NOT NULL DEFAULT FALSE'),
        ('status',     'VARCHAR(30)'),
        ('tipo_midia', 'VARCHAR(30)'),
        ('arquivo_url','TEXT'),
    ]

    for col, definicao in novas_colunas:
        if coluna_existe(cur, 'whatsapp_mensagem', col):
            print(f'  ⚠️  Coluna whatsapp_mensagem.{col} já existe, pulando.')
        else:
            cur.execute(
                f'ALTER TABLE whatsapp_mensagem ADD COLUMN {col} {definicao};'
            )
            print(f'  ✅ Coluna whatsapp_mensagem.{col} criada.')

    # --- 2. Tabela conversa_config ---
    if tabela_existe(cur, 'conversa_config'):
        print('  ⚠️  Tabela conversa_config já existe, pulando.')
    else:
        cur.execute(
            """
            CREATE TABLE conversa_config (
                id              SERIAL PRIMARY KEY,
                usuario_crm_id  INTEGER NOT NULL
                                REFERENCES usuario_crm(id) ON DELETE CASCADE,
                telefone        VARCHAR(50) NOT NULL,
                fixada          BOOLEAN NOT NULL DEFAULT FALSE,
                arquivada       BOOLEAN NOT NULL DEFAULT FALSE,
                data_config     TIMESTAMP DEFAULT NOW(),
                CONSTRAINT uq_conversa_config UNIQUE (usuario_crm_id, telefone)
            );
            """
        )
        print('  ✅ Tabela conversa_config criada.')

    conn.commit()
    cur.close()
    conn.close()
    print('\n✅ Migration concluída com sucesso!')


if __name__ == '__main__':
    run()
