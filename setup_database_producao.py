"""
Script para setup inicial do banco de dados em produção
Execute este script após fazer deploy na Locaweb
"""
import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente de produção
load_dotenv('.env')

print("="*60)
print("🗄️  SETUP DO BANCO DE DADOS - PRODUÇÃO")
print("="*60)
print()

# Verificar se está usando configuração de produção
database_url = os.environ.get('DATABASE_URL')
if not database_url or 'localhost' in database_url:
    print("❌ ERRO: DATABASE_URL não configurada ou aponta para localhost!")
    print("   Configure o arquivo .env com os dados da Locaweb")
    sys.exit(1)

print(f"📊 Conectando ao banco: {database_url.split('@')[1] if '@' in database_url else 'configurado'}")
print()

from database_rls import db
from CRM import app

def criar_estrutura():
    """Cria todas as tabelas no banco de produção"""
    
    with app.app_context():
        try:
            print("1️⃣  Criando estrutura do banco de dados...")
            db.create_all()
            print("   ✅ Tabelas criadas com sucesso!")
            print()
            
            print("2️⃣  Aplicando índices de performance...")
            from aplicar_indices import aplicar_indices_direto
            aplicar_indices_direto()
            print()
            
            print("3️⃣  Verificando estrutura...")
            # Contar tabelas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tabelas = inspector.get_table_names()
            print(f"   ✅ {len(tabelas)} tabelas criadas:")
            for tabela in sorted(tabelas)[:10]:  # Mostrar primeiras 10
                print(f"      - {tabela}")
            if len(tabelas) > 10:
                print(f"      ... e mais {len(tabelas) - 10} tabelas")
            print()
            
            print("="*60)
            print("✅ BANCO DE DADOS CONFIGURADO COM SUCESSO!")
            print("="*60)
            print()
            print("📝 PRÓXIMOS PASSOS:")
            print("   1. Criar usuário administrador: python criar_usuario_crm.py")
            print("   2. Reiniciar aplicação: touch tmp/restart.txt")
            print("   3. Acessar: https://seu-dominio.com.br")
            print()
            
        except Exception as e:
            print(f"❌ ERRO ao criar estrutura: {str(e)}")
            print()
            print("🔍 Possíveis causas:")
            print("   - Credenciais do banco incorretas no .env")
            print("   - Banco de dados não existe na Locaweb")
            print("   - Firewall bloqueando conexão")
            print()
            import traceback
            traceback.print_exc()
            sys.exit(1)

def aplicar_indices_direto():
    """Aplica índices diretamente"""
    indices = [
        ("idx_cliente_telefone", "CREATE INDEX IF NOT EXISTS idx_cliente_telefone ON cliente(telefone)"),
        ("idx_cliente_email", "CREATE INDEX IF NOT EXISTS idx_cliente_email ON cliente(email)"),
        ("idx_mesa_cliente_id", "CREATE INDEX IF NOT EXISTS idx_mesa_cliente_id ON mesa_negocio(cliente_id)"),
        ("idx_wpp_numero", "CREATE INDEX IF NOT EXISTS idx_wpp_numero ON whatsapp_mensagem(numero)"),
        ("idx_usuario_email", "CREATE INDEX IF NOT EXISTS idx_usuario_email ON usuario_crm(email)"),
    ]
    
    for nome, sql in indices:
        try:
            db.session.execute(db.text(sql))
            db.session.commit()
            print(f"   ✅ {nome}")
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"   ⏭️  {nome} (já existe)")
            else:
                print(f"   ⚠️  {nome}: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    criar_estrutura()
