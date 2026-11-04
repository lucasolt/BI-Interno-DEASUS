"""Monta o notebook do Colab a partir de gerar_documentos.py (fonte única do código).
Rode depois de alterar gerar_documentos.py:  python montar_notebook.py"""
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
codigo = (AQUI / "gerar_documentos.py").read_text(encoding="utf-8")


def md(texto):
    return {"cell_type": "markdown", "metadata": {}, "source": texto}


def code(texto, form=False):
    meta = {"cellView": "form"} if form else {}
    return {"cell_type": "code", "metadata": meta, "execution_count": None, "outputs": [], "source": texto}


celulas = [
    md("# DEASUS · Documentos de Acompanhamento Periódico do Auditor\n\n"
       "**Como usar (3 passos):**\n\n"
       "1. No BI, aba **Acompanhamento Periódico**: filtre o período → na tabela, menu **…** → "
       "**Exportar dados** → **Dados com layout atual** → `.xlsx`.\n"
       "2. Preencha o **período** e os **avaliadores** abaixo.\n"
       "3. Menu **Ambiente de execução → Executar tudo**. Quando aparecer o botão **Escolher arquivos**, "
       "selecione **juntos** o Excel exportado e o modelo `.docx`. No fim, o navegador baixa um `.zip` "
       "com um documento por auditor.\n\n"
       "Dica: se quiser a avaliação descritiva já preenchida, acrescente no Excel uma coluna chamada "
       "**Avaliação Descritiva** antes de enviar. Se não, escreva direto em cada documento depois."),
    code('#@title 1. Dados do período { display-mode: "form" }\n'
         'PERIODO = "1º/2026"  #@param {type:"string"}\n'
         'AVALIADORES = ""  #@param {type:"string"}\n', form=True),
    code('#@title 2. Preparação (não precisa mexer) { display-mode: "form" }\n'
         '!pip -q install docxtpl\n'
         '# código do gerador (fonte: gerar_documentos.py no repositório BI-Interno-DEASUS)\n'
         'CODIGO = ' + repr(codigo) + '\n'
         'open("gerar_documentos.py", "w", encoding="utf-8").write(CODIGO)\n'
         'print("Pronto.")\n', form=True),
    code('#@title 3. Enviar arquivos e gerar documentos { display-mode: "form" }\n'
         'import os, shutil\n'
         'from google.colab import files\n'
         'import gerar_documentos as g\n'
         '\n'
         'for pasta in ("entrada", "documentos_acompanhamento"):\n'
         '    shutil.rmtree(pasta, ignore_errors=True)\n'
         'os.makedirs("entrada")\n'
         'print("Selecione JUNTOS o Excel exportado do BI e o modelo .docx:")\n'
         'enviados = files.upload()\n'
         'excel = modelo = None\n'
         'for nome in enviados:\n'
         '    destino = os.path.join("entrada", nome)\n'
         '    shutil.move(nome, destino)\n'
         '    if nome.lower().endswith((".xlsx", ".csv")):\n'
         '        excel = destino\n'
         '    elif nome.lower().endswith(".docx"):\n'
         '        modelo = destino\n'
         'if not excel or not modelo:\n'
         '    raise SystemExit("Faltou arquivo: envie o Excel (.xlsx) E o modelo (.docx). Rode esta célula de novo.")\n'
         'zip_path = g.gerar(excel, modelo, PERIODO, AVALIADORES)\n'
         'files.download(zip_path)\n', form=True),
]
celulas = [c for c in celulas if c["source"].strip()]
nb = {"cells": celulas, "metadata": {"colab": {"provenance": []}, "kernelspec": {"name": "python3", "display_name": "Python 3"},
                                     "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
(AQUI / "Gerador_Acompanhamento_Periodico.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("Notebook gerado.")
