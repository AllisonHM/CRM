# adicionar_colunas_direto.py
"""
Script para adicionar colunas diretamente no PostgreSQL na ordem correta
"""

from CRM import app
from database import db

def adicionar_colunas():
    """Adiciona colunas uma por uma na ordem correta"""
    
    with app.app_context():
        comandos = [
            # 1. Garantir que tabela usuario_crm existe
            """
            CREATE TABLE IF NOT EXISTS usuario_crm (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(200) NOT NULL,
                numero_whatsapp VARCHAR(50) NOT NULL UNIQUE,
                api_token VARCHAR(255),
                dias_quarentena_nps INTEGER DEFAULT 30,
                ativo BOOLEAN DEFAULT TRUE,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            
            # 2. Adicionar coluna usuario_crm_id na tabela cliente
            "ALTER TABLE cliente ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER",
            
            # 3. Adicionar coluna data_ultimo_nps_envio na tabela cliente
            "ALTER TABLE cliente ADD COLUMN IF NOT EXISTS data_ultimo_nps_envio TIMESTAMP",
            
            # 4. Adicionar coluna usuario_crm_id na tabela mesa_negocio
            "ALTER TABLE mesa_negocio ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER",
            
            # 5. Adicionar coluna usuario_crm_id na tabela ocorrencia
            "ALTER TABLE ocorrencia ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER",
            
            # 6. Adicionar coluna usuario_crm_id na tabela whatsapp_mensagem
            "ALTER TABLE whatsapp_mensagem ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER",
            
            # 7. Adicionar coluna usuario_crm_id na tabela produto
            "ALTER TABLE produto ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER",
            
            # 8. Adicionar coluna usuario_crm_id na tabela planner_evento
            "ALTER TABLE planner_evento ADD COLUMN IF NOT EXISTS usuario_crm_id INTEGER",
            
            # 9. Inserir usuário CRM inicial se não existir
            """
            INSERT INTO usuario_crm (nome, numero_whatsapp, dias_quarentena_nps, ativo)
            SELECT 'Minha Empresa', '4797043489', 30, TRUE
            WHERE NOT EXISTS (SELECT 1 FROM usuario_crm WHERE numero_whatsapp = '4797043489')
            """,
            
            # 10. Adicionar foreign keys (ignorar erros se já existirem)
            "ALTER TABLE cliente ADD CONSTRAINT fk_cliente_usuario_crm FOREIGN KEY (usuario_crm_id) REFERENCES usuario_crm(id)",
            "ALTER TABLE mesa_negocio ADD CONSTRAINT fk_mesa_usuario_crm FOREIGN KEY (usuario_crm_id) REFERENCES usuario_crm(id)",
            "ALTER TABLE ocorrencia ADD CONSTRAINT fk_ocorrencia_usuario_crm FOREIGN KEY (usuario_crm_id) REFERENCES usuario_crm(id)",
            "ALTER TABLE whatsapp_mensagem ADD CONSTRAINT fk_whatsapp_usuario_crm FOREIGN KEY (usuario_crm_id) REFERENCES usuario_crm(id)",
            "ALTER TABLE produto ADD CONSTRAINT fk_produto_usuario_crm FOREIGN KEY (usuario_crm_id) REFERENCES usuario_crm(id)",
            "ALTER TABLE planner_evento ADD CONSTRAINT fk_planner_usuario_crm FOREIGN KEY (usuario_crm_id) REFERENCES usuario_crm(id)",
        ]
        
        print("=" * 70)
        print("ADICIONANDO COLUNAS NO BANCO DE DADOS POSTGRESQL")
        print("=" * 70)
        
        sucesso = 0
        avisos = 0
        
        for i, comando in enumerate(comandos, 1):
            try:
                db.session.execute(db.text(comando))
                db.session.commit()
                print(f"✅ [{i:02d}/{len(comandos)}] Executado com sucesso")
                sucesso += 1
            except Exception as e:
                erro_str = str(e)
                # Ignorar erros de constraint já existe
                if 'already exists' in erro_str or 'já existe' in erro_str:
                    print(f"⚠️  [{i:02d}/{len(comandos)}] Já existe (OK)")
                    avisos += 1
                else:
                    print(f"❌ [{i:02d}/{len(comandos)}] Erro: {erro_str[:100]}")
                db.session.rollback()
        
        print("\n" + "=" * 70)
        print("VERIFICANDO RESULTADO")
        print("=" * 70)
        
        # Verificar colunas criadas
        try:
            result = db.session.execute(db.text("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name IN ('cliente', 'mesa_negocio', 'ocorrencia', 
                                    'whatsapp_mensagem', 'produto', 'planner_evento')
                AND column_name = 'usuario_crm_id'
                ORDER BY table_name
            """))
            
            colunas = result.fetchall()
            if colunas:
                print("✅ Colunas usuario_crm_id criadas:")
                for col in colunas:
                    print(f"   - {col[0]}.{col[1]} ({col[2]})")
            else:
                print("❌ Nenhuma coluna usuario_crm_id encontrada!")
            
            # Verificar data_ultimo_nps_envio
            result2 = db.session.execute(db.text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'cliente' 
                AND column_name = 'data_ultimo_nps_envio'
            """))
            
            col_nps = result2.fetchone()
            if col_nps:
                print(f"\n✅ Coluna cliente.data_ultimo_nps_envio criada ({col_nps[1]})")
            else:
                print("\n❌ Coluna data_ultimo_nps_envio não encontrada!")
            
            # Verificar usuários CRM
            result3 = db.session.execute(db.text("SELECT COUNT(*) FROM usuario_crm"))
            count = result3.fetchone()[0]
            print(f"\n✅ Tabela usuario_crm possui {count} usuário(s)")
            
        except Exception as e:
            print(f"❌ Erro ao verificar: {str(e)}")
        
        print("\n" + "=" * 70)
        print(f"RESUMO: {sucesso} sucesso(s), {avisos} aviso(s)")
        print("=" * 70)

if __name__ == '__main__':
    adicionar_colunas()
