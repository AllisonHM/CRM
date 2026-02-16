"""
Script para atualizar mensagens antigas do WhatsApp associando-as ao usuário correto.
Isso corrige mensagens que foram salvas sem usuario_crm_id.
"""
from database_rls import db, init_db
from models import WhatsAppMensagem, Cliente
from CRM import app, normalize_phone, find_cliente_by_phone

def atualizar_mensagens():
    """Atualiza mensagens sem usuario_crm_id"""
    with app.app_context():
        print("\n" + "="*60)
        print("🔧 INICIANDO ATUALIZAÇÃO DE MENSAGENS")
        print("="*60)
        
        # Buscar mensagens sem usuario_crm_id
        mensagens_sem_usuario = WhatsAppMensagem.query.filter(
            WhatsAppMensagem.usuario_crm_id.is_(None)
        ).all()
        
        print(f"\n📊 Total de mensagens sem usuário: {len(mensagens_sem_usuario)}")
        
        if len(mensagens_sem_usuario) == 0:
            print("✅ Todas as mensagens já têm usuário associado!")
            return
        
        atualizadas = 0
        nao_encontradas = 0
        
        for msg in mensagens_sem_usuario:
            # Buscar cliente pelo número da mensagem
            cliente = find_cliente_by_phone(msg.numero)
            
            if cliente and cliente.usuario_crm_id:
                msg.usuario_crm_id = cliente.usuario_crm_id
                atualizadas += 1
                print(f"✅ Mensagem {msg.id} associada ao usuário {cliente.usuario_crm_id} (Cliente: {cliente.nome})")
            else:
                nao_encontradas += 1
                print(f"⚠️ Mensagem {msg.id} - Cliente não encontrado para número {msg.numero}")
        
        # Salvar alterações
        if atualizadas > 0:
            db.session.commit()
            print(f"\n💾 {atualizadas} mensagens atualizadas com sucesso!")
        
        if nao_encontradas > 0:
            print(f"⚠️ {nao_encontradas} mensagens não puderam ser associadas (cliente não encontrado)")
            print("   Essas mensagens só serão visíveis para super_admin")
        
        print("\n" + "="*60)
        print("✅ ATUALIZAÇÃO CONCLUÍDA")
        print("="*60 + "\n")

if __name__ == "__main__":
    atualizar_mensagens()
