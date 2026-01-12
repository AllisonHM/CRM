# executar_sql_manual.py
"""
Script para executar SQL manualmente no banco de dados PostgreSQL
e adicionar as colunas necessárias.
"""

from CRM import app
from database import db

def executar_sql_manual():
    """Executa SQL para adicionar colunas manualmente"""
    
    with app.app_context():
        try:
            # Ler o arquivo SQL
            with open('adicionar_colunas_manual.sql', 'r', encoding='utf-8') as f:
                sql_commands = f.read()
            
            # Separar comandos individuais
            commands = [cmd.strip() for cmd in sql_commands.split(';') if cmd.strip() and not cmd.strip().startswith('--')]
            
            print("=" * 60)
            print("EXECUTANDO SQL PARA ADICIONAR COLUNAS")
            print("=" * 60)
            
            for i, command in enumerate(commands, 1):
                if command and not command.startswith('SELECT'):
                    try:
                        db.session.execute(db.text(command))
                        db.session.commit()
                        print(f"✅ Comando {i} executado com sucesso")
                    except Exception as e:
                        print(f"⚠️  Comando {i}: {str(e)}")
                        db.session.rollback()
            
            # Verificar se as colunas foram criadas
            print("\n" + "=" * 60)
            print("VERIFICANDO COLUNAS CRIADAS")
            print("=" * 60)
            
            result = db.session.execute(db.text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'cliente' 
                AND column_name IN ('usuario_crm_id', 'data_ultimo_nps_envio')
            """))
            
            colunas = result.fetchall()
            if colunas:
                print("✅ Colunas encontradas na tabela cliente:")
                for col in colunas:
                    print(f"   - {col[0]}: {col[1]}")
            else:
                print("❌ Colunas não encontradas!")
            
            # Verificar tabela usuario_crm
            result2 = db.session.execute(db.text("""
                SELECT COUNT(*) FROM usuario_crm
            """))
            count = result2.fetchone()[0]
            print(f"\n✅ Tabela usuario_crm possui {count} registro(s)")
            
            print("\n" + "=" * 60)
            print("PROCESSO CONCLUÍDO!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ ERRO: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    executar_sql_manual()
