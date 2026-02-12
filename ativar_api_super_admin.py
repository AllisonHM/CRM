"""
Script para ativar a API do WhatsApp no usuário Super Administrador
Execute este script para configurar as credenciais da Z-API no super admin
"""

import os
from database_rls import db, init_db
from models import UsuarioCRM
from flask import Flask

# Configurar app
app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "instance", "crm.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar banco
init_db(app)

def ativar_api_whatsapp():
    with app.app_context():
        # Buscar super admin
        super_admin = UsuarioCRM.query.filter_by(tipo_usuario='super_admin').first()
        
        if not super_admin:
            print(" Super Admin não encontrado! Criando...")
            
            # Criar super admin
            super_admin = UsuarioCRM(
                nome="Administrador",
                email="admin@crm.com",
                tipo_usuario="super_admin",
                ativo=True
            )
            super_admin.set_password("admin123")
            db.session.add(super_admin)
            db.session.commit()
            
            print(f"✅ Super Admin criado com sucesso!")
            print(f"   Email: admin@crm.com")
            print(f"   Senha: admin123 (altere após o primeiro login!)")
            print()
        
        print(f"\n✅ Super Admin: {super_admin.nome} ({super_admin.email})")
        print("\n" + "="*60)
        print("CONFIGURAÇÃO DA API Z-API (WhatsApp)")
        print("="*60)
        
        # Solicitar credenciais
        print("\n📝 Digite as credenciais da sua API Z-API:")
        print("(Deixe em branco para manter os valores atuais)\n")
        
        api_instance = input(f"Instance ID [{super_admin.api_instance or 'não configurado'}]: ").strip()
        api_token = input(f"API Token [{super_admin.api_token or 'não configurado'}]: ").strip()
        numero_whatsapp = input(f"Número WhatsApp [{super_admin.numero_whatsapp or 'não configurado'}]: ").strip()
        
        # Atualizar apenas se fornecido
        atualizado = False
        if api_instance:
            super_admin.api_instance = api_instance
            print(f"✓ Instance ID atualizado")
            atualizado = True
        
        if api_token:
            super_admin.api_token = api_token
            print(f"✓ API Token atualizado")
            atualizado = True
        
        if numero_whatsapp:
            super_admin.numero_whatsapp = numero_whatsapp
            print(f"✓ Número WhatsApp atualizado")
            atualizado = True
        
        if not atualizado:
            print("\n⚠️ Nenhum valor foi atualizado (todos os campos ficaram em branco)")
        
        # Salvar no banco
        db.session.commit()
        
        print("\n" + "="*60)
        print("✅ CONFIGURAÇÃO SALVA COM SUCESSO!")
        print("="*60)
        print(f"\n📊 Status da API:")
        print(f"  • Instance ID: {super_admin.api_instance or 'não configurado'}")
        print(f"  • Token: {'*' * 20 if super_admin.api_token else 'não configurado'}")
        print(f"  • Número WhatsApp: {super_admin.numero_whatsapp or 'não configurado'}")
        print(f"  • API Configurada: {'✅ SIM' if super_admin.tem_api_configurada() else '❌ NÃO'}")
        print("\n")

if __name__ == '__main__':
    try:
        ativar_api_whatsapp()
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()
