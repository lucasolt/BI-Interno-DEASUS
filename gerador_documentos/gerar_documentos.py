"""Gera os Documentos de Acompanhamento Periódico do Auditor (um .docx por auditor).

Entrada:
  1. O Excel exportado da tabela da aba "Acompanhamento Periódico" do BI
     (menu ... da tabela -> Exportar dados -> Dados com layout atual -> .xlsx).
  2. O modelo .docx com os campos {{ Auditor }}, {{ Quadrimestre }}, {{ Avaliadores }},
     {{ atividade_1 }} ... {{ avaliacao_7 }}, {{ proas }} e {{ Avaliacao_Descritiva }}.

As colunas são lidas PELO NOME (não pela posição). Se alguém renomear uma coluna no BI,
ajuste a lista ATIVIDADES abaixo.

Uso no computador (opcional; no dia a dia use o notebook no Colab):
    python gerar_documentos.py exportacao.xlsx modelo.docx --periodo "1º/2026" --avaliadores "Fulano, Beltrano"
"""
import os
import re
import ast
import zipfile
import unicodedata
from datetime import datetime

import pandas as pd
from docxtpl import DocxTemplate

# Linhas da tabela do documento: (texto que aparece no documento, coluna do Excel exportado).
# O modelo tem 7 linhas (atividade_1..7). Para mudar o que aparece, troque aqui.
ATIVIDADES = [
    ("Total de auditorias designadas", "Total de auditorias designadas"),
    ("Auditorias (coordenação)", "Auditorias (coordenação)"),
    ("Auditorias (composição de equipe)", "Auditorias (composição de equipe)"),
    ("Relatórios Preliminares entregues", "Relatórios Preliminares entregues"),
    ("Qtd de Matrizes RAI", "Qtd de Matrizes RAI"),   # 5ª linha igual à do notebook antigo
    ("Ciclos de monitoramento realizados como Coordenador", "Ciclos de monitoramento realizados como Coordenador"),
    ("Ciclos de monitoramento realizados como Equipe", "Ciclos de monitoramento realizados como Equipe"),
]
COL_AUDITOR = "Auditor"
COL_PROAS = "PROAs"
COL_DESCRITIVA = "Avaliação Descritiva"   # opcional: se existir no Excel, vai para o documento

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def _chave(txt):
    """Compara nomes de coluna sem acento, maiúsculas ou espaços extras."""
    txt = unicodedata.normalize("NFD", str(txt))
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", txt).strip().lower()


def ler_exportacao(caminho):
    """Lê o Excel/CSV exportado do BI. Acha a linha de cabeçalho (a que tem 'Auditor')
    e descarta linhas vazias, de total e as notas de filtro que o Power BI põe no fim."""
    if caminho.lower().endswith(".csv"):
        bruto = pd.read_csv(caminho, header=None, dtype=object)
    else:
        bruto = pd.read_excel(caminho, header=None, dtype=object)
    linha_cab = None
    for i, linha in bruto.iterrows():
        if any(_chave(v) == _chave(COL_AUDITOR) for v in linha.values if pd.notna(v)):
            linha_cab = i
            break
    if linha_cab is None:
        raise ValueError(f"Não achei a coluna '{COL_AUDITOR}' no arquivo {caminho}. "
                         "Confira se exportou a tabela da aba Acompanhamento Periódico.")
    df = bruto.iloc[linha_cab + 1:].copy()
    df.columns = [str(c).strip() if pd.notna(c) else f"_col{j}" for j, c in enumerate(bruto.iloc[linha_cab])]
    mapa = {_chave(c): c for c in df.columns}
    df = df.rename(columns={mapa[_chave(COL_AUDITOR)]: COL_AUDITOR})
    df[COL_AUDITOR] = df[COL_AUDITOR].astype("string").str.strip()
    ruido = df[COL_AUDITOR].isna() | (df[COL_AUDITOR] == "") | df[COL_AUDITOR].str.lower().isin(["total", "(não informado)"]) \
        | df[COL_AUDITOR].str.lower().str.startswith(("filtros aplicados", "applied filters"))
    return df[~ruido].reset_index(drop=True), mapa


def _numero(v):
    if v is None or (isinstance(v, float) and pd.isna(v)) or (isinstance(v, str) and not v.strip()):
        return "0"
    try:
        f = float(str(v).replace(",", "."))
        return str(int(f)) if f.is_integer() else f"{f:.2f}".replace(".", ",")
    except ValueError:
        return str(v)


def _proas(v):
    """Aceita 'A; B; C' (BI) ou "['A', 'B']" (planilha antiga do notebook)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = str(v).strip()
    if s.startswith("["):
        try:
            itens = ast.literal_eval(s)
        except (ValueError, SyntaxError):
            itens = [s]
    else:
        itens = re.split(r";|\n", s)
    return "\n".join(re.sub(r"\s+", " ", i).strip() for i in itens if str(i).strip())


def montar_contexto(linha, mapa, periodo, avaliadores):
    hoje = datetime.now()
    ctx = {
        "Auditor": linha[COL_AUDITOR],
        "Quadrimestre": periodo,
        "Avaliadores": avaliadores,
        "DataHoje": f"{hoje.day} de {MESES[hoje.month - 1]} de {hoje.year}",
        "proas": _proas(linha.get(mapa.get(_chave(COL_PROAS)))),
        "Avaliacao_Descritiva": "",
    }
    col_desc = mapa.get(_chave(COL_DESCRITIVA))
    if col_desc and pd.notna(linha.get(col_desc)):
        ctx["Avaliacao_Descritiva"] = str(linha.get(col_desc))
    for i, (rotulo, coluna) in enumerate(ATIVIDADES, start=1):
        col = mapa.get(_chave(coluna))
        ctx[f"atividade_{i}"] = rotulo
        ctx[f"avaliacao_{i}"] = _numero(linha.get(col)) if col else ""
    return ctx


def gerar(caminho_excel, caminho_modelo, periodo, avaliadores="", pasta_saida="documentos_acompanhamento"):
    df, mapa = ler_exportacao(caminho_excel)
    faltando = [c for _, c in ATIVIDADES if _chave(c) not in mapa]
    if faltando:
        print("ATENÇÃO: colunas não encontradas no Excel (ficarão em branco no documento):", faltando)
    if _chave(COL_PROAS) not in mapa:
        print(f"ATENÇÃO: coluna '{COL_PROAS}' não encontrada; a lista de PROAs sairá vazia.")
    os.makedirs(pasta_saida, exist_ok=True)
    arquivos = []
    for n, linha in df.iterrows():
        ctx = montar_contexto(linha, mapa, periodo, avaliadores)
        doc = DocxTemplate(caminho_modelo)
        doc.render(ctx)
        nome = re.sub(r"[^\w\-]+", "_", ctx["Auditor"]).strip("_")
        caminho = os.path.join(pasta_saida, f"acompanhamento_{n + 1:02d}_{nome}.docx")
        doc.save(caminho)
        arquivos.append(caminho)
        print("Gerado:", caminho)
    zip_path = pasta_saida.rstrip("/\\") + ".zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for a in arquivos:
            z.write(a, os.path.basename(a))
    print(f"\n{len(arquivos)} documento(s) gerado(s). ZIP: {zip_path}")
    return zip_path


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("excel")
    ap.add_argument("modelo")
    ap.add_argument("--periodo", required=True, help='Ex.: "1º/2026"')
    ap.add_argument("--avaliadores", default="")
    ap.add_argument("--saida", default="documentos_acompanhamento")
    a = ap.parse_args()
    gerar(a.excel, a.modelo, a.periodo, a.avaliadores, a.saida)
