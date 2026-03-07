"""
Serviço para envio de mensagens via Meta Graph API e renovação de tokens.

Responsabilidades:
 - Enviar mensagem para um contato (Facebook Messenger ou Instagram DM).
 - Persistir mensagens enviadas pelo agente no banco.
 - Trocar short-lived tokens por long-lived tokens (válidos ~60 dias).
 - Renovar tokens de todas as páginas (job automático mensal).
"""

import logging
import requests
from datetime import datetime
from typing import Optional, Tuple

from database_rls import db
from models import Conversation, FacebookPage, Message

logger = logging.getLogger(__name__)

META_GRAPH_VERSION = "v19.0"
GRAPH_BASE = f"https://graph.facebook.com/{META_GRAPH_VERSION}"
TOKEN_URL = f"{GRAPH_BASE}/oauth/access_token"


# ---------------------------------------------------------------------------
# Envio de mensagens
# ---------------------------------------------------------------------------

def enviar_mensagem(
    conversa: Conversation,
    texto: str,
    usuario_crm_id: int,
) -> Tuple[bool, Optional[str]]:
    """
    Envia uma mensagem para o contato da conversa via Meta Graph API.

    Escolhe automaticamente o endpoint correto:
      • Facebook Messenger → POST /{page_id}/messages
      • Instagram DM      → POST /{ig_id}/messages

    Retorna (True, None) em sucesso ou (False, mensagem_erro) em falha.
    """
    # Busca a página associada à conversa, filtrando pelo tenant
    fb_page: Optional[FacebookPage] = FacebookPage.query.filter_by(
        usuario_crm_id=usuario_crm_id,
        page_id=conversa.page_id,
    ).first()

    if not fb_page:
        return False, "Página não encontrada para este usuário. Reconecte nas Parametrizações."

    token = fb_page.page_access_token

    if conversa.platform == "instagram":
        return _enviar_instagram(
            ig_id=fb_page.instagram_id,
            recipient_id=conversa.contact_id,
            texto=texto,
            token=token,
        )

    return _enviar_messenger(
        page_id=conversa.page_id,
        recipient_id=conversa.contact_id,
        texto=texto,
        token=token,
    )


def _enviar_messenger(
    page_id: str,
    recipient_id: str,
    texto: str,
    token: str,
) -> Tuple[bool, Optional[str]]:
    """Envia mensagem via Facebook Messenger."""
    url = f"{GRAPH_BASE}/{page_id}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": texto},
        "messaging_type": "RESPONSE",  # Resposta dentro da janela de 24h
    }

    try:
        resp = requests.post(url, json=payload, params={"access_token": token}, timeout=15)
        data = resp.json()
    except requests.exceptions.RequestException as exc:
        return False, f"Falha de conexão com a Meta: {exc}"

    if "error" in data:
        return False, data["error"].get("message", "Erro desconhecido da Meta.")

    return True, None


def _enviar_instagram(
    ig_id: Optional[str],
    recipient_id: str,
    texto: str,
    token: str,
) -> Tuple[bool, Optional[str]]:
    """Envia mensagem via Instagram Direct Message."""
    if not ig_id:
        return False, "Esta página não possui Instagram Business conectado."

    url = f"{GRAPH_BASE}/{ig_id}/messages"
    payload = {
        "recipient": {"id": recipient_id},
        "message": {"text": texto},
    }

    try:
        resp = requests.post(url, json=payload, params={"access_token": token}, timeout=15)
        data = resp.json()
    except requests.exceptions.RequestException as exc:
        return False, f"Falha de conexão com a Meta: {exc}"

    if "error" in data:
        return False, data["error"].get("message", "Erro desconhecido da Meta.")

    return True, None


# ---------------------------------------------------------------------------
# Persistência de mensagens enviadas
# ---------------------------------------------------------------------------

def salvar_mensagem_enviada(
    conversa: Conversation,
    texto: str,
) -> Message:
    """
    Persiste no banco a mensagem enviada pelo agente e atualiza last_message_at.
    """
    agora = datetime.utcnow()

    msg = Message(
        conversation_id=conversa.id,
        sender_type="agent",
        message_text=texto,
        platform_message_id=None,  # Mensagens enviadas não têm mid da Meta
        created_at=agora,
    )
    db.session.add(msg)
    conversa.last_message_at = agora
    db.session.commit()
    return msg


# ---------------------------------------------------------------------------
# Renovação de tokens
# ---------------------------------------------------------------------------

def exchange_for_long_lived_token(
    app_id: str,
    app_secret: str,
    short_lived_token: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Troca um short-lived user/page token por um long-lived token (~60 dias).

    Endpoint: GET /oauth/access_token
    Parâmetro especial: grant_type=fb_exchange_token

    Retorna (novo_token, None) em sucesso ou (None, mensagem_erro) em falha.
    """
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token,
    }

    try:
        resp = requests.get(TOKEN_URL, params=params, timeout=15)
        data = resp.json()
    except requests.exceptions.RequestException as exc:
        return None, f"Falha de conexão ao renovar token: {exc}"

    if "error" in data:
        return None, data["error"].get("message", "Erro ao renovar token.")

    novo_token = data.get("access_token")
    if not novo_token:
        return None, "Meta não retornou um token válido na renovação."

    return novo_token, None


def renovar_tokens_expirados(app_id: str, app_secret: str) -> int:
    """
    Percorre todas as páginas conectadas e renova seus page_access_tokens.

    Chamado pelo job automático a cada 30 dias.
    Page_access_tokens de pages são tecnicamente de longa duração, mas
    a renovação proativa garante continuidade do serviço.

    Retorna o número de tokens renovados com sucesso.
    """
    paginas = FacebookPage.query.all()
    renovados = 0

    for pagina in paginas:
        novo_token, erro = exchange_for_long_lived_token(
            app_id, app_secret, pagina.page_access_token
        )
        if novo_token:
            pagina.page_access_token = novo_token
            renovados += 1
            logger.info(f"Token renovado: {pagina.page_name} (page_id={pagina.page_id})")
        else:
            logger.warning(
                f"Falha ao renovar token para {pagina.page_name} (page_id={pagina.page_id}): {erro}"
            )

    if renovados > 0:
        try:
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            logger.error(f"Erro ao salvar tokens renovados: {exc}")
            return 0

    return renovados
