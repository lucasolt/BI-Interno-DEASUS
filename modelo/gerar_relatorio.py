"""Gera as páginas/visuais (formato PBIR) do relatório 'BI Interno DEASUS'.

Uso (com o Power BI Desktop FECHADO):
    python modelo/gerar_relatorio.py

Apaga e recria todas as páginas em 'BI Interno DEASUS.Report/definition/pages'.
Ajustes manuais feitos no Desktop serão sobrescritos se o script for rodado de novo.
"""
import hashlib
import json
import os
import shutil
import stat
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGES = RAIZ / "BI Interno DEASUS.Report" / "definition" / "pages"

SCHEMA_VISUAL = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.12.0/schema.json"
SCHEMA_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
SCHEMA_PAGES = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json"

W, H = 1920, 1080
SIDEBAR = 180
X0, XMAX = SIDEBAR + 15, W - 7  # área útil

# ---------------- Paleta ----------------
NAVY = "#0B2E59"
NAVY2 = "#163F73"
FUNDO = "#EEF2F7"
BRANCO = "#FFFFFF"
BORDA = "#D5DCE6"
TEXTO = "#1F2D3D"
CINZA_TXT = "#5B6B7F"
VERDE = "#2E9E44"
VERMELHO = "#D64545"
AMARELO = "#F2B705"
CINZA = "#A6A6A6"
AZUL = "#1F6FD1"
VERDE_CLARO = "#7BC67E"

COR_SITUACAO = {
    "No prazo": VERDE,
    "Fora do prazo": VERMELHO,
    "Pendente (vencida)": AMARELO,
    "Em andamento": CINZA,
    "Não se aplica": "#C9D3E0",
    "Sem prazo definido": "#6E7F96",
}


# ---------------- Helpers de expressão ----------------
def uid(*partes):
    return hashlib.md5("|".join(partes).encode("utf-8")).hexdigest()[:20]


def L(v):
    return {"expr": {"Literal": {"Value": v}}}


def S(txt):  # literal string
    return L("'" + txt.replace("'", "''") + "'")


def D(n):
    return L(f"{n}D")


def B(b):
    return L("true" if b else "false")


def COR(hexa):
    return {"solid": {"color": L(f"'{hexa}'")}}


def col(tabela, coluna):
    return {"Column": {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": coluna}}


def med(nome, tabela="_Medidas"):
    return {"Measure": {"Expression": {"SourceRef": {"Entity": tabela}}, "Property": nome}}


def qref(campo):
    k = list(campo)[0]
    return f'{campo[k]["Expression"]["SourceRef"]["Entity"]}.{campo[k]["Property"]}'


def proj(campo, nome=None, active=None):
    p = {"field": campo, "queryRef": qref(campo), "nativeQueryRef": nome or campo[list(campo)[0]]["Property"]}
    if nome:
        p["displayName"] = nome
    if active is not None:
        p["active"] = active
    return p


def filtro_in(tabela, coluna, valores, nome):
    return {
        "name": nome,
        "field": col(tabela, coluna),
        "type": "Categorical",
        "filter": {
            "Version": 2,
            "From": [{"Name": "t", "Entity": tabela, "Type": 0}],
            "Where": [{"Condition": {"In": {
                "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "t"}}, "Property": coluna}}],
                "Values": [[{"Literal": {"Value": "'" + v + "'"}}] for v in valores],
            }}}],
        },
    }


# ---------------- Container ----------------
def container(titulo=None, fundo=BRANCO, borda=True, sombra=False, titulo_cor=NAVY, titulo_tam=12, raio=8):
    o = {
        "background": [{"properties": {"show": B(fundo is not None), **({"color": COR(fundo), "transparency": D(0)} if fundo else {})}}],
        "border": [{"properties": {"show": B(borda), "color": COR(BORDA), "radius": D(raio), "width": D(1)}}],
        "dropShadow": [{"properties": {"show": B(sombra)}}],
        "visualHeader": [{"properties": {"show": B(False)}}],
        "padding": [{"properties": {"top": D(6), "bottom": D(6), "left": D(8), "right": D(8)}}],
    }
    if titulo:
        o["title"] = [{"properties": {
            "show": B(True), "text": S(titulo), "fontColor": COR(titulo_cor), "fontSize": D(titulo_tam),
            "bold": B(True), "titleWrap": B(True)}}]
    else:
        o["title"] = [{"properties": {"show": B(False)}}]
    return o


class Pagina:
    def __init__(self, nome, titulo):
        self.id = uid("page", nome)
        self.nome = nome
        self.titulo = titulo
        self.visuais = []
        self.z = 0

    def add(self, chave, x, y, w, h, visual, filtros=None, how=None):
        self.z += 1
        v = {
            "$schema": SCHEMA_VISUAL,
            "name": uid(self.nome, chave),
            "position": {"x": x, "y": y, "z": self.z * 1000, "height": h, "width": w, "tabOrder": self.z * 1000},
            "visual": visual,
        }
        if filtros:
            v["filterConfig"] = {"filters": filtros}
        if how:
            v["howCreated"] = how
        self.visuais.append(v)
        return v


# ---------------- Fábricas de visuais ----------------
def shape(cor, raio=0, borda=None):
    obj = {
        "shape": [{"properties": {"tileShape": S("rectangle" if not raio else "rectangleRounded"),
                                  **({"roundEdge": L(f"{raio}L")} if raio else {})}}],
        "fill": [{"properties": {"fillColor": COR(cor), "transparency": D(0)}, "selector": {"id": "default"}}],
        "outline": [{"properties": {"show": B(borda is not None), **({"lineColor": COR(borda), "weight": D(1)} if borda else {})}}],
    }
    return {"visualType": "shape", "objects": obj, "drillFilterOtherVisuals": True}


def textbox(paragrafos, fundo=None):
    """paragrafos: lista de listas de (texto, estilo-dict)."""
    pars = []
    for runs in paragrafos:
        pars.append({"textRuns": [{"value": t, "textStyle": st} for t, st in runs]})
    vco = {"background": [{"properties": {"show": B(fundo is not None), **({"color": COR(fundo)} if fundo else {})}}]}
    return {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": pars}}]},
            "visualContainerObjects": vco, "drillFilterOtherVisuals": True}


def st(tam=11, cor=TEXTO, negrito=False):
    d = {"fontSize": f"{tam}pt", "color": cor}
    if negrito:
        d["fontWeight"] = "bold"
    return d


def card(medida, titulo=None, tam=28, cor=NAVY, fundo=BRANCO, borda=True):
    return {
        "visualType": "card",
        "query": {"queryState": {"Values": {"projections": [proj(med(medida))]}}},
        "objects": {
            "labels": [{"properties": {"color": COR(cor), "fontSize": D(tam), "labelDisplayUnits": D(1), "bold": B(True)}}],
            "categoryLabels": [{"properties": {"show": B(False)}}],
        },
        "visualContainerObjects": container(titulo, fundo=fundo, borda=borda, titulo_cor=CINZA_TXT, titulo_tam=11),
        "drillFilterOtherVisuals": True,
    }


def slicer(campo, titulo, sync, modo="Dropdown"):
    return {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [proj(campo, nome=titulo, active=True)]}}},
        "objects": {
            "data": [{"properties": {"mode": S(modo)}}],
            "selection": [{"properties": {"selectAllCheckboxEnabled": B(True), "singleSelect": B(False)}}],
            "header": [{"properties": {"show": B(True), "fontColor": COR(NAVY), "textSize": D(10)}}],
            "items": [{"properties": {"textSize": D(10)}}],
        },
        "visualContainerObjects": container(None, borda=True),
        "syncGroup": {"groupName": sync, "fieldChanges": True, "filterChanges": True},
        "drillFilterOtherVisuals": True,
    }


