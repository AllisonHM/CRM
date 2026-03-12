# tasks.py — Tarefas assíncronas com Celery
import os
import logging
import requests
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# Configuração do Celery (requer REDIS_URL no .env)
# Exemplo: REDIS_URL=redis://localhost:6379/0
# ------------------------------------------------------------------
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery = Celery(
    'tasks',
    broker=REDIS_URL,
    backend=REDIS_URL,
)
celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='America/Sao_Paulo',
    enable_utc=True,
)

# ------------------------------------------------------------------
# Credenciais Z-API — lidas do .env
# ------------------------------------------------------------------
ZAPI_INSTANCE = os.getenv('ZAPI_INSTANCE', '')
ZAPI_TOKEN = os.getenv('ZAPI_TOKEN', '')
ZAPI_CLIENT_TOKEN = os.getenv('ZAPI_CLIENT_TOKEN', '')


def _build_zapi_url(endpoint: str) -> str:
    return (
        f"https://api.z-api.io/instances/{ZAPI_INSTANCE}"
        f"/token/{ZAPI_TOKEN}/{endpoint}"
    )


@celery.task(bind=True, max_retries=3, default_retry_delay=10)
def enviar_whatsapp(self, numero: str, texto: str):
    """Envia mensagem de texto via Z-API de forma assíncrona."""
    if not ZAPI_INSTANCE or not ZAPI_TOKEN:
        logger.error("ZAPI_INSTANCE ou ZAPI_TOKEN não configurados no .env")
        return {"status": "error", "detail": "Credenciais Z-API ausentes"}

    url = _build_zapi_url("send-text")
    headers = {
        'client-token': ZAPI_CLIENT_TOKEN,
        'Content-Type': 'application/json',
    }
    payload = {"phone": numero, "message": texto}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        logger.info(f"Mensagem enviada para {numero}: {resp.status_code}")
        return resp.json()
    except requests.exceptions.RequestException as exc:
        logger.error(f"Erro ao enviar WhatsApp para {numero}: {exc}")
        raise self.retry(exc=exc)
