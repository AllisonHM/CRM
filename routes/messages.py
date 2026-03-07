"""
Blueprint Flask: Envio de mensagens via Meta Graph API.

Rota:
    POST /api/messages/send
        Envia uma mensagem para o contato de uma conversa existente.
        Identifica automaticamente se é Messenger ou Instagram DM.
        Persiste a mensagem enviada no banco e atualiza last_message_at.

Autenticação:
    @login_required — chamado via fetch() do inbox.html com cookie de sessão.
"""

import logging
from typing import Optional

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from models import Conversation
from services.message_service import enviar_mensagem, salvar_mensagem_enviada

logger = logging.getLogger(__name__)

messages_bp = Blueprint("messages", __name__)


@messages_bp.route("/api/messages/send", methods=["POST"])
@login_required
def enviar():
    """
    Envia uma mensagem para o contato de uma conversa.

    Payload JSON esperado:
        {
            "conversation_id": 123,
            "message": "Olá, como posso ajudar?"
        }

    Fluxo:
        1. Valida os campos obrigatórios.
        2. Busca a conversa filtrando por usuario_crm_id (isolamento por tenant).
        3. Chama o service que escolhe Messenger ou Instagram DM e faz o POST na Meta.
        4. Persiste a mensagem no banco como sender_type='agent'.
        5. Retorna JSON com status e IDs.
    """
    data = request.get_json(silent=True) or {}

    conversation_id = data.get("conversation_id")
    texto: str = (data.get("message") or "").strip()

    # ── Validação de entrada ─────────────────────────────────────────────
    if not conversation_id:
        return jsonify({"error": "conversation_id é obrigatório."}), 400
    if not texto:
        return jsonify({"error": "message não pode estar vazio."}), 400
    if len(texto) > 2000:
        return jsonify({"error": "Mensagem excede 2000 caracteres."}), 400

    # ── Busca de conversa (tenant isolation) ─────────────────────────────
    conversa: Optional[Conversation] = Conversation.query.filter_by(
        id=conversation_id,
        usuario_crm_id=current_user.id,
    ).first()

    if not conversa:
        return jsonify({"error": "Conversa não encontrada."}), 404

    # ── Envio via Meta Graph API ─────────────────────────────────────────
    sucesso, erro = enviar_mensagem(conversa, texto, current_user.id)

    if not sucesso:
        logger.error(
            f"Falha ao enviar mensagem | conversa={conversation_id} | "
            f"usuario={current_user.id} | erro={erro}"
        )
        return jsonify({"error": f"Falha ao enviar mensagem: {erro}"}), 502

    # ── Persiste no banco ────────────────────────────────────────────────
    msg = salvar_mensagem_enviada(conversa, texto)

    return jsonify({
        "status": "enviada",
        "message_id": msg.id,
        "conversation_id": conversa.id,
    }), 200