def grafico(tipo, categoria, medidas, titulo, cores=None, legenda=True, rotulos=True, eixo_valor=False,
            ordem=None, objetos_extra=None, series=None):
    qs = {"Category": {"projections": [proj(categoria, active=True)]},
          "Y": {"projections": [proj(med(m), nome=n) for m, n in medidas]}}
    if series:
        qs["Series"] = {"projections": [proj(series)]}
    obj = {
        "legend": [{"properties": {"show": B(legenda), "position": S("Top"), "fontSize": D(9)}}],
        "labels": [{"properties": {"show": B(rotulos), "fontSize": D(9), "labelDisplayUnits": D(1)}}],
        "valueAxis": [{"properties": {"show": B(eixo_valor), "showAxisTitle": B(False), "gridlineShow": B(False)}}],
        "categoryAxis": [{"properties": {"show": B(True), "showAxisTitle": B(False), "fontSize": D(9)}}],
    }
    if cores:
        obj["dataPoint"] = [{"properties": {"fill": COR(c)}, "selector": {"metadata": qref(med(m))}} for (m, _), c in zip(medidas, cores)]
    if objetos_extra:
        obj.update(objetos_extra)
    v = {"visualType": tipo, "query": {"queryState": qs}, "objects": obj,
         "visualContainerObjects": container(titulo), "drillFilterOtherVisuals": True}
    if ordem:
        campo, direcao = ordem
        v["query"]["sortDefinition"] = {"sort": [{"field": campo, "direction": direcao}]}
    return v


def donut_situacao(medida, titulo):
    cat = col("dSituacao", "Situação")
    dp = []
    for sit, c in COR_SITUACAO.items():
        dp.append({"properties": {"fill": COR(c)}, "selector": {"data": [{"scopeId": {"Comparison": {
            "ComparisonKind": 0, "Left": cat, "Right": {"Literal": {"Value": f"'{sit}'"}}}}}]}})
    return {
        "visualType": "donutChart",
        "query": {"queryState": {
            "Category": {"projections": [proj(cat, active=True)]},
            "Y": {"projections": [proj(med(medida))]}},
            "sortDefinition": {"sort": [{"field": cat, "direction": "Ascending"}]}},
        "objects": {
            "legend": [{"properties": {"show": B(True), "position": S("Right"), "fontSize": D(10)}}],
            "labels": [{"properties": {"show": B(True), "labelStyle": S("Percent of total"), "fontSize": D(9)}}],
            "dataPoint": dp,
        },
        "visualContainerObjects": container(titulo),
        "drillFilterOtherVisuals": True,
    }


def gauge(medida, titulo, cor):
    return {
        "visualType": "gauge",
        "query": {"queryState": {"Y": {"projections": [proj(med(medida))]}}},
        "objects": {
            "axis": [{"properties": {"min": D(0), "max": D(1)}}],
            "dataPoint": [{"properties": {"fill": COR(cor), "target": COR(NAVY)}}],
            "calloutValue": [{"properties": {"color": COR(NAVY), "fontSize": D(20)}}],
            "labels": [{"properties": {"show": B(True), "fontSize": D(8)}}],
        },
        "visualContainerObjects": container(titulo, borda=False, titulo_tam=10),
        "drillFilterOtherVisuals": True,
    }


def matriz(linhas, medidas, titulo, ordem_medida=None):
    v = {
        "visualType": "pivotTable",
        "query": {"queryState": {
            "Rows": {"projections": [proj(c, active=True) for c in linhas]},
            "Values": {"projections": [proj(med(m), nome=n) for m, n in medidas]}}},
        "objects": {
            "grid": [{"properties": {"rowPadding": D(3), "gridHorizontal": B(True), "gridHorizontalColor": COR("#E3E8EF")}}],
            "columnHeaders": [{"properties": {"fontColor": COR(BRANCO), "backColor": COR(NAVY), "fontSize": D(9),
                                              "bold": B(True), "wordWrap": B(True), "alignment": S("Center")}}],
            "rowHeaders": [{"properties": {"fontSize": D(9), "showExpandCollapseButtons": B(True)}}],
            "values": [{"properties": {"fontSize": D(9)}}],
            "subTotals": [{"properties": {"rowSubtotals": B(True), "fontColor": COR(NAVY), "bold": B(True),
                                          "backColor": COR("#E8EEF7"), "fontSize": D(9)}}],
            "total": [{"properties": {"fontColor": COR(BRANCO), "backColor": COR(NAVY2), "bold": B(True), "fontSize": D(10)}}],
        },
        "visualContainerObjects": container(titulo),
        "drillFilterOtherVisuals": True,
    }
    if ordem_medida:
        v["query"]["sortDefinition"] = {"sort": [{"field": med(ordem_medida), "direction": "Descending"}]}
    return v


