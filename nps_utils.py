# nps_utils.py
from datetime import datetime, timedelta
from models import Cliente, UsuarioCRM
from database import db

def obter_clientes_aptos_nps(usuario_crm_id):
    """
    Retorna a lista de clientes aptos a receber solicitação de NPS
    com base no intervalo de quarentena configurado pelo usuário do CRM.
    
    Args:
        usuario_crm_id: ID do usuário/instância do CRM
        
    Returns:
        Lista de objetos Cliente aptos a receber NPS
    """
    # Busca as configurações do usuário CRM
    usuario = UsuarioCRM.query.get(usuario_crm_id)
    if not usuario:
        return []
    
    # Calcula a data limite (data atual - dias de quarentena)
    data_limite = datetime.now() - timedelta(days=usuario.dias_quarentena_nps)
    
    # Busca clientes desta instância que:
    # 1. Nunca receberam NPS (data_ultimo_nps_envio é None)
    # 2. OU receberam há mais tempo que a quarentena
    clientes_aptos = Cliente.query.filter(
        Cliente.usuario_crm_id == usuario_crm_id,
        db.or_(
            Cliente.data_ultimo_nps_envio.is_(None),
            Cliente.data_ultimo_nps_envio <= data_limite
        )
    ).all()
    
    return clientes_aptos


def marcar_envio_nps(cliente_id):
    """
    Marca que o cliente recebeu uma solicitação de NPS agora.
    Atualiza o campo data_ultimo_nps_envio e aguardando_nps.
    
    Args:
        cliente_id: ID do cliente que recebeu o NPS
    """
    cliente = Cliente.query.get(cliente_id)
    if cliente:
        cliente.data_ultimo_nps_envio = datetime.now()
        cliente.aguardando_nps = True
        db.session.commit()


def registrar_resposta_nps(cliente_id, nota, comentario=None):
    """
    Registra a resposta do cliente ao NPS.
    
    Args:
        cliente_id: ID do cliente que respondeu
        nota: Nota de 0 a 10
        comentario: Comentário opcional do cliente
    """
    cliente = Cliente.query.get(cliente_id)
    if cliente:
        cliente.nps_nota = nota
        cliente.nps_data = datetime.now()
        cliente.nps_comentario = comentario
        cliente.aguardando_nps = False
        db.session.commit()


def enviar_nps_em_massa(usuario_crm_id):
    """
    Envia solicitação de NPS para todos os clientes aptos
    de uma instância específica do CRM.
    
    Args:
        usuario_crm_id: ID do usuário/instância do CRM
        
    Returns:
        Dicionário com resultado do envio
    """
    clientes_aptos = obter_clientes_aptos_nps(usuario_crm_id)
    
    enviados = []
    erros = []
    
    for cliente in clientes_aptos:
        try:
            # Aqui você integraria com a API de WhatsApp
            # Por enquanto, apenas marca como enviado
            marcar_envio_nps(cliente.id)
            enviados.append(cliente.nome)
            
            # TODO: Implementar envio real via API WhatsApp
            # enviar_whatsapp(cliente.telefone, mensagem_nps)
            
        except Exception as e:
            erros.append(f"{cliente.nome}: {str(e)}")
    
    return {
        'total_aptos': len(clientes_aptos),
        'enviados': len(enviados),
        'erros': len(erros),
        'detalhes_enviados': enviados,
        'detalhes_erros': erros
    }


def obter_estatisticas_nps(usuario_crm_id):
    """
    Retorna estatísticas de NPS para uma instância do CRM.
    
    Args:
        usuario_crm_id: ID do usuário/instância do CRM
        
    Returns:
        Dicionário com estatísticas
    """
    clientes = Cliente.query.filter_by(usuario_crm_id=usuario_crm_id).all()
    
    total_clientes = len(clientes)
    clientes_com_nps = len([c for c in clientes if c.nps_nota is not None])
    aguardando_resposta = len([c for c in clientes if c.aguardando_nps])
    clientes_aptos = len(obter_clientes_aptos_nps(usuario_crm_id))
    
    # Calcula NPS médio (promotores - detratores)
    notas = [c.nps_nota for c in clientes if c.nps_nota is not None]
    if notas:
        promotores = len([n for n in notas if n >= 9])
        detratores = len([n for n in notas if n <= 6])
        nps_score = ((promotores - detratores) / len(notas)) * 100
    else:
        nps_score = None
    
    return {
        'total_clientes': total_clientes,
        'clientes_com_nps': clientes_com_nps,
        'aguardando_resposta': aguardando_resposta,
        'clientes_aptos_novo_envio': clientes_aptos,
        'nps_score': round(nps_score, 2) if nps_score is not None else None,
        'taxa_resposta': round((clientes_com_nps / total_clientes * 100), 2) if total_clientes > 0 else 0
    }
