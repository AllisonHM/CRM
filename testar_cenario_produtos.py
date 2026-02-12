"""
Script para criar usuários de teste e simular o problema
"""
from CRM import app, db
from models import UsuarioCRM, Produto
from werkzeug.security import generate_password_hash

with app.app_context():
    print("🔧 Preparando ambiente de teste...\n")
    
    # Verifica usuário super admin
    super_admin = UsuarioCRM.query.filter_by(tipo_usuario='super_admin').first()
    if not super_admin:
        print("❌ Super admin não encontrado!")
        exit(1)
    
    print(f"✅ Super Admin: {super_admin.nome} (ID: {super_admin.id})\n")
    
    # Cria um usuário admin (cliente)
    admin_cliente = UsuarioCRM.query.filter_by(email='cliente1@teste.com').first()
    if not admin_cliente:
        admin_cliente = UsuarioCRM(
            nome='Cliente Teste 1',
            email='cliente1@teste.com',
            senha_hash=generate_password_hash('senha123'),
            tipo_usuario='admin',
            usuario_pai_id=None
        )
        db.session.add(admin_cliente)
        db.session.commit()
        print(f"✅ Criado Admin Cliente: {admin_cliente.nome} (ID: {admin_cliente.id})")
    else:
        print(f"✅ Admin Cliente já existe: {admin_cliente.nome} (ID: {admin_cliente.id})")
    
    # Cria um colaborador do cliente
    colaborador = UsuarioCRM.query.filter_by(email='colaborador1@teste.com').first()
    if not colaborador:
        colaborador = UsuarioCRM(
            nome='Colaborador Teste 1',
            email='colaborador1@teste.com',
            senha_hash=generate_password_hash('senha123'),
            tipo_usuario='colaborador',
            usuario_pai_id=admin_cliente.id
        )
        db.session.add(colaborador)
        db.session.commit()
        print(f"✅ Criado Colaborador: {colaborador.nome} (ID: {colaborador.id}, Pai: {colaborador.usuario_pai_id})")
    else:
        print(f"✅ Colaborador já existe: {colaborador.nome} (ID: {colaborador.id}, Pai: {colaborador.usuario_pai_id})")
    
    print("\n" + "="*70)
    print("🧪 TESTANDO CADASTRO DE PRODUTOS")
    print("="*70 + "\n")
    
    # Teste 1: Super admin cria produto "Computador"
    produto_nome = "Computador"
    print(f"📝 Teste 1: Super Admin criando produto '{produto_nome}'")
    
    p1 = Produto.query.filter_by(
        usuario_crm_id=super_admin.id,
        nome=produto_nome
    ).first()
    
    if not p1:
        p1 = Produto(
            usuario_crm_id=super_admin.id,
            nome=produto_nome,
            descricao="Notebook Dell",
            quantidade=10
        )
        db.session.add(p1)
        db.session.commit()
        print(f"   ✅ Produto criado (ID: {p1.id})")
    else:
        print(f"   ℹ️  Produto já existe (ID: {p1.id})")
    
    # Teste 2: Cliente admin tenta criar produto com mesmo nome
    print(f"\n📝 Teste 2: Cliente Admin criando produto '{produto_nome}' (mesmo nome)")
    
    p2 = Produto.query.filter_by(
        usuario_crm_id=admin_cliente.id,
        nome=produto_nome
    ).first()
    
    if not p2:
        try:
            p2 = Produto(
                usuario_crm_id=admin_cliente.id,
                nome=produto_nome,
                descricao="Desktop HP",
                quantidade=5
            )
            db.session.add(p2)
            db.session.commit()
            print(f"   ✅ Produto criado com SUCESSO! (ID: {p2.id})")
            print(f"   ✅ FUNCIONOU! Usuários diferentes podem ter produtos com mesmo nome!")
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ ERRO: {str(e)}")
    else:
        print(f"   ℹ️  Produto já existe (ID: {p2.id})")
    
    # Teste 3: Colaborador tenta criar produto
    print(f"\n📝 Teste 3: Colaborador criando produto 'Mouse'")
    
    # O colaborador deve usar o ID do pai (admin_cliente)
    principal_id = colaborador.usuario_pai_id if colaborador.usuario_pai_id else colaborador.id
    
    p3 = Produto.query.filter_by(
        usuario_crm_id=principal_id,
        nome="Mouse"
    ).first()
    
    if not p3:
        try:
            p3 = Produto(
                usuario_crm_id=principal_id,
                nome="Mouse",
                descricao="Mouse sem fio",
                quantidade=20
            )
            db.session.add(p3)
            db.session.commit()
            print(f"   ✅ Produto criado (ID: {p3.id}, Dono: {principal_id})")
        except Exception as e:
            db.session.rollback()
            print(f"   ❌ ERRO: {str(e)}")
    else:
        print(f"   ℹ️  Produto já existe (ID: {p3.id})")
    
    # Lista todos os produtos
    print("\n" + "="*70)
    print("📦 PRODUTOS NO BANCO:")
    print("="*70)
    
    todos_produtos = Produto.query.all()
    for p in todos_produtos:
        usuario = UsuarioCRM.query.get(p.usuario_crm_id)
        print(f"   • ID {p.id}: '{p.nome}' - Dono: {usuario.nome if usuario else 'N/A'} (ID: {p.usuario_crm_id})")
    
    print("\n✅ Teste concluído!")