def tabela(campos, titulo, ordem=None):
    v = {
        "visualType": "tableEx",
        "query": {"queryState": {"Values": {"projections": [proj(c, nome=n) for c, n in campos]}}},
        "objects": {
            "grid": [{"properties": {"rowPadding": D(3), "gridHorizontal": B(True), "gridHorizontalColor": COR("#E3E8EF")}}],
            "columnHeaders": [{"properties": {"fontColor": COR(BRANCO), "backColor": COR(NAVY), "fontSize": D(9),
                                              "bold": B(True), "wordWrap": B(True)}}],
            "values": [{"properties": {"fontSize": D(9)}}],
            "total": [{"properties": {"fontColor": COR(BRANCO), "backColor": COR(NAVY2), "bold": B(True)}}],
        },
        "visualContainerObjects": container(titulo),
        "drillFilterOtherVisuals": True,
    }
    if ordem:
        campo, direcao = ordem
        v["query"]["sortDefinition"] = {"sort": [{"field": campo, "direction": direcao}]}
    return v


# ---------------- Moldura comum (sidebar, cabeçalho, filtros) ----------------
SUBTITULO = {
    "geral": "Auditoria (RAI · RAF) e Monitoramento (1º, 2º e 3º Ciclos) · Designações, entregas e prazos",
    "aud": "Fase de Auditoria · Relatório Inicial (prazo 30 dias) e Relatório Final (prazo 60 dias) a partir da designação",
    "carteira": "Posição de hoje (não segue o filtro de Período) · auditoria pelo Status do processo (42), monitoramento pelo status do ciclo",
    "monit": "Monitoramento das Recomendações (1º, 2º e 3º Ciclos) · prazo de 30 dias após a Data Final da Designação",
}


def moldura(p: Pagina, fase="geral", com_filtros=True):
    p.add("fundo", 0, 0, W, H, shape(FUNDO))
    p.add("sidebar", 0, 0, SIDEBAR, H, shape(NAVY))
    p.add("logo", 10, 18, SIDEBAR - 20, 70, textbox([
        [("DEASUS", st(18, BRANCO, True))],
        [("Produtividade", st(10, "#BFD0E6"))],
    ]))
    p.add("nav", 8, 100, SIDEBAR - 16, 640, {
        "visualType": "pageNavigator",
        "objects": {
            "layout": [{"properties": {"orientation": D(1), "cellPadding": D(6)}}],
            "shape": [{"properties": {"tileShape": S("rectangleRounded"), "roundEdge": L("6L")}, "selector": {"id": "default"}}],
            "text": [
                {"properties": {"fontColor": COR(BRANCO), "fontSize": D(10), "bold": B(True)}, "selector": {"id": "default"}},
                {"properties": {"fontColor": COR(NAVY), "fontSize": D(10), "bold": B(True)}, "selector": {"id": "selected"}},
            ],
            "fill": [
                {"properties": {"fillColor": COR(NAVY2), "transparency": D(0)}, "selector": {"id": "default"}},
                {"properties": {"fillColor": COR(BRANCO), "transparency": D(0)}, "selector": {"id": "selected"}},
                {"properties": {"fillColor": COR("#24548F")}, "selector": {"id": "hover"}},
            ],
            "outline": [{"properties": {"show": B(False)}}],
        },
        "drillFilterOtherVisuals": True,
    }, how="InsertVisualButton")

    p.add("header", SIDEBAR, 0, W - SIDEBAR, 80, shape(NAVY))
    p.add("titulo", X0, 6, 1350, 70, textbox([
        [(p.titulo, st(20, BRANCO, True))],
        [(SUBTITULO[fase], st(11, "#BFD0E6"))],
    ]))
    p.add("atualizacao", W - 330, 18, 320, 46, card("Última Atualização", tam=12, cor=BRANCO, fundo=None, borda=False))

    if not com_filtros:
        return
    # barra lateral: auditores ativos (padrão: só ativos)
    ativo = slicer(col("dAuditor", "Ativo"), "Auditores ativos", "Auditores ativos")
    ativo["objects"]["general"] = [{"properties": {"filter": {"filter": filtro_in("dAuditor", "Ativo", ["Sim"], "x")["filter"]}}}]
    p.add("f_ativo", 8, 760, SIDEBAR - 16, 66, ativo)
    y, h = 90, 66
    x = X0
    titulo_periodo = {"geral": "Período (Designação)", "aud": "Período (Data de Designação)",
                      "monit": "Período (Data Inicial da Designação)"}[fase]
    p.add("f_periodo", x, y, 300, h, slicer(col("dCalendario", "Data"), titulo_periodo, "Periodo", "Between"))
    x += 310
    lista = []
    if fase == "monit":
        lista.append(("f_ciclo", col("fDesignacoes", "Ciclo"), "Ciclo"))
    elif fase == "aud":
        lista.append(("f_relatorio", col("fAuditoria", "Relatório"), "Relatório (RAI/RAF)"))
    lista += [
        ("f_funcao", col("dFuncao", "Função"), "Função"),
        ("f_auditor", col("dAuditor", "Auditor"), "Auditor"),
        ("f_eixo", col("dProcesso", "Eixo Temático"), "Eixo Temático"),
        ("f_situacao", col("dSituacao", "Situação"), "Situação"),
    ]
    larg = 232 if len(lista) == 5 else 290
    for chave, campo, tit in lista:
        filtros = None
        if chave == "f_auditor":
            filtros = [filtro_in("dAuditor", "Possui Designação", ["Sim"], "fPossuiDesig")]
        p.add(chave, x, y, larg, h, slicer(campo, tit, tit), filtros=filtros)
        x += larg + 10
    p.add("limpar", x, y + 8, XMAX - x, h - 16, {
        "visualType": "actionButton",
        "objects": {
            "icon": [{"properties": {"shapeType": S("blank")}, "selector": {"id": "default"}}],
            "text": [{"properties": {"show": B(True), "text": S("Limpar filtros"), "fontColor": COR(BRANCO),
                                     "fontSize": D(11), "bold": B(True)}, "selector": {"id": "default"}}],
            "fill": [{"properties": {"show": B(True), "fillColor": COR(NAVY), "transparency": D(0)}, "selector": {"id": "default"}}],
            "outline": [{"properties": {"show": B(False)}, "selector": {"id": "default"}}],
            "shape": [{"properties": {"tileShape": S("rectangleRounded"), "roundEdge": L("6L")}, "selector": {"id": "default"}}],
        },
        "visualContainerObjects": {"visualLink": [{"properties": {"show": B(True), "type": S("ClearAllSlicers")}}]},
        "drillFilterOtherVisuals": True,
    }, how="InsertVisualButton")


