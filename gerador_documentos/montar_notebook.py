"""Monta o notebook do Colab a partir de gerar_documentos.py, painel.py e do modelo .docx.
Rode depois de alterar qualquer um deles:  python montar_notebook.py"""
import base64
import json
from pathlib import Path

AQUI = Path(__file__).resolve().parent
MODELO = AQUI / "Modelo_Documento_de_Acompanhamento_Quadrimestral_do_Auditor.docx"
codigo_gerador = (AQUI / "gerar_documentos.py").read_text(encoding="utf-8")
codigo_painel = (AQUI / "painel.py").read_text(encoding="utf-8")
modelo_b64 = base64.b64encode(MODELO.read_bytes()).decode()


def md(texto):
    return {"cell_type": "markdown", "metadata": {}, "source": texto}


def code(texto):
    return {"cell_type": "code", "metadata": {"cellView": "form"}, "execution_count": None, "outputs": [],
            "source": texto}


celulas = [
    md("# DEASUS · Documentos de Acompanhamento Periódico do Auditor\n\n"
       "1. No BI, aba **Acompanhamento Periódico**: filtre o período → na tabela, menu **…** → "
       "**Exportar dados** → **Dados com layout atual** → `.xlsx`.\n"
       "2. Aqui: menu **Ambiente de execução → Executar tudo** e use o **painel** que aparece abaixo.\n\n"
       "O modelo do documento já está embutido. Para usar outro modelo, escolha o `.docx` junto com o Excel.\n\n"
       "A avaliação descritiva é escrita depois, direto em cada documento."),
    code('#@title ▶ Painel (clique em Executar tudo) { display-mode: "form" }\n'
         'import subprocess, sys\n'
         'subprocess.run([sys.executable, "-m", "pip", "-q", "install", "docxtpl"], check=False)\n'
         '# código: gerar_documentos.py e painel.py (repositório BI-Interno-DEASUS, pasta gerador_documentos)\n'
         'open("gerar_documentos.py", "w", encoding="utf-8").write(' + repr(codigo_gerador) + ')\n'
         'open("painel.py", "w", encoding="utf-8").write(' + repr(codigo_painel) + ')\n'
         'MODELO_PADRAO_B64 = ' + repr(modelo_b64) + '\n'
         'try:\n'
         '    from google.colab import files, output\n'
         '    output.enable_custom_widget_manager()\n'
         '    baixar = files.download\n'
         'except ImportError:  # fora do Colab (Jupyter): só o link de download\n'
         '    baixar = None\n'
         'import importlib, gerar_documentos, painel\n'
         'importlib.reload(gerar_documentos); importlib.reload(painel)\n'
         '_painel = painel.criar_painel(MODELO_PADRAO_B64, baixar)\n'),
    md("---\n**Plano B** — só se o botão *Escolher Excel* do painel não funcionar: preencha os campos abaixo, "
       "clique no ▶ desta célula e escolha o Excel no botão que aparecer."),
    code('#@title Plano B: enviar o Excel e gerar { display-mode: "form" }\n'
         'PERIODO = ""  #@param {type:"string"}\n'
         'AVALIADORES = ""  #@param {type:"string"}\n'
         'DATA = ""  #@param {type:"string"}\n'
         'import os, base64, shutil\n'
         'from google.colab import files\n'
         'import gerar_documentos\n'
         'shutil.rmtree("entrada", ignore_errors=True); os.makedirs("entrada")\n'
         'excel = modelo = None\n'
         'for nome, dados in files.upload().items():\n'
         '    destino = os.path.join("entrada", nome)\n'
         '    open(destino, "wb").write(dados)\n'
         '    if nome.lower().endswith((".xlsx", ".csv")): excel = destino\n'
         '    elif nome.lower().endswith(".docx"): modelo = destino\n'
         'if not modelo:\n'
         '    modelo = "entrada/modelo_padrao.docx"\n'
         '    open(modelo, "wb").write(base64.b64decode(MODELO_PADRAO_B64))\n'
         'if not excel or not PERIODO.strip():\n'
         '    raise SystemExit("Preencha o PERIODO e escolha o Excel exportado do BI.")\n'
         'files.download(gerar_documentos.gerar(excel, modelo, PERIODO.strip(), AVALIADORES.strip(), data=DATA.strip() or None))\n'),
]
nb = {"cells": celulas,
      "metadata": {"colab": {"provenance": []}, "kernelspec": {"name": "python3", "display_name": "Python 3"},
                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 0}
(AQUI / "Gerador_Acompanhamento_Periodico.ipynb").write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("Notebook gerado.")
