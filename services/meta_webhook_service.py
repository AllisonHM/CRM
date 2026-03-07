"""
Serviço para processar eventos de webhook recebidos da Meta.

Responsabilidades:
 - Identificar o tipo de evento (Messenger ou Instagram DM).
 - Extrair page_id, sender_id e texto da mensagem.
 - Salvar conversa e mensagem no banco com deduplicação.

ATENÇÃO MULTI-TENANT:
 O webhook é público (chamado pela Meta, sem sessão do usuário).
 Para encontrar o tenant correto, fazemos lookup por page_id na tabela
 facebook_pages. Caso a tabela tenha RLS habilitado no futuro, esta query
 precisará de uma conexão de superusuário ou role bypassrls.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from database_rls import db
from models import Conversation, FacebookPage, Message

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ponto de entrada principal
# ---------------------------------------------------------------------------

def processar_evento_webhook(payload: Dict[str, Any]) -> int:
    """
    Processa o payload completo enviado pela Meta ao webhook POST.

    Estruturas suportadas:
      • object == "page"  → Facebook Messenger  (entry[].messaging[])
      • object == "instagram" → Instagram DM    (entry[].changes[].value.messages[])

    Retorna o número de mensagens novas salvas.
    """
    object_type = payload.get("object", "")
    entries = payload.get("entry", [])
    total_salvas = 0

    for entry in entries:
        # O campo "id" do entry corresponde ao page_id no Messenger
        page_id = str(entry.get("id", ""))

        # ── 1. Facebook Messenger ─────────────────────────────────────────
        for event in entry.get("messaging", []):
            if _processar_evento_messenger(event, page_id):
                total_salvas += 1

        # ── 2. Instagram DM (via changes) ─────────────────────────────────
        for change in entry.get("changes", []):
            if change.get("field") == "messages":
                value = change.get("value", {})
                ig_page_id = str(value.get("recipient_id", page_id))

                for msg_event in value.get("messages", []):
                    if _processar_evento_instagram(msg_event, ig_page_id):
                        total_salvas += 1

    return total_salvas


# ---------------------------------------------------------------------------
# Handlers por plataforma
# ---------------------------------------------------------------------------

def _processar_evento_messenger(event: Dict[str, Any], page_id: str) -> bool:
    """
    Processa um evento individual do Messenger.

    Ignora:
      • Echoes (mensagens originadas pelo próprio bot/agente)
      • Eventos sem texto (ex.: stickers, location, reaction)
    """
    msg_data = event.get("message", {})

    # Ignora echo — É a mensagem que O PRÓPRIO bot enviou, refletida de volta
    if msg_data.get("is_echo"):
        return False

    sender_id = str(event.get("sender", {}).get("id", ""))
    text = msg_data.get("text", "").strip()
    mid = msg_data.get("mid", "")

    if not sender_id or not text:
        return False

    return _persistir_mensagem(
        page_id=page_id,
        sender_id=sender_id,
        text=text,
        mid=mid,
        platform="facebook",
    )


def _processar_evento_instagram(event: Dict[str, Any], page_id: str) -> bool:
    """
    Processa um evento de mensagem do Instagram DM.

    A estrutura é diferente do Messenger: o sender vem em 'from.id'
    e o texto em 'text.body' (ou 'text' direto dependendo da versão da API).
    """
    sender_id = str(event.get("from", {}).get("id", ""))
    mid = str(event.get("id", ""))

    # O texto pode vir em formatos ligeiramente diferentes conforme a versão
    text_field = event.get("text")
    if isinstance(text_field, dict):
        text = text_field.get("body", "").strip()
    else:
        text = str(text_field or "").strip()

    if not sender_id or not text:
        return False

    return _persistir_mensagem(
        page_id=page_id,
        sender_id=sender_id,
        text=text,
        mid=mid,
        platform="instagram",
    )


# ---------------------------------------------------------------------------
# Persistência com deduplicação e upsert de conversa
# ---------------------------------------------------------------------------

def _persistir_mensagem(
    page_id: str,
    sender_id: str,
    text: str,
    mid: str,
    platform: str,
) -> bool:
    """
    Salva a mensagem no banco de dados.

    Etapas:
      1. Deduplicação: verifica se mid (platform_message_id) já existe.
      2. Lookup do tenant via page_id → facebook_pages.
      3. Upsert da conversa (cria se não existir, atualiza last_message_at).
      4. Cria o registro de mensagem.
      5. Commit.

    Retorna True em sucesso, False em falha ou duplicata.
    """
    # ── 1. Deduplicação ───────────────────────────────────────────────────
    if mid:
        duplicata = Message.query.filter_by(platform_message_id=mid).first()
        if duplicata:
            logger.debug(f"Mensagem duplicada ignorada (mid={mid!r})")
            return False

    # ── 2. Identificar tenant (qual usuário do CRM é dono desta página) ───
    fb_page: Optional[FacebookPage] = FacebookPage.query.filter_by(page_id=page_id).first()
    if not fb_page:
        logger.warning(
            f"page_id {page_id!r} não encontrado em facebook_pages. "
            "Mensagem descartada — verifique se a página está conectada ao CRM."
        )
        return False

    usuario_crm_id = fb_page.usuario_crm_id
    agora = datetime.utcnow()

    # ── 3. Upsert da conversa ─────────────────────────────────────────────
    conversa: Optional[Conversation] = Conversation.query.filter_by(
        usuario_crm_id=usuario_crm_id,
        page_id=page_id,
        contact_id=sender_id,
        platform=platform,
    ).first()

    if conversa:
        conversa.last_message_at = agora
    else:
        conversa = Conversation(
            usuario_crm_id=usuario_crm_id,
            page_id=page_id,
            contact_id=sender_id,
            platform=platform,
            created_at=agora,
            last_message_at=agora,
        )
        db.session.add(conversa)
        db.session.flush()  # obtém conversa.id garantindo FK válida

    # ── 4. Criar mensagem ─────────────────────────────────────────────────
    msg = Message(
        conversation_id=conversa.id,
        sender_type="customer",
        message_text=text,
        platform_message_id=mid or None,
        created_at=agora,
    )
    db.session.add(msg)

    # ── 5. Commit ─────────────────────────────────────────────────────────
    try:
        db.session.commit()
        logger.info(
            f"Mensagem salva | conversa={conversa.id} | plataforma={platform} | sender={sender_id}"
        )
        return True
    except Exception as exc:
        db.session.rollback()
        logger.error(f"Erro ao persistir mensagem do webhook: {exc}")
        return False
