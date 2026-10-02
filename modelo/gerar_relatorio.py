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


def donut_situacao():
    cat = col("fDesignacoes", "Situação")
    dp = []
    for sit, c in COR_SITUACAO.items():
        dp.append({"properties": {"fill": COR(c)}, "selector": {"data": [{"scopeId": {"Comparison": {
            "ComparisonKind": 0, "Left": cat, "Right": {"Literal": {"Value": f"'{sit}'"}}}}}]}})
    return {
        "visualType": "donutChart",
        "query": {"queryState": {
            "Category": {"projections": [proj(cat, active=True)]},
            "Y": {"projections": [proj(med("Designações"))]}},
            "sortDefinition": {"sort": [{"field": col("fDesignacoes", "Situação"), "direction": "Ascending"}]}},
        "objects": {
            "legend": [{"properties": {"show": B(True), "position": S("Right"), "fontSize": D(10)}}],
            "labels": [{"properties": {"show": B(True), "labelStyle": S("Percent of total"), "fontSize": D(9)}}],
            "dataPoint": dp,
        },
        "visualContainerObjects": container("DESIGNAÇÕES POR SITUAÇÃO"),
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
def moldura(p: Pagina, com_filtros=True):
    p.add("fundo", 0, 0, W, H, shape(FUNDO))
    p.add("sidebar", 0, 0, SIDEBAR, H, shape(NAVY))
    p.add("logo", 10, 18, SIDEBAR - 20, 70, textbox([
        [("DEASUS", st(18, BRANCO, True))],
        [("Produtividade", st(10, "#BFD0E6"))],
    ]))
    p.add("nav", 10, 110, SIDEBAR - 20, 430, {
        "visualType": "pageNavigator",
        "objects": {
            "layout": [{"properties": {"orientation": D(1), "cellPadding": D(8)}}],
            "shape": [{"properties": {"tileShape": S("rectangleRounded"), "roundEdge": L("6L")}, "selector": {"id": "default"}}],
            "text": [
                {"properties": {"fontColor": COR(BRANCO), "fontSize": D(11), "bold": B(True)}, "selector": {"id": "default"}},
                {"properties": {"fontColor": COR(NAVY), "fontSize": D(11), "bold": B(True)}, "selector": {"id": "selected"}},
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

    # Cabeçalho
    p.add("header", SIDEBAR, 0, W - SIDEBAR, 80, shape(NAVY))
    p.add("titulo", X0, 6, 1250, 70, textbox([
        [(p.titulo, st(20, BRANCO, True))],
        [("Designações, Relatórios Entregues e Cumprimento de Prazo · Monitoramentos (1º, 2º e 3º Ciclos)", st(11, "#BFD0E6"))],
    ]))
    p.add("atualizacao", W - 330, 18, 320, 46, card("Última Atualização", tam=12, cor=BRANCO, fundo=None, borda=False))

    if not com_filtros:
        return
    y, h = 90, 66
    x = X0
    p.add("f_periodo", x, y, 300, h, slicer(col("dCalendario", "Data"), "Período (Data Final da Designação)", "Periodo", "Between"))
    x += 310
    for chave, campo, tit in [
        ("f_ciclo", col("fDesignacoes", "Ciclo"), "Ciclo"),
        ("f_funcao", col("fDesignacoes", "Função"), "Função"),
        ("f_auditor", col("dAuditor", "Auditor"), "Auditor"),
        ("f_unidade", col("dAuditor", "Lotação"), "Unidade (Lotação)"),
        ("f_situacao", col("fDesignacoes", "Situação"), "Situação da Designação"),
    ]:
        filtros = None
        if chave == "f_auditor":
            filtros = [filtro_in("dAuditor", "Possui Designação", ["Sim"], "fPossuiDesig")]
        p.add(chave, x, y, 232, h, slicer(campo, tit, tit), filtros=filtros)
        x += 242
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


def kpis(p: Pagina, y=166, h=112):
    itens = [
        ("Designações", "Sub Designações", "Total de Designações", NAVY),
        ("Relatórios Entregues", "Sub Entregues", "Relatórios Entregues", AZUL),
        ("Entregues no Prazo", "Sub No Prazo", "Entregues no Prazo", VERDE),
        ("Entregues Fora do Prazo", "Sub Fora do Prazo", "Entregues Fora do Prazo", VERMELHO),
        ("Pendências Vencidas", "Sub Pendências Vencidas", "Pendências Vencidas", AMARELO),
        ("Dias Médios para Entrega", "Sub Prazo Médio", "Prazo Médio de Entrega (dias)", NAVY),
    ]
    gap = 10
    w = (XMAX - X0 - gap * (len(itens) - 1)) / len(itens)
    for i, (m, sub, tit, cor) in enumerate(itens):
        x = X0 + i * (w + gap)
        p.add(f"kpi_bg_{i}", x, y, w, h, shape(BRANCO, raio=8, borda=BORDA))
        p.add(f"kpi_bar_{i}", x, y, 6, h, shape(cor))
        p.add(f"kpi_{i}", x + 8, y + 2, w - 12, h - 34, card(m, tit, tam=26, cor=cor, fundo=None, borda=False))
        p.add(f"kpi_sub_{i}", x + 8, y + h - 34, w - 12, 30, card(sub, tam=9, cor=CINZA_TXT, fundo=None, borda=False))


# ---------------- Páginas ----------------
def pg_visao_geral():
    p = Pagina("visao_geral", "ANÁLISE DE PRODUTIVIDADE POR AUDITOR")
    p.nome_exib = "Visão Geral"
    moldura(p)
    kpis(p)
    y2, h2 = 288, 330
    p.add("donut", X0, y2, 440, h2, donut_situacao())
    p.add("evolucao", X0 + 450, y2, 770, h2, grafico(
        "columnChart", col("dCalendario", "Mês/Ano"),
        [("Entregas no Prazo (por Data Relatório)", "Entregues no prazo"),
         ("Entregas Fora do Prazo (por Data Relatório)", "Fora do prazo"),
         ("Pendências Vencidas (por Data Limite)", "Pendentes vencidos")],
        "EVOLUÇÃO DE ENTREGAS POR MÊS", cores=[VERDE, VERMELHO, AMARELO],
        ordem=(col("dCalendario", "Mês/Ano"), "Ascending")))
    xg = X0 + 1230
    wg = XMAX - xg
    p.add("taxas_bg", xg, y2, wg, h2, shape(BRANCO, raio=8, borda=BORDA))
    p.add("taxas_tit", xg + 8, y2 + 6, wg - 16, 34, textbox([[("TAXAS GERAIS", st(12, NAVY, True))]]))
    gw = (wg - 20) / 3
    for i, (m, t, c) in enumerate([("Taxa de Entrega", "Taxa de Entrega", AZUL),
                                   ("Taxa de Pontualidade", "Taxa de Pontualidade", AZUL),
                                   ("Taxa de Pendência Vencida", "Taxa de Pendência Vencida", VERMELHO)]):
        p.add(f"gauge_{i}", xg + 10 + i * gw, y2 + 50, gw, h2 - 60, gauge(m, t, c))

    y3, h3 = 628, 320
    p.add("matriz", X0, y3, 1220, h3, matriz(
        [col("dAuditor", "Auditor"), col("fDesignacoes", "Função")],
        [("Designações", "Designações"), ("Designações Encerradas", "Encerradas"), ("Relatórios Entregues", "Entregues"),
         ("Entregues no Prazo", "No Prazo"), ("Entregues Fora do Prazo", "Fora do Prazo"),
         ("Pendências Vencidas", "Pend. Vencidas"), ("Taxa de Entrega", "Taxa de Entrega"),
         ("Taxa de Pontualidade", "Taxa de Pontualidade"), ("Dias Médios para Entrega", "Média de Dias (Entrega)")],
        "DESEMPENHO POR AUDITOR · Visão consolidada (Coordenador + Equipe)", ordem_medida="Designações"))
    hh = (h3 - 10) / 2
    p.add("ciclo_barras", xg, y3, wg, hh, grafico(
        "clusteredBarChart", col("fDesignacoes", "Ciclo"),
        [("Designações", "Designações"), ("Relatórios Entregues", "Entregues")],
        "DESIGNAÇÕES POR CICLO", cores=[NAVY, VERDE_CLARO], ordem=(col("fDesignacoes", "Ciclo"), "Ascending")))
    p.add("ciclo_dias", xg, y3 + hh + 10, wg, hh, grafico(
        "clusteredColumnChart", col("fDesignacoes", "Ciclo"),
        [("Dias Médios para Entrega", "Dias médios")],
        "MÉDIA DE DIAS PARA ENTREGA POR CICLO", cores=[NAVY], legenda=False,
        ordem=(col("fDesignacoes", "Ciclo"), "Ascending")))

    y4 = y3 + h3 + 10
    h4 = H - y4 - 8
    p.add("como_calc", X0, y4, 1220, h4, textbox([
        [("COMO É CALCULADO   ", st(11, NAVY, True)),
         ("Prazo: ", st(9, TEXTO, True)), ("Data Final da Designação + 30 dias.   ", st(9)),
         ("Pontualidade: ", st(9, TEXTO, True)), ("relatório entregue até a Data Limite.   ", st(9)),
         ("Taxa de Entrega: ", st(9, TEXTO, True)), ("Entregues ÷ (Entregues + Pendências vencidas).   ", st(9)),
         ("Taxa de Pontualidade: ", st(9, TEXTO, True)), ("No prazo ÷ Entregues.", st(9))],
        [("Dias para entrega = Data do Relatório − Data Inicial da Designação. Cada membro da equipe conta uma designação. "
          "Pendente (vencida) = sem relatório e Data Limite já ultrapassada na data da atualização.", st(9, CINZA_TXT))],
    ], fundo=BRANCO))
    p.add("obs", xg, y4, wg, h4, textbox([
        [("ÍNDICE DE PRODUTIVIDADE", st(11, NAVY, True))],
        [("40% Entrega + 40% Pontualidade + 20% Participação. Ranking na página Por Auditor.", st(9, CINZA_TXT))],
    ], fundo=BRANCO))
    return p


def pg_auditor():
    p = Pagina("por_auditor", "PRODUTIVIDADE POR AUDITOR")
    p.nome_exib = "Por Auditor"
    moldura(p)
    y = 166
    h = H - y - 8
    p.add("matriz", X0, y, 1150, h, matriz(
        [col("dAuditor", "Auditor"), col("fDesignacoes", "Função")],
        [("Designações", "Designações"), ("Relatórios Entregues", "Entregues"),
         ("Entregues no Prazo", "No Prazo"), ("Entregues Fora do Prazo", "Fora do Prazo"),
         ("Relatórios Pendentes", "Pendências"), ("Pendências Vencidas", "Pend. Vencidas"),
         ("Taxa de Entrega", "Taxa de Entrega"), ("Taxa de Pontualidade", "Taxa de Pontualidade"),
         ("Dias Médios para Entrega", "Tempo Médio de Entrega"), ("Dias Médios de Atraso", "Dias Médios de Atraso"),
         ("Índice de Produtividade", "Índice"), ("Ranking Produtividade", "Ranking")],
        "DESEMPENHO POR AUDITOR (expanda para ver Coordenador x Equipe)", ordem_medida="Designações"))
    x2 = X0 + 1160
    w2 = XMAX - x2
    h2 = (h - 10) / 2
    p.add("ranking", x2, y, w2, h2, grafico(
        "clusteredBarChart", col("dAuditor", "Auditor"), [("Índice de Produtividade", "Índice")],
        "CLASSIFICAÇÃO POR ÍNDICE DE PRODUTIVIDADE", cores=[AZUL], legenda=False,
        ordem=(med("Índice de Produtividade"), "Descending")))
    p.add("por_funcao", x2, y + h2 + 10, w2, h2, grafico(
        "barChart", col("dAuditor", "Auditor"),
        [("Designações Coordenador", "Coordenador"), ("Designações Equipe", "Equipe")],
        "DESIGNAÇÕES POR AUDITOR E FUNÇÃO", cores=[NAVY, VERDE_CLARO],
        ordem=(med("Designações Coordenador"), "Descending")))
    return p


def pg_ciclo():
    p = Pagina("por_ciclo", "PRODUTIVIDADE POR CICLO")
    p.nome_exib = "Por Ciclo"
    moldura(p)
    kpis(p)
    y = 288
    h = (H - y - 18) / 2
    wl = 900
    ciclo = col("fDesignacoes", "Ciclo")
    ordem = (ciclo, "Ascending")
    p.add("desig_ent", X0, y, wl, h, grafico(
        "clusteredColumnChart", ciclo,
        [("Designações", "Designações"), ("Relatórios Entregues", "Entregues"), ("Pendências Vencidas", "Pend. vencidas")],
        "DESIGNAÇÕES E ENTREGAS POR CICLO", cores=[NAVY, VERDE_CLARO, AMARELO], ordem=ordem))
    p.add("funcao", X0 + wl + 10, y, XMAX - X0 - wl - 10, h, grafico(
        "columnChart", ciclo, [("Designações Coordenador", "Coordenador"), ("Designações Equipe", "Equipe")],
        "DESIGNAÇÕES POR FUNÇÃO (COORDENADOR x EQUIPE)", cores=[NAVY, VERDE_CLARO], ordem=ordem))
    y2 = y + h + 10
    p.add("taxas", X0, y2, wl, h, grafico(
        "clusteredColumnChart", ciclo, [("Taxa de Entrega", "Taxa de Entrega"), ("Taxa de Pontualidade", "Taxa de Pontualidade")],
        "TAXA DE ENTREGA E PONTUALIDADE POR CICLO", cores=[AZUL, VERDE], ordem=ordem))
    p.add("dias", X0 + wl + 10, y2, XMAX - X0 - wl - 10, h, grafico(
        "clusteredColumnChart", ciclo,
        [("Dias Médios para Entrega", "Dias médios p/ entrega"), ("Dias Médios de Atraso", "Dias médios de atraso")],
        "PRAZO MÉDIO DE ENTREGA E ATRASO POR CICLO (DIAS)", cores=[NAVY, VERMELHO], ordem=ordem))
    return p


def pg_pendencias():
    p = Pagina("pendencias", "PENDÊNCIAS E ATRASOS")
    p.nome_exib = "Pendências"
    moldura(p)
    y = 166
    h = H - y - 8
    wl = 560
    hh = (h - 10) / 2
    p.add("pend_aud", X0, y, wl, hh, grafico(
        "barChart", col("dAuditor", "Auditor"),
        [("Pendências Vencidas", "Vencidas"), ("Em Andamento", "Em andamento")],
        "RELATÓRIOS PENDENTES POR AUDITOR", cores=[AMARELO, CINZA],
        ordem=(med("Pendências Vencidas"), "Descending")))
    p.add("fora_aud", X0, y + hh + 10, wl, hh, grafico(
        "barChart", col("dAuditor", "Auditor"), [("Entregues Fora do Prazo", "Fora do prazo")],
        "ENTREGAS FORA DO PRAZO POR AUDITOR", cores=[VERMELHO], legenda=False,
        ordem=(med("Entregues Fora do Prazo"), "Descending")))
    f = "fDesignacoes"
    p.add("lista", X0 + wl + 10, y, XMAX - X0 - wl - 10, h, tabela(
        [(col(f, "Situação"), "Situação"), (col(f, "Auditor"), "Auditor"), (col(f, "Função"), "Função"),
         (col(f, "Nº PROA"), "Nº PROA"), (col(f, "Ciclo"), "Ciclo"), (col("dProcesso", "Auditado"), "Auditado"),
         (col(f, "Data Final Designação"), "Data Final Designação"), (col(f, "Data Limite"), "Data Limite"),
         (col(f, "Data Relatório"), "Data Relatório"), (col(f, "Dias de Atraso"), "Dias de Atraso")],
        "DESIGNAÇÕES PENDENTES OU ENTREGUES FORA DO PRAZO", ordem=(col(f, "Dias de Atraso"), "Descending")),
        filtros=[filtro_in(f, "Situação", ["Pendente (vencida)", "Em andamento", "Fora do prazo"], "fSitPend")])
    return p


def pg_detalhe():
    p = Pagina("detalhamento", "DETALHAMENTO DAS DESIGNAÇÕES")
    p.nome_exib = "Detalhamento"
    moldura(p)
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
        "TODAS AS DESIGNAÇÕES (use os filtros acima)", ordem=(col(f, "Data Final Designação"), "Descending")))
    return p


def pg_metodologia():
    p = Pagina("metodologia", "METODOLOGIA")
    p.nome_exib = "Metodologia"
    moldura(p, com_filtros=False)
    t, n, c = (lambda s: (s, st(14, NAVY, True))), (lambda s: (s, st(11, TEXTO, True))), (lambda s: (s, st(11)))
    p.add("texto", X0, 100, XMAX - X0, H - 110, textbox([
        [t("Fonte")],
        [c("Planilha 'ESTUDO DOS PROCESSOS PARA ANÁLISE DO RDQA', aba PROCESSOS. Auditores conforme lista de SERVIDORES (aba APOIO).")],
        [c(" ")],
        [t("Campos utilizados por ciclo")],
        [n("1º Ciclo: "), c("Coordenador (56), Equipe (57), Data Inicial Designação (52), Data Final Designação (53), Data Relatório (55).")],
        [n("2º Ciclo: "), c("Coordenador (81), Equipe (82), Data Inicial Designação (77), Data Final Designação (78), Data Relatório (80).")],
        [n("3º Ciclo: "), c("Coordenador (105), Equipe (106), Data Inicial Designação (101), Data Final Designação (102), Data Relatório (104).")],
        [c(" ")],
        [t("Regras")],
        [n("Data Limite: "), c("Data Final da Designação + 30 dias.")],
        [n("No prazo: "), c("Data do Relatório ≤ Data Limite.   "), n("Fora do prazo: "), c("Data do Relatório > Data Limite.")],
        [n("Pendente (vencida): "), c("sem data de relatório e Data Limite anterior à data da atualização.   "),
         n("Em andamento: "), c("sem relatório, ainda no prazo.")],
        [n("Sem prazo definido: "), c("designação sem Data Final informada (fora das taxas).")],
        [c(" ")],
        [t("Indicadores")],
        [n("Designações: "), c("cada auditor em cada função de cada processo/ciclo conta 1 (equipe de 3 = 3 designações).")],
        [n("Taxa de Entrega: "), c("Entregues ÷ (Entregues + Pendências vencidas).   "), n("Taxa de Pontualidade: "), c("No prazo ÷ Entregues.")],
        [n("Taxa de Pendência Vencida: "), c("Pendências vencidas ÷ Designações.")],
        [n("Dias para Entrega: "), c("Data do Relatório − Data Inicial da Designação.   "),
         n("Dias de Atraso: "), c("Data do Relatório − Data Limite (entregas fora do prazo).")],
        [n("Índice de Produtividade: "), c("40% Taxa de Entrega + 40% Taxa de Pontualidade + 20% Participação "
                                           "(designações do auditor ÷ maior nº de designações entre os auditores filtrados).")],
        [c(" ")],
        [t("Filtro de Período")],
        [c("Filtra pela Data Final da Designação. O gráfico de evolução mensal usa a Data do Relatório (entregas) "
           "e a Data Limite (pendências vencidas).")],
    ], fundo=BRANCO))
    return p


def main():
    paginas = [pg_visao_geral(), pg_auditor(), pg_ciclo(), pg_pendencias(), pg_detalhe(), pg_metodologia()]
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
