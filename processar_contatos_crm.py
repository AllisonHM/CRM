"""
Processador de Contatos para CRM
=================================
Recebe arquivos .xlsx ou .csv e gera um CSV padronizado e limpo,
pronto para importação no CRM e disparos via WhatsApp.

Uso:
    python processar_contatos_crm.py <arquivo>
    python processar_contatos_crm.py clientes.xlsx
    python processar_contatos_crm.py leads.csv
"""

import sys
import re
import os
import chardet
import pandas as pd


# ---------------------------------------------------------------------------
# Mapeamento de colunas → padrão CRM
# ---------------------------------------------------------------------------
COLUMN_MAP = {
    "nome":         "nome",
    "name":         "nome",
    "cliente":      "nome",
    "razao_social": "nome",
    "razao social":  "nome",
    "telefone":     "telefone",
    "celular":      "telefone",
    "whatsapp":     "telefone",
    "fone":         "telefone",
    "phone":        "telefone",
    "mobile":       "telefone",
    "tel":          "telefone",
    "email":        "email",
    "e-mail":       "email",
    "e_mail":       "email",
    "mail":         "email",
    "empresa":      "empresa",
    "empresa_nome": "empresa",
    "company":      "empresa",
    "cnpj":         "empresa",
}

COLUNAS_SAIDA = ["nome", "telefone", "email", "empresa"]


# ---------------------------------------------------------------------------
# Utilitários
# ---------------------------------------------------------------------------

def detectar_encoding(caminho: str) -> str:
    """Detecta encoding do arquivo com fallback sequencial."""
    with open(caminho, "rb") as f:
        raw = f.read(min(65536, os.path.getsize(caminho)))
    resultado = chardet.detect(raw)
    enc = resultado.get("encoding") or "utf-8"
    # Normaliza aliases
    enc = enc.lower().replace("-", "").replace("_", "")
    if enc in ("utf8", "utf8bom", "utf8sig"):
        return "utf-8-sig"
    if enc in ("latin1", "iso88591", "windows1252", "cp1252"):
        return "latin-1"
    return resultado.get("encoding") or "utf-8"


def limpar_telefone(valor) -> str:
    """
    Limpa e padroniza o número de telefone.
    Retorna string com apenas dígitos, com DDI 55 se necessário.
    Retorna '' se inválido.
    """
    if pd.isna(valor):
        return ""
    tel = str(valor).strip()
    # Remove tudo que não for dígito
    tel = re.sub(r"\D", "", tel)
    if not tel:
        return ""
    # Remove .0 float residual (ex: "47999999999.0")
    tel = tel.rstrip("0").rstrip(".") if "." in tel else tel
    tel = re.sub(r"\D", "", tel)  # limpa novamente após float fix
    # Comprimento mínimo esperado: 10 dígitos (DDD + número) sem DDI
    if len(tel) < 8:
        return ""
    # Adiciona DDI 55 se ainda não tiver
    if not tel.startswith("55"):
        tel = "55" + tel
    # Valida comprimento final: 55 + DDD (2) + número (8 ou 9) = 12 ou 13
    if len(tel) < 12 or len(tel) > 13:
        return ""
    return tel


def limpar_nome(valor) -> str:
    """Remove espaços extras e capitaliza."""
    if pd.isna(valor):
        return ""
    nome = " ".join(str(valor).split())
    return nome.title()


def limpar_email(valor) -> str:
    """Valida formato básico de e-mail; retorna '' se inválido."""
    if pd.isna(valor):
        return ""
    email = str(valor).strip().lower()
    if re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        return email
    return ""


def limpar_empresa(valor) -> str:
    """Remove espaços extras."""
    if pd.isna(valor):
        return ""
    return " ".join(str(valor).split())


# ---------------------------------------------------------------------------
# Carregamento do arquivo
# ---------------------------------------------------------------------------

def carregar_arquivo(caminho: str) -> pd.DataFrame:
    ext = os.path.splitext(caminho)[1].lower()
    if ext in (".xlsx", ".xls", ".xlsm"):
        df = pd.read_excel(caminho, sheet_name=0, dtype=str)
    elif ext == ".csv":
        enc = detectar_encoding(caminho)
        try:
            df = pd.read_csv(caminho, encoding=enc, dtype=str, on_bad_lines="skip")
        except Exception:
            try:
                df = pd.read_csv(caminho, encoding="latin-1", dtype=str, on_bad_lines="skip")
            except Exception:
                df = pd.read_csv(caminho, encoding="ISO-8859-1", dtype=str, on_bad_lines="skip")
    else:
        raise ValueError(f"Formato não suportado: {ext}. Use .xlsx ou .csv")
    return df


# ---------------------------------------------------------------------------
# Mapeamento de colunas
# ---------------------------------------------------------------------------

def mapear_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Renomeia colunas para o padrão CRM e descarta as demais."""
    rename = {}
    for col in df.columns:
        chave = col.strip().lower()
        if chave in COLUMN_MAP:
            rename[col] = COLUMN_MAP[chave]

    df = df.rename(columns=rename)

    # Garante que todas as colunas de saída existam (mesmo que vazias)
    colunas_presentes = [c for c in COLUNAS_SAIDA if c in df.columns]
    for c in COLUNAS_SAIDA:
        if c not in df.columns:
            df[c] = ""

    # Mantém somente as colunas de saída na ordem correta
    return df[COLUNAS_SAIDA]


# ---------------------------------------------------------------------------
# Pipeline de limpeza
# ---------------------------------------------------------------------------

def processar(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Telefone — etapa crítica primeiro
    df["telefone"] = df["telefone"].apply(limpar_telefone)

    # Remove linhas sem telefone válido
    df = df[df["telefone"] != ""].copy()

    # Nome
    df["nome"] = df["nome"].apply(limpar_nome)

    # Email
    df["email"] = df["email"].apply(limpar_email)

    # Empresa
    df["empresa"] = df["empresa"].apply(limpar_empresa)

    # Remove linhas completamente vazias (após limpeza de telefone já tratado)
    df = df.dropna(how="all")

    # Remove duplicados pelo telefone (mantém primeira ocorrência)
    df = df.drop_duplicates(subset=["telefone"], keep="first")

    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Relatório de resumo
# ---------------------------------------------------------------------------

def imprimir_resumo(total_original: int, df_final: pd.DataFrame):
    removidos = total_original - len(df_final)
    print("=" * 50)
    print("  RELATÓRIO DE PROCESSAMENTO")
    print("=" * 50)
    print(f"  Registros originais : {total_original}")
    print(f"  Registros válidos   : {len(df_final)}")
    print(f"  Removidos/inválidos : {removidos}")
    print("=" * 50)


# ---------------------------------------------------------------------------
# Ponto de entrada
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Uso: python processar_contatos_crm.py <arquivo.xlsx|arquivo.csv>")
        sys.exit(1)

    caminho_entrada = sys.argv[1]

    if not os.path.isfile(caminho_entrada):
        print(f"Erro: arquivo não encontrado → {caminho_entrada}")
        sys.exit(1)

    # Carrega
    df = carregar_arquivo(caminho_entrada)
    total_original = len(df)

    # Mapeia colunas
    df = mapear_colunas(df)

    # Processa
    df = processar(df)

    # Define nome do arquivo de saída
    base, _ = os.path.splitext(caminho_entrada)
    caminho_saida = f"{base}_crm_ready.csv"

    # Salva
    df.to_csv(caminho_saida, index=False, encoding="utf-8")

    imprimir_resumo(total_original, df)
    print(f"\n  Arquivo gerado: {caminho_saida}\n")


if __name__ == "__main__":
    main()
