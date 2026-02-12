# -*- coding: utf-8 -*-
"""
Script para corrigir constraint usando SQLAlchemy
"""
from CRM import app, db
from sqlalchemy import text

print("=" * 80)
print("CORRECAO DE CONSTRAINT - TABELA PRODUTO")
print("=" * 80)

with app.app_context():
    try:
        print("\nVerificando constraints existentes...")
        result = db.session.execute(text("""
            SELECT conname, contype 
            FROM pg_constraint 
            WHERE conrelid = 'produto'::regclass
            ORDER BY conname
        """))
        
        constraints = result.fetchall()
        print(f"\nConstraints encontradas: {len(constraints)}")
        for c in constraints:
            tipo_map = {'p': 'PRIMARY KEY', 'u': 'UNIQUE', 'f': 'FOREIGN KEY', 'c': 'CHECK'}
            print(f"  - {c[0]}: {tipo_map.get(c[1], c[1])}")
        
        # Remove constraint antiga
        print("\nRemovendo constraint antiga 'produto_nome_key'...")
        db.session.execute(text("ALTER TABLE produto DROP CONSTRAINT IF EXISTS produto_nome_key CASCADE"))
        db.session.commit()
        print("Constraint antiga removida!")
        
        # Verifica se já existe a nova constraint
        result = db.session.execute(text("""
            SELECT 1 FROM pg_constraint 
            WHERE conname IN ('uq_produto_usuario_nome', 'produto_usuario_crm_id_nome_key')
            AND conrelid = 'produto'::regclass
        """))
        
        tem_constraint_nova = result.fetchone() is not None
        
        if not tem_constraint_nova:
            print("\nCriando nova constraint UNIQUE (usuario_crm_id, nome)...")
            db.session.execute(text("""
                ALTER TABLE produto 
                ADD CONSTRAINT uq_produto_usuario_nome 
                UNIQUE (usuario_crm_id, nome)
            """))
            db.session.commit()
            print("Nova constraint criada!")
        else:
            print("\nNova constraint ja existe!")
        
        # Verifica resultado final
        print("\nConstraints finais na tabela produto:")
        result = db.session.execute(text("""
            SELECT conname, contype 
            FROM pg_constraint 
            WHERE conrelid = 'produto'::regclass
            ORDER BY conname
        """))
        
        constraints_final = result.fetchall()
        for c in constraints_final:
            tipo_map = {'p': 'PRIMARY KEY', 'u': 'UNIQUE', 'f': 'FOREIGN KEY', 'c': 'CHECK'}
            print(f"  - {c[0]}: {tipo_map.get(c[1], c[1])}")
        
        print("\n" + "=" * 80)
        print("MIGRACAO CONCLUIDA COM SUCESSO!")
        print("=" * 80)
        print("\nAgora cada usuario pode ter produtos com o mesmo nome!")
        
    except Exception as e:
        print(f"\nErro: {e}")
        db.session.rollback()
        import traceback
        traceback.print_exc()