KPIS_MONIT = [
    ("Monitoramentos Designados", "Sub Designações", "Ciclos Designados (Monitoramento)", NAVY),
    ("Relatórios Entregues", "Sub Entregues", "Relatórios Entregues", AZUL),
    ("Entregues no Prazo", "Sub No Prazo", "Entregues no Prazo", VERDE),
    ("Entregues Fora do Prazo", "Sub Fora do Prazo", "Entregues Fora do Prazo", VERMELHO),
    ("Carteira Monitoramento", "Sub Carteira Mon", "Ciclos em Aberto Hoje", AMARELO),
    ("Dias Médios para Entrega", "Sub Prazo Médio", "Tempo Médio até a Entrega (dias)", NAVY),
]
KPIS_AUD = [
    ("Aud Processos Designados", "Sub Aud Designações", "Processos Designados (Auditoria)", NAVY),
    ("RAI Entregues", "Sub RAI Entregues", "RAI Entregues", AZUL),
    ("RAF Entregues", "Sub RAF Entregues", "RAF Entregues", VERDE),
    ("Carteira Auditoria", "Sub Carteira Quem", "Em Andamento Hoje (Auditoria)", AMARELO),
    ("RAI Dias Médios para Entrega", "Sub RAI Dias", "Dias Médios até o RAI", NAVY),
    ("Aud Média de Matrizes por Relatório", "Sub Aud Matrizes", "Matrizes de Qualidade / Relatório", VERMELHO),
]
# Página Auditoria: foco em dias (contínuo) no lugar de pendências vencidas (binário)
KPIS_AUD_PAGINA = [
    ("Aud Processos Designados", "Sub Aud Designações", "Processos Designados (Auditoria)", NAVY),
    ("RAI Entregues", "Sub RAI Entregues", "RAI Entregues", AZUL),
    ("RAF Entregues", "Sub RAF Entregues", "RAF Entregues", VERDE),
    ("RAI Dias Médios para Entrega", "Sub RAI Dias Card", "Dias Médios até o RAI", AZUL),
    ("RAF Dias Médios para Entrega", "Sub RAF Dias Card", "Dias Médios até o RAF", VERDE),
    ("Aud Média de Matrizes por Relatório", "Sub Aud Matrizes", "Matrizes de Qualidade / Relatório", VERMELHO),
]


def kpis(p: Pagina, itens, y=166, h=112, prefixo="kpi"):
    gap = 10
    w = (XMAX - X0 - gap * (len(itens) - 1)) / len(itens)
    tam = 26 if h >= 105 else 22
    for i, (m, sub, tit, cor) in enumerate(itens):
        x = X0 + i * (w + gap)
        p.add(f"{prefixo}_bg_{i}", x, y, w, h, shape(BRANCO, raio=8, borda=BORDA))
        p.add(f"{prefixo}_bar_{i}", x, y, 6, h, shape(cor))
        p.add(f"{prefixo}_{i}", x + 8, y + 2, w - 12, h - 32, card(m, tit, tam=tam, cor=cor, fundo=None, borda=False))
        p.add(f"{prefixo}_sub_{i}", x + 8, y + h - 32, w - 12, 28, card(sub, tam=9, cor=CINZA_TXT, fundo=None, borda=False))


def rotulo_secao(p: Pagina, chave, y, texto, cor=NAVY):
    p.add(chave, X0, y, XMAX - X0, 26, textbox([[(texto, st(12, cor, True))]]))


def taxas(p: Pagina, x, y, w, h, itens, titulo="TAXAS GERAIS"):
    p.add("taxas_bg", x, y, w, h, shape(BRANCO, raio=8, borda=BORDA))
    p.add("taxas_tit", x + 8, y + 6, w - 16, 34, textbox([[(titulo, st(12, NAVY, True))]]))
    gw = (w - 20) / len(itens)
    for i, (m, t, c) in enumerate(itens):
        p.add(f"gauge_{i}", x + 10 + i * gw, y + 50, gw, h - 60, gauge(m, t, c))


AUDITOR = col("dAuditor", "Auditor")
FUNCAO = col("dFuncao", "Função")
YG = 288          # topo da 2ª faixa nas páginas com KPI
XG = X0 + 1230    # coluna da direita
WG = XMAX - XG


# ---------------- Páginas ----------------
def pg_resumo():
    p = Pagina("resumo", "RESUMO DE PRODUTIVIDADE POR AUDITOR")
    p.nome_exib = "Resumo Geral"
    moldura(p, "geral")
    rotulo_secao(p, "sec_aud", 162, "AUDITORIA  ·  Relatório Inicial (RAI) e Relatório Final (RAF)")
    kpis(p, KPIS_AUD, y=188, h=100, prefixo="kaud")
    rotulo_secao(p, "sec_mon", 294, "MONITORAMENTO  ·  1º, 2º e 3º Ciclos")
    kpis(p, KPIS_MONIT, y=320, h=100, prefixo="kmon")
    y = 430
    p.add("matriz", X0, y, XMAX - X0, H - y - 8, matriz(
        [AUDITOR, FUNCAO],
        [("Aud Designações", "AUD · Designações"),
         ("RAI Entregues", "RAI · Entregues"), ("RAI Taxa de Pontualidade", "RAI · % no Prazo"),
         ("RAI Dias Médios para Entrega", "RAI · Dias Médios"),
         ("RAF Entregues", "RAF · Entregues"), ("RAF Taxa de Pontualidade", "RAF · % no Prazo"),
         ("RAF Dias Médios para Entrega", "RAF · Dias Médios"),
         ("Aud Média de Matrizes por Relatório", "AUD · Matrizes/Rel."),
         ("Designações", "MON · Designações"), ("Relatórios Entregues", "MON · Entregues"),
         ("Taxa de Pontualidade", "MON · % no Prazo"), ("Dias Médios para Entrega", "MON · Dias Médios")],
        "RESUMO POR AUDITOR · AUDITORIA x MONITORAMENTO (expanda para ver Coordenador x Equipe)",
        ordem_medida="Aud Designações"))
    return p


