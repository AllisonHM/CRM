"""
Serviço para descobrir a conta do Instagram Business conectada a uma página do Facebook.

Usa o campo 'instagram_business_account' da Graph API.
Nem toda página possui um Instagram Business conectado — isso é tratado sem erro.
"""

import requests
from typing import Optional, Tuple

META_GRAPH_VERSION = "v19.0"
GRAPH_BASE = f"https://graph.facebook.com/{META_GRAPH_VERSION}"


def buscar_instagram_da_pagina(
    page_id: str,
    page_access_token: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Verifica se a página possui uma conta Instagram Business vinculada.

    Retorna:
        (instagram_id, None)     se uma conta Instagram Business for encontrada.
        (None, None)             se a página não tiver Instagram conectado.
        (None, mensagem_erro)    em caso de falha grave de API.

    A ausência de Instagram NÃO é considerada erro — páginas sem Instagram
    Business são válidas e serão salvas normalmente, apenas sem instagram_id.
    """
    url = f"{GRAPH_BASE}/{page_id}"
    params = {
        "fields": "instagram_business_account",
        "access_token": page_access_token,
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
    except requests.exceptions.RequestException as exc:
        # Falha de rede: não bloqueia o salvamento da página
        return None, f"Falha de conexão ao verificar Instagram: {exc}"

    if "error" in data:
        # Erro de permissão ou token — também não bloqueia
        return None, None

    ig_data = data.get("instagram_business_account")
    if ig_data and ig_data.get("id"):
        return ig_data["id"], None

    # Página sem Instagram Business conectado
    return None, None
