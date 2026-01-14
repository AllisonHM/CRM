"""
Script para popular dados de teste com múltiplos tenants
Execute este script para criar dados que permitam testar o isolamento RLS
"""
import psycopg2
from datetime import datetime, timedelta
import random

# Configurações do banco
DB_CONFIG = {
    'host': 'localhost',
    'port': 1222,
    'database': 'crm',
    'user': 'postgres',
    'password': 'Amovoce123@'
}

def conectar():
    """Conecta ao banco de dados"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        return None

def criar_usuarios_teste(conn):
    """Cria usuários CRM de teste (3 tenants)"""
    print("\n" + "="*60)
    print("👥 Criando Usuários de Teste")
    print("="*60)
    
    cursor = conn.cursor()
    usuarios = []
    
    for i in range(1, 4):
        nome = f"Tenant {i}"
        email = f"tenant{i}@teste.com"
        senha_hash = "scrypt:32768:8:1$salttest$hashedpassword"  # Senha: teste123
        
        try:
            cursor.execute("""
                INSERT INTO usuario_crm 
                (nome, email, senha, tipo_usuario, usuario_pai_id, ativo)
                VALUES (%s, %s, %s, 'admin', NULL, true)
                ON CONFLICT (email) DO UPDATE 
                SET nome = EXCLUDED.nome
                RETURNING id
            """, (nome, email, senha_hash))
            
            usuario_id = cursor.fetchone()[0]
            usuarios.append(usuario_id)
            print(f"✅ Usuário criado: {nome} (ID: {usuario_id})")
            
        except Exception as e:
            print(f"⚠️  Erro ao criar {nome}: {e}")
            cursor.execute("SELECT id FROM usuario_crm WHERE email = %s", (email,))
            row = cursor.fetchone()
            if row:
                usuarios.append(row[0])
                print(f"ℹ️  Usuário já existe: {nome} (ID: {row[0]})")
    
    conn.commit()
    cursor.close()
    return usuarios

def criar_clientes_teste(conn, usuarios):
    """Cria clientes para cada tenant"""
    print("\n" + "="*60)
    print("👤 Criando Clientes de Teste")
    print("="*60)
    
    cursor = conn.cursor()
    
    nomes_pf = [
        "João Silva", "Maria Santos", "Pedro Oliveira", "Ana Costa",
        "Carlos Souza", "Juliana Lima", "Roberto Alves", "Fernanda Rocha"
    ]
    
    nomes_pj = [
        "Tech Solutions LTDA", "Comercial ABC", "Indústria XYZ",
        "Serviços Delta", "Construtora Alfa"
    ]
    
    for tenant_id in usuarios:
        print(f"\nTenant {tenant_id}:")
        
        # Clientes PF
        for i in range(5):
            nome = random.choice(nomes_pf)
            telefone = f"479{random.randint(10000000, 99999999)}"
            
            try:
                cursor.execute("""
                    INSERT INTO cliente 
                    (nome, telefone, tipo_pessoa, usuario_crm_id, data_cadastro)
                    VALUES (%s, %s, 'pf', %s, NOW())
                    RETURNING id
                """, (f"{nome} #{i+1}", telefone, tenant_id))
                
                cliente_id = cursor.fetchone()[0]
                print(f"  ✓ Cliente PF: {nome} #{i+1} (ID: {cliente_id})")
                
            except Exception as e:
                print(f"  ✗ Erro ao criar cliente: {e}")
        
        # Clientes PJ
        for i in range(3):
            nome = random.choice(nomes_pj)
            telefone = f"479{random.randint(10000000, 99999999)}"
            
            try:
                cursor.execute("""
                    INSERT INTO cliente 
                    (nome, telefone, tipo_pessoa, usuario_crm_id, data_cadastro)
                    VALUES (%s, %s, 'pj', %s, NOW())
                    RETURNING id
                """, (f"{nome} #{i+1}", telefone, tenant_id))
                
                cliente_id = cursor.fetchone()[0]
                print(f"  ✓ Cliente PJ: {nome} #{i+1} (ID: {cliente_id})")
                
            except Exception as e:
                print(f"  ✗ Erro ao criar cliente: {e}")
    
    conn.commit()
    cursor.close()

def criar_mesas_teste(conn, usuarios):
    """Cria mesas de negócio para cada tenant"""
    print("\n" + "="*60)
    print("💼 Criando Mesas de Negócio")
    print("="*60)
    
    cursor = conn.cursor()
    
    estagios = ['lead', 'contato_feito', 'reuniao_agendada', 'proposta', 'negociacao', 'fechado_ganho']
    
    for tenant_id in usuarios:
        print(f"\nTenant {tenant_id}:")
        
        # Pega clientes deste tenant
        cursor.execute("""
            SELECT id, nome FROM cliente 
            WHERE usuario_crm_id = %s 
            LIMIT 5
        """, (tenant_id,))
        
        clientes = cursor.fetchall()
        
        for cliente_id, cliente_nome in clientes:
            estagio = random.choice(estagios)
            valor = random.randint(1000, 50000)
            
            try:
                cursor.execute("""
                    INSERT INTO mesa_negocio 
                    (cliente_id, valor, estagio, data_criacao, usuario_crm_id)
                    VALUES (%s, %s, %s, NOW(), %s)
                    RETURNING id
                """, (cliente_id, valor, estagio, tenant_id))
                
                mesa_id = cursor.fetchone()[0]
                print(f"  ✓ Mesa: {cliente_nome} - R$ {valor} ({estagio})")
                
            except Exception as e:
                print(f"  ✗ Erro ao criar mesa: {e}")
    
    conn.commit()
    cursor.close()

def criar_ocorrencias_teste(conn, usuarios):
    """Cria ocorrências para cada tenant"""
    print("\n" + "="*60)
    print("📝 Criando Ocorrências")
    print("="*60)
    
    cursor = conn.cursor()
    
    tipos = ['ligacao', 'email', 'whatsapp', 'reuniao', 'proposta']
    
    for tenant_id in usuarios:
        print(f"\nTenant {tenant_id}:")
        
        # Pega clientes deste tenant
        cursor.execute("""
            SELECT id, nome FROM cliente 
            WHERE usuario_crm_id = %s 
            LIMIT 5
        """, (tenant_id,))
        
        clientes = cursor.fetchall()
        
        for cliente_id, cliente_nome in clientes:
            tipo = random.choice(tipos)
            
            try:
                cursor.execute("""
                    INSERT INTO ocorrencia 
                    (cliente_id, tipo, descricao, data, usuario_crm_id)
                    VALUES (%s, %s, %s, NOW(), %s)
                    RETURNING id
                """, (cliente_id, tipo, f"Ocorrência de teste - {tipo}", tenant_id))
                
                ocorrencia_id = cursor.fetchone()[0]
                print(f"  ✓ Ocorrência: {cliente_nome} - {tipo}")
                
            except Exception as e:
                print(f"  ✗ Erro ao criar ocorrência: {e}")
    
    conn.commit()
    cursor.close()

def mostrar_estatisticas(conn):
    """Mostra estatísticas dos dados criados"""
    print("\n" + "="*60)
    print("📊 Estatísticas dos Dados")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Clientes por tenant
    cursor.execute("""
        SELECT 
            u.nome as tenant,
            COUNT(c.id) as total_clientes
        FROM usuario_crm u
        LEFT JOIN cliente c ON c.usuario_crm_id = u.id
        WHERE u.tipo_usuario = 'admin' AND u.usuario_pai_id IS NULL
        GROUP BY u.id, u.nome
        ORDER BY u.id
    """)
    
    print("\n📋 Clientes por Tenant:")
    print("-" * 40)
    for tenant, total in cursor.fetchall():
        print(f"  {tenant}: {total} clientes")
    
    # Mesas por tenant
    cursor.execute("""
        SELECT 
            u.nome as tenant,
            COUNT(m.id) as total_mesas
        FROM usuario_crm u
        LEFT JOIN mesa_negocio m ON m.usuario_crm_id = u.id
        WHERE u.tipo_usuario = 'admin' AND u.usuario_pai_id IS NULL
        GROUP BY u.id, u.nome
        ORDER BY u.id
    """)
    
    print("\n💼 Mesas de Negócio por Tenant:")
    print("-" * 40)
    for tenant, total in cursor.fetchall():
        print(f"  {tenant}: {total} mesas")
    
    # Ocorrências por tenant
    cursor.execute("""
        SELECT 
            u.nome as tenant,
            COUNT(o.id) as total_ocorrencias
        FROM usuario_crm u
        LEFT JOIN ocorrencia o ON o.usuario_crm_id = u.id
        WHERE u.tipo_usuario = 'admin' AND u.usuario_pai_id IS NULL
        GROUP BY u.id, u.nome
        ORDER BY u.id
    """)
    
    print("\n📝 Ocorrências por Tenant:")
    print("-" * 40)
    for tenant, total in cursor.fetchall():
        print(f"  {tenant}: {total} ocorrências")
    
    cursor.close()

def main():
    print("="*60)
    print("🎲 POPULAR DADOS DE TESTE MULTI-TENANT")
    print("="*60)
    print()
    print("Este script vai criar:")
    print("- 3 usuários de teste (Tenant 1, 2 e 3)")
    print("- 8 clientes por tenant (5 PF + 3 PJ)")
    print("- 5 mesas de negócio por tenant")
    print("- 5 ocorrências por tenant")
    print()
    print("📧 Credenciais de login:")
    print("   Email: tenant1@teste.com, tenant2@teste.com, tenant3@teste.com")
    print("   Senha: teste123")
    print()
    
    resposta = input("Deseja continuar? (s/n): ").lower()
    if resposta != 's':
        print("❌ Operação cancelada")
        return
    
    conn = conectar()
    if not conn:
        return
    
    try:
        # Criar estrutura de dados
        usuarios = criar_usuarios_teste(conn)
        
        if len(usuarios) < 3:
            print(f"\n⚠️  Aviso: Apenas {len(usuarios)} usuários criados")
        
        criar_clientes_teste(conn, usuarios)
        criar_mesas_teste(conn, usuarios)
        criar_ocorrencias_teste(conn, usuarios)
        
        # Mostrar estatísticas
        mostrar_estatisticas(conn)
        
        print("\n" + "="*60)
        print("✅ DADOS DE TESTE CRIADOS COM SUCESSO!")
        print("="*60)
        print()
        print("🎯 Próximos passos:")
        print("1. Execute: python testar_rls.py")
        print("2. Faça login com tenant1@teste.com (senha: teste123)")
        print("3. Verifique que só vê dados do Tenant 1")
        print("4. Faça login com tenant2@teste.com")
        print("5. Verifique que só vê dados do Tenant 2")
        print()
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
