# criar_usuario_crm.py
"""
Script para criar o primeiro usuário CRM (instância).
Execute este script após rodar as migrações.
"""

from CRM import app
from database_rls import db
from models import UsuarioCRM

def criar_usuario_crm_inicial():
    """Cria o primeiro usuário/instância do CRM"""
    
    with app.app_context():
        # Verifica se já existe algum usuário
        usuario_existente = UsuarioCRM.query.first()
        
        if usuario_existente:
            print(f"✅ Já existe um usuário CRM cadastrado: {usuario_existente.nome}")
            print(f"   WhatsApp: {usuario_existente.numero_whatsapp}")
            print(f"   Quarentena NPS: {usuario_existente.dias_quarentena_nps} dias")
            return
        
        # Solicita dados do usuário
        print("=" * 50)
        print("CRIAR PRIMEIRO USUÁRIO DO CRM")
        print("=" * 50)
        
        nome = input("Nome da instância/empresa: ").strip()
        numero_whatsapp = input("Número do WhatsApp (com DDD): ").strip()
        
        dias_quarentena = input("Dias mínimos entre envios de NPS (padrão 30): ").strip()
        dias_quarentena = int(dias_quarentena) if dias_quarentena else 30
        
        api_token = input("Token da API WhatsApp (opcional, pressione Enter para pular): ").strip()
        api_token = api_token if api_token else None
        
        # Cria o usuário
        novo_usuario = UsuarioCRM(
            nome=nome,
            numero_whatsapp=numero_whatsapp,
            dias_quarentena_nps=dias_quarentena,
            api_token=api_token,
            ativo=True
        )
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        print("\n✅ Usuário CRM criado com sucesso!")
        print(f"   ID: {novo_usuario.id}")
        print(f"   Nome: {novo_usuario.nome}")
        print(f"   WhatsApp: {novo_usuario.numero_whatsapp}")
        print(f"   Quarentena NPS: {novo_usuario.dias_quarentena_nps} dias")
        print("\n⚠️  IMPORTANTE: Anote o ID acima. Você precisará dele para configurar o sistema.")
        
        # Opção de vincular clientes existentes
        print("\n" + "=" * 50)
        vincular = input("Deseja vincular todos os clientes existentes a este usuário? (s/n): ").strip().lower()
        
        if vincular == 's':
            from models import Cliente, MesaNegocio, Ocorrencia, WhatsAppMensagem, Produto, PlannerEvento
            
            # Atualiza clientes
            clientes_atualizados = Cliente.query.update({Cliente.usuario_crm_id: novo_usuario.id})
            # Atualiza mesas
            mesas_atualizadas = MesaNegocio.query.update({MesaNegocio.usuario_crm_id: novo_usuario.id})
            # Atualiza ocorrências
            ocorrencias_atualizadas = Ocorrencia.query.update({Ocorrencia.usuario_crm_id: novo_usuario.id})
            # Atualiza mensagens
            mensagens_atualizadas = WhatsAppMensagem.query.update({WhatsAppMensagem.usuario_crm_id: novo_usuario.id})
            # Atualiza produtos
            produtos_atualizados = Produto.query.update({Produto.usuario_crm_id: novo_usuario.id})
            # Atualiza eventos
            eventos_atualizados = PlannerEvento.query.update({PlannerEvento.usuario_crm_id: novo_usuario.id})
            
            db.session.commit()
            
            print(f"\n✅ Registros vinculados ao usuário:")
            print(f"   - {clientes_atualizados} clientes")
            print(f"   - {mesas_atualizadas} mesas de negócio")
            print(f"   - {ocorrencias_atualizadas} ocorrências")
            print(f"   - {mensagens_atualizadas} mensagens WhatsApp")
            print(f"   - {produtos_atualizados} produtos")
            print(f"   - {eventos_atualizados} eventos do planner")

if __name__ == '__main__':
    criar_usuario_crm_inicial()