def pg_auditoria():
    p = Pagina("auditoria", "AUDITORIA · PRODUTIVIDADE")
    p.nome_exib = "Auditoria"
    moldura(p, "aud")
    kpis(p, KPIS_AUD_PAGINA)
    h2 = 330
    p.add("donut", X0, YG, 440, h2, donut_situacao("Aud Relatórios", "RELATÓRIOS POR SITUAÇÃO (RAI + RAF)"))
    p.add("evolucao", X0 + 450, YG, 770, h2, grafico(
        "columnChart", col("dCalendario", "Mês/Ano"),
        [("Aud No Prazo (por Data Entrega)", "Entregues no prazo"),
         ("Aud Fora do Prazo (por Data Entrega)", "Fora do prazo"),
         ("Aud Pendências Vencidas (por Data Limite)", "Pendentes vencidos")],
        "EVOLUÇÃO MENSAL DE ENTREGAS (RAI + RAF)", cores=[VERDE, VERMELHO, AMARELO],
        ordem=(col("dCalendario", "Mês/Ano"), "Ascending")))
    taxas(p, XG, YG, WG, h2, [("RAI Taxa de Pontualidade", "Pontualidade RAI", AZUL),
                              ("RAF Taxa de Pontualidade", "Pontualidade RAF", VERDE),
                              ("Aud Taxa de Pendência Vencida", "Pendência Vencida", VERMELHO)])
    y3 = YG + h2 + 10
    p.add("matriz", X0, y3, 1220, H - y3 - 8, matriz(
        [AUDITOR, FUNCAO],
        [("Aud Designações", "Designações"),
         ("RAI Entregues", "RAI Entregues"), ("RAI No Prazo", "RAI No Prazo"), ("RAI Fora do Prazo", "RAI Fora"),
         ("RAI Taxa de Pontualidade", "RAI % Prazo"),
         ("RAI Dias Médios para Entrega", "RAI Dias"),
         ("RAF Entregues", "RAF Entregues"), ("RAF No Prazo", "RAF No Prazo"), ("RAF Fora do Prazo", "RAF Fora"),
         ("RAF Taxa de Pontualidade", "RAF % Prazo"),
         ("RAF Dias Médios para Entrega", "RAF Dias"),
         ("Aud Média de Matrizes por Relatório", "Matrizes/Rel.")],
        "DESEMPENHO POR AUDITOR NA AUDITORIA", ordem_medida="Aud Designações"))
    hh = (H - y3 - 8 - 10) / 2
    ano = col("dCalendario", "Ano")
    p.add("dias_ano", XG, y3, WG, hh, grafico(
        "clusteredColumnChart", ano,
        [("RAI Dias Médios para Entrega", "RAI"), ("RAF Dias Médios para Entrega", "RAF")],
        "DIAS MÉDIOS ATÉ A ENTREGA, POR ANO DA DESIGNAÇÃO", cores=[AZUL, NAVY], ordem=(ano, "Ascending")))
    p.add("matriz_ano", XG, y3 + hh + 10, WG, hh, grafico(
        "clusteredColumnChart", ano,
        [("RAI Média de Matrizes", "RAI"), ("RAF Média de Matrizes", "RAF")],
        "MATRIZES DE QUALIDADE POR RELATÓRIO, POR ANO", cores=[AZUL, NAVY], ordem=(ano, "Ascending")))
    return p


def pg_auditoria_detalhe():
    p = Pagina("auditoria_detalhe", "AUDITORIA · DETALHES DOS RELATÓRIOS")
    p.nome_exib = "Auditoria · Detalhes"
    moldura(p, "aud")
    f = "fAuditoria"
    y = 166
    p.add("lista", X0, y, XMAX - X0, H - y - 8, tabela(
        [(col(f, "Nº PROA"), "Nº PROA"), (col("dProcesso", "Auditado"), "Auditado"), (col("dProcesso", "CRS"), "CRS"),
         (col("dProcesso", "Tipo de Auditoria"), "Tipo"), (col(f, "Relatório"), "Relatório"),
         (col(f, "Função"), "Função"), (col(f, "Auditor"), "Auditor"),
         (col(f, "Data Designação"), "Designação"), (col(f, "Data Limite"), "Data Limite"),
         (col(f, "Data Entrega"), "Entrega"), (col(f, "Nº Relatório"), "Nº Relatório"),
         (col(f, "Situação"), "Situação"), (col(f, "Dias para Entrega"), "Dias p/ Entrega"),
         (col(f, "Dias de Atraso"), "Dias de Atraso"), (col(f, "Matrizes de Qualidade"), "Matrizes"),
         (col(f, "Status do Processo"), "Status do Processo"), (col(f, "Alerta de Qualidade"), "Alerta de Qualidade")],
        "TODOS OS RELATÓRIOS DE AUDITORIA (use os filtros acima)", ordem=(col(f, "Data Designação"), "Descending")))
    return p


