"""Painel com botões (ipywidgets) para o gerador de documentos. Usado pelo notebook do Colab.

O modelo .docx vem embutido no notebook (MODELO_PADRAO_B64). Se a pessoa enviar um .docx
junto com o Excel, ele substitui o modelo embutido.
"""
import base64
import io
import os
import re
import shutil
import contextlib

import ipywidgets as w
from IPython.display import display

import gerar_documentos as g

PASTA_ENTRADA = "entrada"


def _arquivos_enviados(valor):
    """Normaliza o valor do FileUpload (ipywidgets 7: dict; ipywidgets 8: tupla) -> [(nome, bytes)]."""
    if isinstance(valor, dict):
        return [(nome, bytes(info["content"])) for nome, info in valor.items()]
    return [(item["name"], bytes(item["content"])) for item in valor]


def criar_painel(modelo_padrao_b64=None, baixar=None):
    """Monta e exibe o painel. `baixar(caminho)` é chamado para baixar o ZIP (no Colab: files.download)."""
    estilo = {"description_width": "110px"}
    larg = w.Layout(width="420px")
    periodo = w.Text(description="Período:", placeholder="ex.: 1º/2026", style=estilo, layout=larg)
    avaliadores = w.Text(description="Avaliadores:", placeholder="ex.: Fulano e Beltrano", style=estilo, layout=larg)
    _h = __import__("datetime").date.today()
    data = w.Text(description="Data:", value=f"{_h.day} de {g.MESES[_h.month - 1]} de {_h.year}", style=estilo, layout=larg)
    upload = w.FileUpload(accept=".xlsx,.csv,.docx", multiple=True, description="1. Escolher Excel do BI",
                          layout=w.Layout(width="260px"))
    recebidos = w.HTML("<i>Nenhum arquivo escolhido.</i>")
    gerar_btn = w.Button(description="2. Gerar documentos", button_style="primary", icon="cogs",
                         layout=w.Layout(width="260px"), disabled=True)
    baixar_btn = w.Button(description="3. Baixar ZIP", button_style="success", icon="download",
                          layout=w.Layout(width="260px"), disabled=True)
    link = w.HTML()
    log = w.Output(layout=w.Layout(border="1px solid #D5DCE6", padding="6px", max_height="260px", overflow="auto"))
    estado = {"zip": None}

    def ao_escolher(_=None):
        nomes = [n for n, _ in _arquivos_enviados(upload.value)]
        excel = [n for n in nomes if n.lower().endswith((".xlsx", ".csv"))]
        modelo = [n for n in nomes if n.lower().endswith(".docx")]
        partes = []
        partes.append(f"Excel: <b>{excel[-1]}</b>" if excel else "<span style='color:#D64545'>Falta o Excel exportado do BI</span>")
        partes.append(f"Modelo: <b>{modelo[-1]}</b>" if modelo else "Modelo: <b>padrão (embutido)</b>")
        recebidos.value = " · ".join(partes)
        gerar_btn.disabled = not excel
        baixar_btn.disabled = True
        link.value = ""

    def ao_gerar(_=None):
        log.clear_output()
        baixar_btn.disabled = True
        link.value = ""
        with log:
            if not periodo.value.strip():
                print("Preencha o Período antes de gerar.")
                return
            shutil.rmtree(PASTA_ENTRADA, ignore_errors=True)
            shutil.rmtree("documentos_acompanhamento", ignore_errors=True)
            os.makedirs(PASTA_ENTRADA)
            excel = modelo = None
            for nome, conteudo in _arquivos_enviados(upload.value):
                destino = os.path.join(PASTA_ENTRADA, os.path.basename(nome))
                with open(destino, "wb") as f:
                    f.write(conteudo)
                if nome.lower().endswith((".xlsx", ".csv")):
                    excel = destino
                elif nome.lower().endswith(".docx"):
                    modelo = destino
            if modelo is None:
                if not modelo_padrao_b64:
                    print("Envie também o modelo .docx.")
                    return
                modelo = os.path.join(PASTA_ENTRADA, "modelo_padrao.docx")
                with open(modelo, "wb") as f:
                    f.write(base64.b64decode(modelo_padrao_b64))
            gerar_btn.disabled = True
            gerar_btn.description = "Gerando..."
            try:
                estado["zip"] = g.gerar(excel, modelo, periodo.value.strip(), avaliadores.value.strip(), data=data.value.strip())
            except Exception as e:  # mostra o erro de forma legível
                print("\nERRO:", e)
                return
            finally:
                gerar_btn.disabled = False
                gerar_btn.description = "2. Gerar documentos"
            baixar_btn.disabled = False
            # link de reserva, caso o download automático seja bloqueado pelo navegador
            dados = base64.b64encode(open(estado["zip"], "rb").read()).decode()
            nome_zip = "documentos_" + re.sub(r"[^\w]+", "_", periodo.value.strip()).strip("_") + ".zip"
            link.value = (f"<a download='{nome_zip}' href='data:application/zip;base64,{dados}' "
                          f"style='font-size:13px'>Se o download não começar, clique aqui.</a>")

    def ao_baixar(_=None):
        if estado["zip"] and baixar:
            with log:
                baixar(estado["zip"])

    upload.observe(ao_escolher, names="value")
    gerar_btn.on_click(ao_gerar)
    baixar_btn.on_click(ao_baixar)

    titulo = w.HTML("<h3 style='margin:4px 0;color:#0B2E59'>Documentos de Acompanhamento Periódico</h3>"
                    "<div style='color:#5B6B7F'>Preencha, escolha o Excel exportado do BI e clique em gerar.</div>")
    painel = w.VBox([titulo, periodo, avaliadores, data, w.HBox([upload, recebidos]), gerar_btn,
                     w.HBox([baixar_btn, link]), log])
    display(painel)
    # devolvido para testes
    return {"periodo": periodo, "avaliadores": avaliadores, "data": data, "upload": upload, "gerar": ao_gerar,
            "escolher": ao_escolher, "baixar": ao_baixar, "estado": estado, "log": log, "recebidos": recebidos}
