"""
Serviço para listar as páginas do Facebook vinculadas ao usuário autenticado.

Usa o endpoint GET /me/accounts da Graph API, que retorna a lista de
páginas que o usuário administra junto com o page_access_token de cada uma.
"""

import requests
from typing import Optional, List, Dict, Any, Tuple

META_GRAPH_VERSION = "v19.0"
ME_ACCOUNTS_URL = f"https://graph.facebook.com/{META_GRAPH_VERSION}/me/accounts"


def buscar_paginas(
    user_access_token: str,
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Retorna a lista de páginas que o usuário administra.

    Retorna:
        (lista_paginas, None)   em caso de sucesso.
        ([], mensagem_erro)     em caso de falha.

    Cada item da lista contém:
        {
            "page_id":            str  – ID único da página no Facebook,
            "page_name":          str  – Nome legível da página,
            "page_access_token":  str  – Token de acesso específico da página,
        }

    Nota: O page_access_token é persistido no banco pois tem vida útil longa
    (ou não expira, dependendo das configurações do app), ao contrário do
    user_access_token que é de curta duração.
    """
    params = {
        "access_token": user_access_token,
        "fields": "id,name,access_token",
    }

    try:
        resp = requests.get(ME_ACCOUNTS_URL, params=params, timeout=15)
        data = resp.json()
    except requests.exceptions.RequestException as exc:
        return [], f"Falha de conexão ao listar páginas: {exc}"

    if "error" in data:
        msg = data["error"].get("message", "Erro ao buscar páginas do Facebook.")
        return [], msg

    paginas_raw: List[Dict] = data.get("data", [])

    paginas: List[Dict[str, Any]] = []
    for p in paginas_raw:
        page_id = p.get("id")
        page_token = p.get("access_token")

        # Ignora entradas incompletas da API
        if not page_id or not page_token:
            continue

        paginas.append({
            "page_id": page_id,
            "page_name": p.get("name", "Página sem nome"),
            "page_access_token": page_token,
        })

    return paginas, None