def pg_monitoramento():
    p = Pagina("visao_geral", "MONITORAMENTO · PRODUTIVIDADE")
    p.nome_exib = "Monitoramento"
    moldura(p, "monit")
    kpis(p, KPIS_MONIT)
    h2 = 330
    p.add("donut", X0, YG, 440, h2, donut_situacao("Designações", "DESIGNAÇÕES POR SITUAÇÃO"))
    p.add("evolucao", X0 + 450, YG, 770, h2, grafico(
        "columnChart", col("dCalendario", "Mês/Ano"),
        [("Entregas no Prazo (por Data Relatório)", "Entregues no prazo"),
         ("Entregas Fora do Prazo (por Data Relatório)", "Fora do prazo"),
         ("Pendências Vencidas (por Data Limite)", "Pendentes vencidos")],
        "EVOLUÇÃO DE ENTREGAS POR MÊS", cores=[VERDE, VERMELHO, AMARELO],
        ordem=(col("dCalendario", "Mês/Ano"), "Ascending")))
    taxas(p, XG, YG, WG, h2, [("Taxa de Entrega", "Taxa de Entrega", AZUL),
                              ("Taxa de Pontualidade", "Taxa de Pontualidade", AZUL),
                              ("Taxa de Pendência Vencida", "Taxa de Pendência Vencida", VERMELHO)])
    y3, h3 = YG + h2 + 10, 320
    p.add("matriz", X0, y3, 1220, h3, matriz(
        [AUDITOR, FUNCAO],
        [("Designações", "Designações"), ("Relatórios Entregues", "Entregues"),
         ("Entregues no Prazo", "No Prazo"), ("Entregues Fora do Prazo", "Fora do Prazo"),
         ("Taxa de Entrega", "Taxa de Entrega"),
         ("Taxa de Pontualidade", "Taxa de Pontualidade"), ("Dias Médios para Entrega", "Média de Dias (Entrega)")],
        "DESEMPENHO POR AUDITOR · Visão consolidada (Coordenador + Equipe)", ordem_medida="Designações"))
    hh = (h3 - 10) / 2
    ciclo = col("fDesignacoes", "Ciclo")
    p.add("ciclo_barras", XG, y3, WG, hh, grafico(
        "clusteredBarChart", ciclo, [("Designações", "Designações"), ("Relatórios Entregues", "Entregues")],
        "DESIGNAÇÕES POR CICLO", cores=[NAVY, VERDE_CLARO], ordem=(ciclo, "Ascending")))
    p.add("ciclo_dias", XG, y3 + hh + 10, WG, hh, grafico(
        "clusteredColumnChart", ciclo, [("Dias Médios para Entrega", "Dias médios")],
        "MÉDIA DE DIAS PARA ENTREGA POR CICLO", cores=[NAVY], legenda=False, ordem=(ciclo, "Ascending")))
    y4 = y3 + h3 + 10
    h4 = H - y4 - 8
    p.add("como_calc", X0, y4, 1220, h4, textbox([
        [("COMO É CALCULADO   ", st(11, NAVY, True)),
         ("Prazo: ", st(9, TEXTO, True)), ("Data Final da Designação + 30 dias.   ", st(9)),
         ("Taxa de Entrega: ", st(9, TEXTO, True)), ("Entregues ÷ (Entregues + Pendências vencidas).   ", st(9)),
         ("Taxa de Pontualidade: ", st(9, TEXTO, True)), ("No prazo ÷ Entregues.", st(9))],
        [("Dias para entrega = Data do Relatório − Data Inicial da Designação. Cada membro da equipe conta uma designação. "
          "Pendente (vencida) = sem relatório e Data Limite já ultrapassada na data da atualização.", st(9, CINZA_TXT))],
    ], fundo=BRANCO))
    p.add("obs", XG, y4, WG, h4, textbox([
        [("ÍNDICE DE PRODUTIVIDADE", st(11, NAVY, True))],
        [("40% Entrega + 40% Pontualidade + 20% Participação. Ranking em Monitoramento · Por Auditor.", st(9, CINZA_TXT))],
    ], fundo=BRANCO))
    return p


def pg_monit_auditor():
    p = Pagina("por_auditor", "MONITORAMENTO · POR AUDITOR")
    p.nome_exib = "Monitoramento · Por Auditor"
    moldura(p, "monit")
    y = 166
    h = H - y - 8
    p.add("matriz", X0, y, 1150, h, matriz(
        [AUDITOR, FUNCAO],
        [("Designações", "Designações"), ("Relatórios Entregues", "Entregues"),
         ("Entregues no Prazo", "No Prazo"), ("Entregues Fora do Prazo", "Fora do Prazo"),
         ("Taxa de Entrega", "Taxa de Entrega"), ("Taxa de Pontualidade", "Taxa de Pontualidade"),
         ("Dias Médios para Entrega", "Tempo Médio de Entrega"), ("Dias Médios de Atraso", "Dias Médios de Atraso"),
         ("Índice de Produtividade", "Índice"), ("Ranking Produtividade", "Ranking")],
        "DESEMPENHO POR AUDITOR NO MONITORAMENTO (expanda para ver Coordenador x Equipe)", ordem_medida="Designações"))
    x2 = X0 + 1160
    w2 = XMAX - x2
    h2 = (h - 10) / 2
    p.add("ranking", x2, y, w2, h2, grafico(
        "clusteredBarChart", AUDITOR, [("Índice de Produtividade", "Índice")],
        "CLASSIFICAÇÃO POR ÍNDICE DE PRODUTIVIDADE", cores=[AZUL], legenda=False,
        ordem=(med("Índice de Produtividade"), "Descending")))
    p.add("por_funcao", x2, y + h2 + 10, w2, h2, grafico(
        "barChart", AUDITOR, [("Designações Coordenador", "Coordenador"), ("Designações Equipe", "Equipe")],
        "DESIGNAÇÕES POR AUDITOR E FUNÇÃO", cores=[NAVY, VERDE_CLARO],
        ordem=(med("Designações Coordenador"), "Descending")))
    return p


def pg_monit_ciclo():
    p = Pagina("por_ciclo", "MONITORAMENTO · POR CICLO")
    p.nome_exib = "Monitoramento · Por Ciclo"
    moldura(p, "monit")
    kpis(p, KPIS_MONIT)
    h = (H - YG - 18) / 2
    wl = 900
    ciclo = col("fDesignacoes", "Ciclo")
    ordem = (ciclo, "Ascending")
    p.add("desig_ent", X0, YG, wl, h, grafico(
        "clusteredColumnChart", ciclo,
        [("Designações", "Designações"), ("Relatórios Entregues", "Entregues"), ("Pendências Vencidas", "Pend. vencidas")],
        "DESIGNAÇÕES E ENTREGAS POR CICLO", cores=[NAVY, VERDE_CLARO, AMARELO], ordem=ordem))
    p.add("funcao", X0 + wl + 10, YG, XMAX - X0 - wl - 10, h, grafico(
        "columnChart", ciclo, [("Designações Coordenador", "Coordenador"), ("Designações Equipe", "Equipe")],
        "DESIGNAÇÕES POR FUNÇÃO (COORDENADOR x EQUIPE)", cores=[NAVY, VERDE_CLARO], ordem=ordem))
    y2 = YG + h + 10
    p.add("taxas", X0, y2, wl, h, grafico(
        "clusteredColumnChart", ciclo, [("Taxa de Entrega", "Taxa de Entrega"), ("Taxa de Pontualidade", "Taxa de Pontualidade")],
        "TAXA DE ENTREGA E PONTUALIDADE POR CICLO", cores=[AZUL, VERDE], ordem=ordem))
    p.add("dias", X0 + wl + 10, y2, XMAX - X0 - wl - 10, h, grafico(
        "clusteredColumnChart", ciclo,
        [("Dias Médios para Entrega", "Dias médios p/ entrega"), ("Dias Médios de Atraso", "Dias médios de atraso")],
        "PRAZO MÉDIO DE ENTREGA E ATRASO POR CICLO (DIAS)", cores=[NAVY, VERMELHO], ordem=ordem))
    return p


