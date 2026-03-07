"""
Serviço de autenticação OAuth com a Meta (Facebook / Instagram).

Responsabilidades:
 - Montar a URL de autorização para o dialog/oauth da Meta.
 - Trocar o 'code' recebido no callback por um user access token.
"""

import requests
from urllib.parse import urlencode
from typing import Optional, Tuple

# Versão da Graph API utilizada em todos os endpoints
META_GRAPH_VERSION = "v19.0"
META_DIALOG_BASE = f"https://www.facebook.com/{META_GRAPH_VERSION}/dialog/oauth"
META_TOKEN_URL = f"https://graph.facebook.com/{META_GRAPH_VERSION}/oauth/access_token"

# Permissões necessárias para páginas + Instagram
# Ajuste conforme as permissões aprovadas no seu App da Meta
OAUTH_SCOPES = ",".join([
    "pages_show_list",
    "pages_read_engagement",
    "pages_manage_metadata",
    "pages_messaging",
    "instagram_basic",
    "instagram_manage_messages",
])


def get_oauth_redirect_url(app_id: str, redirect_uri: str, state: str) -> str:
    """
    Monta e retorna a URL completa do dialog de autorização da Meta.

    Parâmetros:
        app_id      – META_APP_ID cadastrado no painel de desenvolvedor da Meta.
        redirect_uri – URL de callback registrada no App (deve ser exata).
        state       – Token aleatório para proteção CSRF (armazenado na sessão).
    """
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "scope": OAUTH_SCOPES,
        "response_type": "code",
        "state": state,
    }
    return f"{META_DIALOG_BASE}?{urlencode(params)}"


def exchange_code_for_token(
    app_id: str,
    app_secret: str,
    redirect_uri: str,
    code: str,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Troca o 'code' recebido no callback por um short-lived user access token.

    Retorna:
        (access_token, None)  em caso de sucesso.
        (None, mensagem_erro) em caso de falha.

    O user_access_token é temporário (normalmente válido por ~1-2 horas).
    Ele é usado APENAS para listar as páginas do usuário via /me/accounts.
    Os page_access_tokens retornados por /me/accounts são os tokens persistentes.
    """
    params = {
        "client_id": app_id,
        "client_secret": app_secret,
        "redirect_uri": redirect_uri,
        "code": code,
    }

    try:
        resp = requests.get(META_TOKEN_URL, params=params, timeout=15)
        data = resp.json()
    except requests.exceptions.RequestException as exc:
        return None, f"Falha de conexão com a Meta: {exc}"

    if "error" in data:
        msg = data["error"].get("message", "Erro desconhecido retornado pela Meta.")
        return None, msg

    token = data.get("access_token")
    if not token:
        return None, "A Meta não retornou um access_token válido."

    return token, None
