# claim_atendimento.py
from sqlalchemy import text
from app import db

def claim_next_atendimento(empresa_id, usuario_id):
    # busca a fila mais antiga não atribuída e trava
    sql = text("""
    WITH cte AS (
      SELECT id FROM atendimento
      WHERE empresa_id = :empresa_id AND status = 'fila'
      ORDER BY created_at
      FOR UPDATE SKIP LOCKED
      LIMIT 1
    )
    UPDATE atendimento
    SET status='em_atendimento', assigned_to=:usuario_id, updated_at=now()
    FROM cte
    WHERE atendimento.id = cte.id
    RETURNING atendimento.id, atendimento.cliente_id, atendimento.mesa_id;
    """)
    res = db.session.execute(sql, {'empresa_id': empresa_id, 'usuario_id': usuario_id}).first()
    db.session.commit()
    return res  # None se vazio