def pg_monit_detalhe():
    p = Pagina("detalhamento", "MONITORAMENTO · DETALHES DAS DESIGNAÇÕES")
    p.nome_exib = "Monitoramento · Detalhes"
    moldura(p, "monit")
    y = 166
    f = "fDesignacoes"
    p.add("lista", X0, y, XMAX - X0, H - y - 8, tabela(
        [(col(f, "Nº PROA"), "Nº PROA"), (col("dProcesso", "Auditado"), "Auditado"), (col("dProcesso", "CRS"), "CRS"),
         (col(f, "Ciclo"), "Ciclo"), (col(f, "Função"), "Função"), (col(f, "Auditor"), "Auditor"),
         (col(f, "Data Inicial Designação"), "Início Designação"), (col(f, "Data Final Designação"), "Fim Designação"),
         (col(f, "Data Limite"), "Data Limite"), (col(f, "Nº Relatório"), "Nº Relatório"),
         (col(f, "Data Relatório"), "Data Relatório"), (col(f, "Situação"), "Situação"),
         (col(f, "Dias para Entrega"), "Dias p/ Entrega"), (col(f, "Dias de Atraso"), "Dias de Atraso"),
         (col(f, "Status do Ciclo"), "Status do Ciclo"), (col(f, "Alerta de Qualidade"), "Alerta de Qualidade")],
        "TODAS AS DESIGNAÇÕES DE MONITORAMENTO (use os filtros acima)",
        ordem=(col(f, "Data Final Designação"), "Descending")))
    return p


def pg_carteira():
    # mesmo id da antiga página "Pendências", que esta substitui
    p = Pagina("pendencias", "TRABALHOS EM ANDAMENTO · O QUE CADA AUDITOR TEM EM MÃOS")
    p.nome_exib = "Trabalhos em Andamento"
    moldura(p, "carteira", com_filtros=False)
    # sem filtro de Período/Situação: a carteira é sempre a posição de hoje
    y, h = 90, 66
    x = X0
    for chave, campo, tit in [("f_funcao", col("dFuncao", "Função"), "Função"),
                              ("f_auditor", col("dAuditor", "Auditor"), "Auditor"),
                              ("f_eixo", col("dProcesso", "Eixo Temático"), "Eixo Temático")]:
        filtros = [filtro_in("dAuditor", "Possui Designação", ["Sim"], "fPossuiDesig")] if chave == "f_auditor" else None
        p.add(chave, x, y, 400, h, slicer(campo, tit, tit), filtros=filtros)
        x += 410
    ativo = slicer(col("dAuditor", "Ativo"), "Auditores ativos", "Auditores ativos")
    ativo["objects"]["general"] = [{"properties": {"filter": {"filter": filtro_in("dAuditor", "Ativo", ["Sim"], "x")["filter"]}}}]
    p.add("f_ativo", 8, 760, SIDEBAR - 16, 66, ativo)

    kpis(p, [
        ("Carteira Auditoria", "Sub Carteira Aud", "Processos em Auditoria", NAVY),
        ("Carteira Aud Com a Equipe", "Sub Carteira Com a Equipe", "Com a Equipe", AZUL),
        ("Carteira Aud Com a Chefia", "Sub Carteira Com a Chefia", "Com a Chefia", VERDE),
        ("Carteira Aud Aguardando Auditado", "Sub Carteira Aguardando", "Aguardando Auditado", CINZA),
        ("Carteira Aud Dias Médios desde a Designação", "Sub Carteira Mov", "Dias Médios desde a Designação", VERMELHO),
        ("Carteira Monitoramento", "Sub Carteira Mon", "Ciclos de Monitoramento em Aberto", AMARELO),
    ], y=166)

    c = "fCarteira"
    y2, h2 = 288, 420
    w2 = 1100
    mat = matriz([AUDITOR, FUNCAO], [("Carteira Auditoria", "Trabalhos")],
                 "AUDITORIA · TRABALHOS POR AUDITOR E COM QUEM ESTÁ A PRÓXIMA AÇÃO", ordem_medida="Carteira Auditoria")
    mat["query"]["queryState"]["Columns"] = {"projections": [proj(col(c, "Com Quem"), active=True)]}
    p.add("mat_carteira", X0, y2, w2, h2, mat)
    p.add("bar_funcao", X0 + w2 + 10, y2, XMAX - X0 - w2 - 10, h2, grafico(
        "barChart", AUDITOR,
        [("Carteira Aud Coordenador", "Coordenador"), ("Carteira Aud Equipe", "Equipe")],
        "AUDITORIA · COORDENAÇÃO x EQUIPE POR AUDITOR", cores=[NAVY, AZUL],
        ordem=(med("Carteira Auditoria"), "Descending")))

    y3 = y2 + h2 + 10
    h3 = H - y3 - 8
    w3 = 1100
    p.add("lista_aud", X0, y3, w3, h3, tabela(
        [(col(c, "Auditor"), "Auditor"), (col(c, "Função"), "Função"), (col(c, "Nº PROA"), "Nº PROA"),
         (col("dProcesso", "Auditado"), "Auditado"), (col("dProcesso", "Eixo Temático"), "Eixo"),
         (col(c, "Fase"), "Fase"), (col(c, "Com Quem"), "Com quem"), (col(c, "Data Designação"), "Designação"),
         (col(c, "Dias desde a Designação"), "Dias desde a designação"),
         (col(c, "Dias desde a Última Movimentação"), "Dias desde a últ. movimentação")],
        "AUDITORIA · TRABALHOS EM ABERTO (mais parados no topo)",
        ordem=(col(c, "Dias desde a Última Movimentação"), "Descending")))
    m = "fDesignacoes"
    p.add("lista_mon", X0 + w3 + 10, y3, XMAX - X0 - w3 - 10, h3, tabela(
        [(col(m, "Auditor"), "Auditor"), (col(m, "Função"), "Função"), (col(m, "Ciclo"), "Ciclo"),
         (col(m, "Nº PROA"), "Nº PROA"), (col(m, "Status do Ciclo"), "Status do ciclo"),
         (col(m, "Dias desde a Designação"), "Dias desde a designação")],
        "MONITORAMENTO · CICLOS EM ABERTO", ordem=(col(m, "Dias desde a Designação"), "Descending")),
        filtros=[filtro_in(m, "Em Carteira", ["Sim"], "fEmCarteira")])
    return p


