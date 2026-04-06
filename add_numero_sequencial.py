"""
Migração: adiciona coluna 'numero' em mesa_negocio e ocorrencia
e popula registros existentes com numeração sequencial por usuário.

Execute uma única vez:
    python add_numero_sequencial.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from CRM import app
from database_rls import db
from sqlalchemy import text

def run():
    with app.app_context():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # ── mesa_negocio ──────────────────────────────────────────────
            has_col = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_name='mesa_negocio' AND column_name='numero'"
            )).scalar()

            if not has_col:
                conn.execute(text("ALTER TABLE mesa_negocio ADD COLUMN numero INTEGER"))
                print("Coluna 'numero' adicionada em mesa_negocio.")
            else:
                print("Coluna 'numero' já existe em mesa_negocio.")

            # Popula registros existentes por usuario_crm_id
            usuarios_mesa = conn.execute(text(
                "SELECT DISTINCT usuario_crm_id FROM mesa_negocio "
                "WHERE numero IS NULL ORDER BY usuario_crm_id"
            )).fetchall()

            for (uid,) in usuarios_mesa:
                rows = conn.execute(text(
                    "SELECT id FROM mesa_negocio "
                    "WHERE usuario_crm_id = :uid "
                    "ORDER BY id ASC"
                ), {"uid": uid}).fetchall()
                for seq, (rid,) in enumerate(rows, start=1):
                    conn.execute(text(
                        "UPDATE mesa_negocio SET numero = :seq WHERE id = :rid"
                    ), {"seq": seq, "rid": rid})
                print(f"  mesa_negocio: usuário {uid} → {len(rows)} registros numerados.")

            # ── ocorrencia ────────────────────────────────────────────────
            has_col_oc = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.columns "
                "WHERE table_name='ocorrencia' AND column_name='numero'"
            )).scalar()

            if not has_col_oc:
                conn.execute(text("ALTER TABLE ocorrencia ADD COLUMN numero INTEGER"))
                print("Coluna 'numero' adicionada em ocorrencia.")
            else:
                print("Coluna 'numero' já existe em ocorrencia.")

            usuarios_oc = conn.execute(text(
                "SELECT DISTINCT usuario_crm_id FROM ocorrencia "
                "WHERE numero IS NULL ORDER BY usuario_crm_id"
            )).fetchall()

            for (uid,) in usuarios_oc:
                rows = conn.execute(text(
                    "SELECT id FROM ocorrencia "
                    "WHERE usuario_crm_id = :uid "
                    "ORDER BY id ASC"
                ), {"uid": uid}).fetchall()
                for seq, (rid,) in enumerate(rows, start=1):
                    conn.execute(text(
                        "UPDATE ocorrencia SET numero = :seq WHERE id = :rid"
                    ), {"seq": seq, "rid": rid})
                print(f"  ocorrencia: usuário {uid} → {len(rows)} registros numerados.")

            trans.commit()
            print("\nMigração concluída com sucesso!")

        except Exception as e:
            trans.rollback()
            print(f"\nERRO: {e}")
            raise
        finally:
            conn.close()

if __name__ == "__main__":
    run()
