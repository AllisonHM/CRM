"""
Blueprint Flask: Integração OAuth Meta (Facebook / Instagram)

Rotas:
    GET  /auth/meta/login              – Inicia o fluxo OAuth redirecionando para o Facebook
    GET  /auth/meta/callback           – Recebe o 'code', troca por token, salva páginas
    POST /auth/meta/desconectar/<id>   – Remove uma página conectada do banco

Segurança:
    - Parâmetro 'state' anti-CSRF armazenado em session antes do redirect.
    - Verificação obrigatória do 'state' no callback.
    - Todas as rotas exigem login (@login_required).
    - Desconexão via POST para evitar CSRF por GET.
"""

import os
import secrets
import logging
from typing import Optional

from flask import (
    Blueprint,
    redirect,
    url_for,
    request,
    flash,
    session,
    current_app,
)
from flask_login import login_required, current_user

from database_rls import db
from models import FacebookPage
from services.meta_auth_service import get_oauth_redirect_url, exchange_code_for_token
from services.meta_pages_service import buscar_paginas
from services.meta_instagram_service import buscar_instagram_da_pagina

logger = logging.getLogger(__name__)

# Blueprint registrado com prefixo /auth/meta
meta_auth_bp = Blueprint("meta_auth", __name__, url_prefix="/auth/meta")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_meta_config() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Lê as variáveis de ambiente da integração Meta.
    Retorna (app_id, app_secret, redirect_uri) — qualquer um pode ser None
    se não configurado, indicando que a integração está incompleta.
    """
    return (
        os.getenv("META_APP_ID"),
        os.getenv("META_APP_SECRET"),
        os.getenv("META_REDIRECT_URI"),
    )


def _config_valida(app_id, app_secret, redirect_uri) -> bool:
    """Verifica se as três variáveis de ambiente estão preenchidas."""
    return bool(app_id and app_secret and redirect_uri)


# ---------------------------------------------------------------------------
# Rota 1: Iniciar fluxo OAuth
# ---------------------------------------------------------------------------

@meta_auth_bp.route("/login")
@login_required
def login():
    """
    Inicia o fluxo OAuth da Meta.

    1. Valida que META_APP_ID / META_APP_SECRET / META_REDIRECT_URI estão definidos.
    2. Gera um token 'state' aleatório e o salva na sessão Flask (proteção CSRF).
    3. Redireciona o usuário para o dialog de autorização do Facebook.
    """
    app_id, app_secret, redirect_uri = _get_meta_config()

    if not _config_valida(app_id, app_secret, redirect_uri):
        flash(
            "Integração com a Meta não configurada. "
            "Defina META_APP_ID, META_APP_SECRET e META_REDIRECT_URI no arquivo .env.",
            "danger",
        )
        logger.warning("Tentativa de OAuth Meta sem variáveis de ambiente configuradas.")
        return redirect(url_for("parametrizacoes"))

    # Gera state anti-CSRF e persiste na sessão
    state = secrets.token_urlsafe(32)
    session["meta_oauth_state"] = state

    oauth_url = get_oauth_redirect_url(app_id, redirect_uri, state)
    logger.info(
        f"Usuário {current_user.id} iniciou OAuth Meta. "
        f"Redirecionando para: {oauth_url[:80]}..."
    )
    return redirect(oauth_url)


# ---------------------------------------------------------------------------
# Rota 2: Callback OAuth
# ---------------------------------------------------------------------------

@meta_auth_bp.route("/callback")
@login_required
def callback():
    """
    Recebe o callback do Facebook após autorização do usuário.

    Etapas:
        1. Verifica se o usuário negou acesso.
        2. Valida o parâmetro 'state' contra o valor salvo na sessão (CSRF).
        3. Extrai o 'code' da query string.
        4. Troca o 'code' por user access token.
        5. Lista todas as páginas via /me/accounts.
        6. Para cada página, verifica se há Instagram Business conectado.
        7. Salva ou atualiza cada página no banco (upsert por page_id).
        8. Redireciona para parametrizações com mensagem de feedback.
    """
    # -- 1. Usuário negou acesso ou houve erro externo --
    if request.args.get("error"):
        descricao = request.args.get("error_description", "Permissão negada pelo usuário.")
        flash(f"Autorização cancelada: {descricao}", "warning")
        return redirect(url_for("parametrizacoes"))

    # -- 2. Verificação do state anti-CSRF --
    state_recebido = request.args.get("state", "")
    state_esperado = session.pop("meta_oauth_state", None)  # consume imediatamente

    if not state_esperado or state_recebido != state_esperado:
        flash(
            "Sessão de autorização inválida ou expirada. "
            "Por favor, tente conectar novamente.",
            "danger",
        )
        logger.warning(
            f"State OAuth inválido para usuário {current_user.id}. "
            f"Recebido: {state_recebido!r}, Esperado: {state_esperado!r}"
        )
        return redirect(url_for("parametrizacoes"))

    # -- 3. Extrai o code --
    code = request.args.get("code")
    if not code:
        flash("Código de autorização não recebido da Meta. Tente novamente.", "danger")
        return redirect(url_for("parametrizacoes"))

    app_id, app_secret, redirect_uri = _get_meta_config()

    # -- 4. Troca code por user access token --
    user_token, erro = exchange_code_for_token(app_id, app_secret, redirect_uri, code)
    if erro:
        flash(f"Erro ao obter token da Meta: {erro}", "danger")
        logger.error(f"exchange_code_for_token falhou para usuário {current_user.id}: {erro}")
        return redirect(url_for("parametrizacoes"))

    # -- 5. Busca páginas do usuário --
    paginas, erro = buscar_paginas(user_token)
    if erro:
        flash(f"Erro ao buscar páginas do Facebook: {erro}", "danger")
        logger.error(f"buscar_paginas falhou para usuário {current_user.id}: {erro}")
        return redirect(url_for("parametrizacoes"))

    if not paginas:
        flash(
            "Nenhuma página do Facebook encontrada. "
            "Certifique-se de ter selecionado ao menos uma página durante a autorização.",
            "warning",
        )
        return redirect(url_for("parametrizacoes"))

    # -- 6 & 7. Para cada página: verifica Instagram e salva no banco --
    novas = 0
    atualizadas = 0

    for p in paginas:
        instagram_id, _ = buscar_instagram_da_pagina(p["page_id"], p["page_access_token"])

        existente: Optional[FacebookPage] = FacebookPage.query.filter_by(
            usuario_crm_id=current_user.id,
            page_id=p["page_id"],
        ).first()

        if existente:
            # Atualiza token e dados (o page_access_token pode ser renovado)
            existente.page_name = p["page_name"]
            existente.page_access_token = p["page_access_token"]
            existente.instagram_id = instagram_id
            atualizadas += 1
        else:
            nova_pagina = FacebookPage(
                usuario_crm_id=current_user.id,
                page_id=p["page_id"],
                page_name=p["page_name"],
                page_access_token=p["page_access_token"],
                instagram_id=instagram_id,
            )
            db.session.add(nova_pagina)
            novas += 1

    # -- 8. Persiste no banco --
    try:
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        flash("Erro ao salvar páginas no banco de dados. Tente novamente.", "danger")
        logger.error(f"Erro ao commitar páginas Meta para usuário {current_user.id}: {exc}")
        return redirect(url_for("parametrizacoes"))

    # Feedback para o usuário
    partes = []
    if novas:
        partes.append(f"{novas} nova(s) página(s) conectada(s)")
    if atualizadas:
        partes.append(f"{atualizadas} página(s) atualizada(s)")

    flash(f"Integração Meta concluída: {', '.join(partes)}.", "success")
    logger.info(
        f"OAuth Meta concluído para usuário {current_user.id}: "
        f"{novas} novas, {atualizadas} atualizadas."
    )
    return redirect(url_for("parametrizacoes"))


# ---------------------------------------------------------------------------
# Rota 3: Desconectar página
# ---------------------------------------------------------------------------

@meta_auth_bp.route("/desconectar/<int:page_db_id>", methods=["POST"])
@login_required
def desconectar_pagina(page_db_id: int):
    """
    Remove uma página conectada do banco de dados.

    Utiliza POST (não GET) para evitar remoção acidental via CSRF.
    O filtro por usuario_crm_id garante que um usuário não remova
    páginas de outro tenant (controle de acesso por dado).
    """
    pagina: Optional[FacebookPage] = FacebookPage.query.filter_by(
        id=page_db_id,
        usuario_crm_id=current_user.id,  # Garante isolamento por tenant
    ).first_or_404()

    nome = pagina.page_name

    try:
        db.session.delete(pagina)
        db.session.commit()
        flash(f'Página "{nome}" desconectada com sucesso.', "success")
        logger.info(
            f"Usuário {current_user.id} desconectou página '{nome}' (id={page_db_id})."
        )
    except Exception as exc:
        db.session.rollback()
        flash("Erro ao desconectar a página. Tente novamente.", "danger")
        logger.error(f"Erro ao desconectar página {page_db_id}: {exc}")

    return redirect(url_for("parametrizacoes"))
