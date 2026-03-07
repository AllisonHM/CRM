"""
Blueprint Flask: Inbox — listagem de conversas e mensagens.

Rotas (JSON API, consumidas pelo template inbox.html via fetch):
    GET /api/conversations
        Retorna todas as conversas do usuário logado, da mais recente.
        Inclui preview da última mensagem para exibição na lista.

    GET /api/conversations/<id>/messages
        Retorna cabeçalho da conversa + lista completa de mensagens.
        Garante isolamento por tenant: só retorna conversas do tenantlogado.
"""

import logging
from typing import Optional

from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from models import Conversation, FacebookPage, Message

logger = logging.getLogger(__name__)

conversations_bp = Blueprint("conversations", __name__)


# ---------------------------------------------------------------------------
# GET /api/conversations
# ---------------------------------------------------------------------------

@conversations_bp.route("/api/conversations", methods=["GET"])
@login_required
def listar_conversas():
    """
    Retorna a lista de conversas do usuário logado, ordenada pela mais recente.

    Cada item inclui um campo 'last_message' com preview de 80 caracteres
    da última mensagem para exibição na sidebar do inbox.
    """
    conversas = (
        Conversation.query
        .filter_by(usuario_crm_id=current_user.id)
        .order_by(Conversation.last_message_at.desc())
        .all()
    )

    resultado = []
    for c in conversas:
        # Busca última mensagem (preview para sidebar)
        ultima: Optional[Message] = (
            Message.query
            .filter_by(conversation_id=c.id)
            .order_by(Message.created_at.desc())
            .first()
        )
        preview = (ultima.message_text[:80] if ultima else "") or ""

        # Resolve nome da página para exibição
        fb_page: Optional[FacebookPage] = FacebookPage.query.filter_by(
            usuario_crm_id=current_user.id,
            page_id=c.page_id,
        ).first()
        page_name = fb_page.page_name if fb_page else c.page_id

        resultado.append({
            "id": c.id,
            "page_id": c.page_id,
            "page_name": page_name,
            "contact_id": c.contact_id,
            "platform": c.platform,
            "last_message": preview,
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })

    return jsonify(resultado)


# ---------------------------------------------------------------------------
# GET /api/conversations/<id>/messages
# ---------------------------------------------------------------------------

@conversations_bp.route("/api/conversations/<int:conversation_id>/messages", methods=["GET"])
@login_required
def listar_mensagens(conversation_id: int):
    """
    Retorna todas as mensagens de uma conversa específica.

    O filtro por usuario_crm_id evita que um tenant acesse dados de outro
    (controle de acesso por dado, independente de RLS).
    """
    conversa: Optional[Conversation] = Conversation.query.filter_by(
        id=conversation_id,
        usuario_crm_id=current_user.id,
    ).first_or_404(description="Conversa não encontrada ou acesso negado.")

    mensagens = (
        Message.query
        .filter_by(conversation_id=conversa.id)
        .order_by(Message.created_at.asc())
        .all()
    )

    fb_page: Optional[FacebookPage] = FacebookPage.query.filter_by(
        usuario_crm_id=current_user.id,
        page_id=conversa.page_id,
    ).first()

    return jsonify({
        "conversation": {
            "id": conversa.id,
            "platform": conversa.platform,
            "contact_id": conversa.contact_id,
            "page_id": conversa.page_id,
            "page_name": fb_page.page_name if fb_page else conversa.page_id,
        },
        "messages": [
            {
                "id": m.id,
                "sender_type": m.sender_type,
                "message_text": m.message_text,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in mensagens
        ],
    })
