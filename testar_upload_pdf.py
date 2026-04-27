"""
Script de teste para upload de PDF na tela de canais
"""
import os
import sys

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

from models import UsuarioCRM, db
from CRM import app

def testar_credenciais_zapi():
    """Verifica se as credenciais Z-API estão configuradas"""
    print("\n" + "="*60)
    print("🔍 TESTE DE CREDENCIAIS Z-API")
    print("="*60)
    
    with app.app_context():
        usuarios = UsuarioCRM.query.all()
        
        print(f"\n📋 Total de usuários: {len(usuarios)}")
        
        for usuario in usuarios:
            print(f"\n👤 Usuário: {usuario.nome} (ID: {usuario.id})")
            print(f"   Email: {usuario.email}")
            
            if usuario.api_instance and usuario.api_token:
                print(f"   ✅ API Instance: {usuario.api_instance[:15]}...")
                print(f"   ✅ API Token: {usuario.api_token[:15]}...")
                print(f"   ✅ API Configurada: SIM")
            else:
                print(f"   ❌ API Instance: {'NÃO CONFIGURADO' if not usuario.api_instance else usuario.api_instance}")
                print(f"   ❌ API Token: {'NÃO CONFIGURADO' if not usuario.api_token else usuario.api_token}")
                print(f"   ❌ API Configurada: NÃO")
                print(f"\n   ⚠️  Para configurar, acesse:")
                print(f"       /parametrizacoes → Preencha 'Instance ID Z-API' e 'Token Z-API'")
    
    print("\n" + "="*60)
    print("💡 INSTRUÇÕES PARA TESTAR O UPLOAD DE PDF:")
    print("="*60)
    print("1. Inicie o servidor: python CRM.py")
    print("2. Acesse a tela de Canais")
    print("3. Clique no ícone de anexo (📎)")
    print("4. Selecione um arquivo PDF")
    print("5. Clique em 'Enviar'")
    print("6. Verifique os logs no terminal do servidor")
    print("7. Abra o Console do navegador (F12) e veja os logs JavaScript")
    print("\n📌 O que verificar nos logs:")
    print("   - Se o arquivo foi recebido pelo servidor")
    print("   - Se foi convertido para base64")
    print("   - Se foi enviado para a Z-API")
    print("   - O status da resposta da Z-API")
    print("="*60 + "\n")

if __name__ == "__main__":
    testar_credenciais_zapi()
