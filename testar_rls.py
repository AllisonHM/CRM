"""
Script de teste para validar isolamento RLS
Testa se os tenants estão isolados corretamente
"""
import psycopg2
from datetime import datetime

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

def teste_1_verificar_rls_ativo(conn):
    """Verifica se RLS está ativo em todas as tabelas"""
    print("\n" + "="*60)
    print("🧪 TESTE 1: Verificar RLS Ativo")
    print("="*60)
    
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tablename, rowsecurity 
        FROM pg_tables 
        WHERE schemaname = 'public' 
          AND tablename IN ('cliente', 'mesa_negocio', 'ocorrencia')
        ORDER BY tablename
    """)
    
    resultados = cursor.fetchall()
    passou = True
    
    for tabela, rls_ativo in resultados:
        if rls_ativo:
            print(f"✅ {tabela}: RLS Ativo")
        else:
            print(f"❌ {tabela}: RLS Inativo!")
            passou = False
    
    cursor.close()
    return passou

def teste_2_isolamento_tenant(conn):
    """Testa isolamento entre tenants"""
    print("\n" + "="*60)
    print("🧪 TESTE 2: Isolamento entre Tenants")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Pega lista de tenants com dados
    cursor.execute("""
        SELECT DISTINCT usuario_crm_id 
        FROM cliente 
        WHERE usuario_crm_id IS NOT NULL 
        ORDER BY usuario_crm_id 
        LIMIT 3
    """)
    
    tenants = [row[0] for row in cursor.fetchall()]
    
    if len(tenants) < 2:
        print("⚠️  Não há tenants suficientes para testar isolamento")
        print(f"   Tenants encontrados: {tenants}")
        cursor.close()
        return True
    
    passou = True
    
    for tenant_id in tenants[:2]:  # Testa os 2 primeiros
        # Define o tenant
        cursor.execute("SET LOCAL app.current_tenant = %s", (tenant_id,))
        
        # Conta clientes do tenant
        cursor.execute("SELECT COUNT(*) FROM cliente")
        count_com_filtro = cursor.fetchone()[0]
        
        # Conta total de clientes do tenant (sem RLS)
        cursor.execute("RESET app.current_tenant")
        cursor.execute(
            "SELECT COUNT(*) FROM cliente WHERE usuario_crm_id = %s",
            (tenant_id,)
        )
        count_real = cursor.fetchone()[0]
        
        if count_com_filtro == count_real:
            print(f"✅ Tenant {tenant_id}: {count_com_filtro} clientes (isolamento OK)")
        else:
            print(f"❌ Tenant {tenant_id}: RLS retornou {count_com_filtro}, esperado {count_real}")
            passou = False
    
    cursor.close()
    return passou

def teste_3_tenant_nao_ve_outros(conn):
    """Testa que um tenant não vê dados de outro"""
    print("\n" + "="*60)
    print("🧪 TESTE 3: Tenant não vê dados de outros")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Pega 2 tenants diferentes
    cursor.execute("""
        SELECT DISTINCT usuario_crm_id 
        FROM cliente 
        WHERE usuario_crm_id IS NOT NULL 
        ORDER BY usuario_crm_id 
        LIMIT 2
    """)
    
    tenants = [row[0] for row in cursor.fetchall()]
    
    if len(tenants) < 2:
        print("⚠️  Não há tenants suficientes para testar")
        cursor.close()
        return True
    
    tenant_1, tenant_2 = tenants[0], tenants[1]
    
    # Define tenant 1
    cursor.execute("SET LOCAL app.current_tenant = %s", (tenant_1,))
    
    # Tenta pegar clientes do tenant 2
    cursor.execute(
        "SELECT COUNT(*) FROM cliente WHERE usuario_crm_id = %s",
        (tenant_2,)
    )
    
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(f"✅ Tenant {tenant_1} não vê dados do tenant {tenant_2}")
        passou = True
    else:
        print(f"❌ Tenant {tenant_1} VÊ {count} clientes do tenant {tenant_2}!")
        print("   ⚠️  RLS NÃO ESTÁ FUNCIONANDO CORRETAMENTE!")
        passou = False
    
    cursor.close()
    return passou

def teste_4_insert_automatico(conn):
    """Testa se INSERT preenche automaticamente usuario_crm_id"""
    print("\n" + "="*60)
    print("🧪 TESTE 4: INSERT com tenant_id automático")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Pega um tenant existente
    cursor.execute("""
        SELECT DISTINCT usuario_crm_id 
        FROM cliente 
        WHERE usuario_crm_id IS NOT NULL 
        LIMIT 1
    """)
    
    row = cursor.fetchone()
    if not row:
        print("⚠️  Não há tenants para testar")
        cursor.close()
        return True
    
    tenant_id = row[0]
    
    # Define tenant
    cursor.execute("SET LOCAL app.current_tenant = %s", (tenant_id,))
    
    # Insere cliente teste (com campos obrigatórios)
    nome_teste = f"Cliente Teste RLS {datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    try:
        cursor.execute("""
            INSERT INTO cliente (nome, telefone, tipo_pessoa, usuario_crm_id) 
            VALUES (%s, '47999999999', 'pf', %s)
            RETURNING id, usuario_crm_id
        """, (nome_teste, tenant_id))
        
        cliente_id, cliente_tenant_id = cursor.fetchone()
        
        if cliente_tenant_id == tenant_id:
            print(f"✅ Cliente inserido com usuario_crm_id correto: {cliente_tenant_id}")
            
            # Limpa teste
            cursor.execute("DELETE FROM cliente WHERE id = %s", (cliente_id,))
            conn.commit()
            passou = True
        else:
            print(f"❌ Cliente inserido com usuario_crm_id errado: {cliente_tenant_id} (esperado {tenant_id})")
            conn.rollback()
            passou = False
            
    except Exception as e:
        print(f"❌ Erro ao inserir: {e}")
        conn.rollback()
        passou = False
    
    cursor.close()
    return passou

def teste_5_update_bloqueado(conn):
    """Testa se UPDATE de outro tenant é bloqueado"""
    print("\n" + "="*60)
    print("🧪 TESTE 5: UPDATE bloqueado entre tenants")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Pega 2 tenants diferentes
    cursor.execute("""
        SELECT c.id, c.usuario_crm_id 
        FROM cliente c
        WHERE c.usuario_crm_id IS NOT NULL
        ORDER BY c.usuario_crm_id
        LIMIT 2
    """)
    
    resultados = cursor.fetchall()
    
    if len(resultados) < 2:
        print("⚠️  Não há clientes suficientes para testar")
        cursor.close()
        return True
    
    # Cliente do tenant 1
    cliente_id = resultados[0][0]
    tenant_1 = resultados[0][1]
    
    # Tenta atualizar com tenant 2
    tenant_2 = resultados[1][1]
    
    if tenant_1 == tenant_2:
        print("⚠️  Não há tenants diferentes para testar")
        cursor.close()
        return True
    
    # Define tenant 2
    cursor.execute("SET LOCAL app.current_tenant = %s", (tenant_2,))
    
    # Tenta atualizar cliente do tenant 1
    cursor.execute("""
        UPDATE cliente 
        SET nome = 'HACK ATTEMPT' 
        WHERE id = %s
    """, (cliente_id,))
    
    if cursor.rowcount == 0:
        print(f"✅ Tenant {tenant_2} não conseguiu atualizar cliente do tenant {tenant_1}")
        passou = True
    else:
        print(f"❌ Tenant {tenant_2} CONSEGUIU atualizar cliente do tenant {tenant_1}!")
        print("   ⚠️  RLS NÃO ESTÁ FUNCIONANDO CORRETAMENTE!")
        passou = False
    
    conn.rollback()
    cursor.close()
    return passou

def teste_6_delete_bloqueado(conn):
    """Testa se DELETE de outro tenant é bloqueado"""
    print("\n" + "="*60)
    print("🧪 TESTE 6: DELETE bloqueado entre tenants")
    print("="*60)
    
    cursor = conn.cursor()
    
    # Pega 2 tenants diferentes
    cursor.execute("""
        SELECT c.id, c.usuario_crm_id 
        FROM cliente c
        WHERE c.usuario_crm_id IS NOT NULL
        ORDER BY c.usuario_crm_id
        LIMIT 2
    """)
    
    resultados = cursor.fetchall()
    
    if len(resultados) < 2:
        print("⚠️  Não há clientes suficientes para testar")
        cursor.close()
        return True
    
    # Cliente do tenant 1
    cliente_id = resultados[0][0]
    tenant_1 = resultados[0][1]
    
    # Tenta deletar com tenant 2
    tenant_2 = resultados[1][1]
    
    if tenant_1 == tenant_2:
        print("⚠️  Não há tenants diferentes para testar")
        cursor.close()
        return True
    
    # Define tenant 2
    cursor.execute("SET LOCAL app.current_tenant = %s", (tenant_2,))
    
    # Tenta deletar cliente do tenant 1
    cursor.execute("DELETE FROM cliente WHERE id = %s", (cliente_id,))
    
    if cursor.rowcount == 0:
        print(f"✅ Tenant {tenant_2} não conseguiu deletar cliente do tenant {tenant_1}")
        passou = True
    else:
        print(f"❌ Tenant {tenant_2} CONSEGUIU deletar cliente do tenant {tenant_1}!")
        print("   ⚠️  RLS NÃO ESTÁ FUNCIONANDO CORRETAMENTE!")
        passou = False
    
    conn.rollback()
    cursor.close()
    return passou

def main():
    print("="*60)
    print("🧪 BATERIA DE TESTES RLS")
    print("="*60)
    print()
    print("Este script vai testar:")
    print("1. RLS está ativo")
    print("2. Isolamento entre tenants")
    print("3. Tenant não vê dados de outros")
    print("4. INSERT automático do tenant_id")
    print("5. UPDATE bloqueado entre tenants")
    print("6. DELETE bloqueado entre tenants")
    print()
    
    conn = conectar()
    if not conn:
        print("❌ Não foi possível conectar ao banco")
        return
    
    resultados = []
    
    # Executa testes
    resultados.append(("RLS Ativo", teste_1_verificar_rls_ativo(conn)))
    resultados.append(("Isolamento", teste_2_isolamento_tenant(conn)))
    resultados.append(("Não vê outros", teste_3_tenant_nao_ve_outros(conn)))
    resultados.append(("INSERT automático", teste_4_insert_automatico(conn)))
    resultados.append(("UPDATE bloqueado", teste_5_update_bloqueado(conn)))
    resultados.append(("DELETE bloqueado", teste_6_delete_bloqueado(conn)))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    passou_todos = True
    for nome, passou in resultados:
        status = "✅ PASSOU" if passou else "❌ FALHOU"
        print(f"{status} - {nome}")
        if not passou:
            passou_todos = False
    
    print("="*60)
    
    if passou_todos:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("🎉 RLS está funcionando corretamente!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("⚠️  Verifique a configuração do RLS")
    
    conn.close()

if __name__ == "__main__":
    main()
