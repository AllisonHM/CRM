"""
Script para verificar se existe cliente com o número das mensagens
"""
from database_rls import db, init_db
from models import Cliente
from CRM import app, normalize_phone

def verificar_clientes():
    """Verifica se existe cliente com o número das mensagens"""
    with app.app_context():
        print("\n" + "="*60)
        print("🔍 VERIFICANDO CLIENTES")
        print("="*60)
        
        numero_busca = "5547999471874"
        
        # Buscar todos os clientes
        clientes = Cliente.query.all()
        
        print(f"\n📊 Total de clientes: {len(clientes)}")
        print(f"🔍 Buscando por número: {numero_busca}")
        print(f"   Últimos 9 dígitos: {numero_busca[-9:]}")
        print(f"   Últimos 11 dígitos: {numero_busca[-11:]}")
        
        encontrados = []
        
        for cliente in clientes:
            tel_norm = normalize_phone(cliente.telefone)
            
            # Verificar várias condições
            if tel_norm == numero_busca:
                encontrados.append((cliente, "Match exato"))
            elif tel_norm[-9:] == numero_busca[-9:]:
                encontrados.append((cliente, f"Match últimos 9 dígitos (tel: {tel_norm})"))
            elif tel_norm[-11:] == numero_busca[-11:]:
                encontrados.append((cliente, f"Match últimos 11 dígitos (tel: {tel_norm})"))
        
        if encontrados:
            print(f"\n✅ {len(encontrados)} clientes encontrados:")
            for cliente, motivo in encontrados:
                print(f"   - {cliente.nome} (ID: {cliente.id}, Tel: {cliente.telefone}, Usuário: {cliente.usuario_crm_id})")
                print(f"     Motivo: {motivo}")
        else:
            print("\n⚠️ Nenhum cliente encontrado com esse número!")
            print("\n📋 Primeiros 10 clientes cadastrados:")
            for cliente in clientes[:10]:
                tel_norm = normalize_phone(cliente.telefone)
                print(f"   - {cliente.nome} (Tel: {tel_norm}, Usuário: {cliente.usuario_crm_id})")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    verificar_clientes()