def pg_metodologia():
    p = Pagina("metodologia", "METODOLOGIA")
    p.nome_exib = "Metodologia"
    moldura(p, "geral", com_filtros=False)
    t, n, c = (lambda s: (s, st(13, NAVY, True))), (lambda s: (s, st(10, TEXTO, True))), (lambda s: (s, st(10)))
    w = (XMAX - X0 - 10) / 2
    p.add("texto_aud", X0, 92, w, H - 100, textbox([
        [t("Fonte")],
        [c("Planilha 'ESTUDO DOS PROCESSOS PARA ANÁLISE DO RDQA', aba PROCESSOS. Nomes padronizados pela lista de SERVIDORES (aba APOIO); "
           "quem está marcado como 'é auditor = Não' não entra nas contagens.")],
        [c(" ")],
        [t("Auditoria")],
        [n("Campos: "), c("Coordenador (14), Equipe (18), Data de Designação (17), Entrega do RAI (19), Entrega do RAF (21), "
                          "Qtde Matriz Qualidade RIA/RFA, Status (42).")],
        [n("Prazo do RAI: "), c("Data de Designação + 30 dias.")],
        [n("Prazo do RAF: "), c("Data de Designação + 60 dias (mesmo cálculo da coluna 22).")],
        [n("Não se aplica: "), c("sem data de entrega em processo ARQUIVADO ou FASE DE AUDITORIA FINALIZADA (fora das taxas).")],
        [n("Dias para entrega: "), c("Data de Entrega − Data de Designação. Média e mediana calculadas por relatório "
                                     "(não pesam o tamanho da equipe); dias negativos são ignorados.")],
        [n("Matrizes de Qualidade: "), c("total de matrizes ÷ relatórios avaliados (indicador de retrabalho).")],
        [c(" ")],
        [t("Situação (vale para as duas fases)")],
        [n("No prazo: "), c("entrega ≤ Data Limite.   "), n("Fora do prazo: "), c("entrega > Data Limite.")],
        [n("Pendente (vencida): "), c("sem entrega e Data Limite anterior à data da atualização.")],
        [n("Em andamento: "), c("sem entrega, ainda no prazo.   "), n("Sem prazo definido: "), c("sem data de designação.")],
        [c(" ")],
        [t("Filtro de Período")],
        [c("Auditoria: Data de Designação. Monitoramento: Data Inicial da Designação do ciclo. Os gráficos de evolução mensal usam a "
           "data de entrega (entregas) e a Data Limite (pendências vencidas).")],
        [c(" ")],
        [t("Filtros")],
        [c("Eixo Temático: agrupa as variações do campo 04 (ex.: Uti, Auditoria Aih → AIH). Sem eixo em Auditoria Especial = Solicitação Externa.")],
        [c("Auditores ativos: coluna 'Ativo?' da aba APOIO. Vem marcado em 'Sim'; limpe o filtro para incluir inativos e não cadastrados.")],
    ], fundo=BRANCO))
    p.add("texto_mon", X0 + w + 10, 92, w, H - 100, textbox([
        [t("Monitoramento")],
        [n("1º Ciclo: "), c("Coordenador (56), Equipe (57), Início (52), Fim (53), Relatório (55).")],
        [n("2º Ciclo: "), c("Coordenador (81), Equipe (82), Início (77), Fim (78), Relatório (80).")],
        [n("3º Ciclo: "), c("Coordenador (105), Equipe (106), Início (101), Fim (102), Relatório (104).")],
        [n("Prazo: "), c("Data Final da Designação + 30 dias. Sem relatório em ciclo arquivado ou encerrado = Não se aplica "
                         "(não conta como pendência).")],
        [n("Dias para entrega: "), c("Data do Relatório − Data Inicial da Designação.")],
        [c(" ")],
        [t("Indicadores")],
        [n("Designações: "), c("cada auditor em cada função de cada processo/ciclo conta 1 (equipe de 3 = 3 designações). "
                                "Usado nas tabelas por auditor; cartões e gráficos gerais contam processos/ciclos/relatórios uma vez só.")],
        [n("Taxa de Entrega: "), c("Entregues ÷ (Entregues + Pendências vencidas).")],
        [n("Taxa de Pontualidade: "), c("No prazo ÷ Entregues.")],
        [n("Taxa de Pendência Vencida: "), c("Pendências vencidas ÷ designações (auditoria: ÷ relatórios aplicáveis).")],
        [n("Dias de Atraso: "), c("entrega − Data Limite (entregas fora do prazo).")],
        [n("Índice de Produtividade (monitoramento): "), c("40% Taxa de Entrega + 40% Pontualidade + 20% Participação "
                                                          "(designações do auditor ÷ maior nº entre os auditores filtrados).")],
        [c(" ")],
        [t("Trabalhos em Andamento")],
        [n("Auditoria: "), c("processos com Status (42) diferente de Arquivado / Fase de auditoria finalizada. A fase e com quem "
                             "está a próxima ação (equipe, chefia ou auditado) vêm do Status.")],
        [n("Monitoramento: "), c("ciclos sem relatório e não arquivados/encerrados.")],
        [n("Posição de hoje: "), c("não segue o filtro de Período. Dias desde a última movimentação = hoje − data mais recente "
                                   "entre designação, RAI e RAF.")],
    ], fundo=BRANCO))
    return p


def main():
    paginas = [pg_resumo(), pg_carteira(), pg_auditoria(), pg_auditoria_detalhe(), pg_monitoramento(), pg_monit_auditor(),
               pg_monit_ciclo(), pg_monit_detalhe(), pg_metodologia()]

    def _forcar(func, caminho, _exc):  # OneDrive marca pastas como somente-leitura
        os.chmod(caminho, stat.S_IWRITE)
        func(caminho)

    PAGES.mkdir(parents=True, exist_ok=True)
    for item in PAGES.iterdir():
        if item.is_dir():
            shutil.rmtree(item, onexc=_forcar)
        else:
            item.unlink()
    for p in paginas:
        pdir = PAGES / p.id
        (pdir / "visuals").mkdir(parents=True)
        page = {"$schema": SCHEMA_PAGE, "name": p.id, "displayName": p.nome_exib, "displayOption": "FitToPage",
                "height": H, "width": W,
                "objects": {"outspace": [{"properties": {"color": COR(FUNDO)}}]}}
        (pdir / "page.json").write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")
        for v in p.visuais:
            vdir = pdir / "visuals" / v["name"]
            vdir.mkdir()
            (vdir / "visual.json").write_text(json.dumps(v, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = {"$schema": SCHEMA_PAGES, "pageOrder": [p.id for p in paginas], "activePageName": paginas[0].id}
    (PAGES / "pages.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(paginas)} páginas, {sum(len(p.visuais) for p in paginas)} visuais gerados em {PAGES}")


if __name__ == "__main__":
    main()
