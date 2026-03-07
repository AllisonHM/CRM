"""
Blueprint Flask: Webhook da Meta (Facebook Messenger + Instagram DM)

Rotas:
    GET  /webhooks/meta  → Verificação do webhook pela Meta (challenge)
    POST /webhooks/meta  → Recebimento de eventos em tempo real

Segurança:
    • Verificação de assinatura HMAC-SHA256 no cabeçalho X-Hub-Signature-256.
    • O META_VERIFY_TOKEN deve ser definido no .env e registrado no painel
      do App da Meta em "Webhooks → Verify Token".
    • Retorna sempre HTTP 200 para eventos POST — a Meta considera qualquer
      outro código como falha e reenvia o evento (podendo causar duplicatas).
    • A deduplicação de mensagens é feita no service via platform_message_id.
"""

import hashlib
import hmac
import logging
import os

from flask import Blueprint, abort, jsonify, request

from services.meta_webhook_service import processar_evento_webhook

logger = logging.getLogger(__name__)

meta_webhook_bp = Blueprint("meta_webhook", __name__)


# ---------------------------------------------------------------------------
# GET /webhooks/meta — Verificação do webhook
# ---------------------------------------------------------------------------

@meta_webhook_bp.route("/webhooks/meta", methods=["GET"])
def webhook_verify():
    """
    Endpoint de verificação do webhook solicitado pela Meta.

    A Meta envia três query params:
      hub.mode         → deve ser "subscribe"
      hub.verify_token → deve coincidir com META_VERIFY_TOKEN no .env
      hub.challenge    → número aleatório que deve ser devolvido

    Configure META_VERIFY_TOKEN no .env com qualquer string secreta
    e registre o mesmo valor no painel do App da Meta.
    """
    mode = request.args.get("hub.mode")
    token_recebido = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    verify_token = os.getenv("META_VERIFY_TOKEN", "")

    if not verify_token:
        logger.error(
            "META_VERIFY_TOKEN não configurado no .env! "
            "Defina um valor secreto para esta variável."
        )
        abort(500)

    if mode == "subscribe" and token_recebido == verify_token:
        logger.info("Webhook Meta verificado com sucesso.")
        return challenge, 200

    logger.warning(
        f"Falha na verificação do webhook Meta. "
        f"Token recebido: {token_recebido!r} | Esperado: (oculto)"
    )
    abort(403)


# ---------------------------------------------------------------------------
# POST /webhooks/meta — Recebimento de eventos
# ---------------------------------------------------------------------------

@meta_webhook_bp.route("/webhooks/meta", methods=["POST"])
def webhook_event():
    """
    Recebe e processa eventos da Meta (Messenger + Instagram DM).

    Valida a assinatura HMAC-SHA256 antes de processar para garantir que
    a requisição veio realmente da Meta e não de um atacante externo.

    Retorna HTTP 200 imediatamente após processar — a Meta exige resposta
    em menos de 20 segundos. Erros internos são logados mas não propagados.
    """
    # ── Validação de assinatura ──────────────────────────────────────────
    app_secret = os.getenv("META_APP_SECRET", "")
    if app_secret:
        sig_header = request.headers.get("X-Hub-Signature-256", "")
        if not _verificar_assinatura(request.data, app_secret, sig_header):
            logger.warning(
                "Requisição ao webhook rejeitada: assinatura HMAC inválida. "
                "Possível tentativa de injeção de payload."
            )
            abort(403)
    else:
        logger.debug("META_APP_SECRET não definido — validação de assinatura ignorada.")

    # ── Parsing do payload ───────────────────────────────────────────────
    payload = request.get_json(silent=True)
    if not payload:
        logger.warning("Webhook recebeu payload vazio ou não-JSON.")
        return jsonify({"status": "ok"}), 200

    # ── Processamento ────────────────────────────────────────────────────
    try:
        n = processar_evento_webhook(payload)
        if n:
            logger.info(f"Webhook Meta processado: {n} mensagem(s) salva(s).")
    except Exception as exc:
        # Retorna 200 mesmo em erro para evitar reenvios infinitos da Meta
        logger.error(f"Erro não tratado ao processar webhook Meta: {exc}", exc_info=True)

    return jsonify({"status": "ok"}), 200


# ---------------------------------------------------------------------------
# Utilitário
# ---------------------------------------------------------------------------

def _verificar_assinatura(payload_bytes: bytes, app_secret: str, header: str) -> bool:
    """
    Valida o cabeçalho X-Hub-Signature-256 usando HMAC-SHA256.

    A Meta assina o payload com o APP_SECRET e envia no formato:
        sha256=<hex_digest>

    Usa hmac.compare_digest para comparação segura contra timing attacks.
    """
    if not header.startswith("sha256="):
        return False

    assinatura_recebida = header.split("sha256=", 1)[1]
    mac = hmac.new(
        app_secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    )
    return hmac.compare_digest(mac.hexdigest(), assinatura_recebida)
