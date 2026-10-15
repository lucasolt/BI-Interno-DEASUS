// Dimensão de processos (1 linha por Nº PROA) com atributos para filtros/evoluções futuras (CRS etc.).
// Somente processos com designação de auditoria ou de monitoramento.
let
    Origem = stgProcessos,
    Col = (codigo as text) as text =>
        List.First(List.Select(Table.ColumnNames(Origem), each Text.StartsWith(_, "(" & codigo & ")"))),
    Mapa = {
        {Col("12"), "Nº PROA"},
        {"Monitoramento", "Classificação Monitoramento"},
        {Col("03"), "Tipo de Auditoria"},
        {Col("04"), "Eixo"},
        {Col("06"), "Auditado"},
        {Col("07"), "Tipo de Estabelecimento"},
        {Col("08"), "Município"},
        {Col("09"), "CRS"},
        {Col("10"), "Região de Saúde"},
        {Col("11"), "Macrorregião"},
        {Col("117"), "Ciclo Atual"},
        {Col("118"), "Status Geral do Monitoramento"}
    },
    Sel = Table.SelectColumns(Origem, List.Transform(Mapa, each _{0})),
    Ren = Table.RenameColumns(Sel, Mapa),
    ParaTexto = (v as any) as nullable text =>
        let t = if v = null then null else Text.Trim(Text.From(v))
        in if t = null or t = "" or t = "-" then null else t,
    Limpo = Table.TransformColumns(Ren, List.Transform(List.Transform(Mapa, each _{1}), (n) => {n, ParaTexto, type nullable text})),
    ProasFato = List.Buffer(List.Distinct(fDesignacoes[Nº PROA] & fAuditoria[Nº PROA])),
    ComDesignacao = Table.SelectRows(Limpo, each List.Contains(ProasFato, [Nº PROA])),
    Distintos = Table.Distinct(ComDesignacao, {"Nº PROA"}),

    // ---- Eixo Temático (agrupa variações do campo 04 via MapaEixos) ----
    ComEixoBase = Table.AddColumn(Distintos, "EixoBase", each
        let e = if [Eixo] = null then null else Text.Trim(Text.Replace([Eixo], Character.FromNumber(160), " "))
        in if e = null and Text.Lower([Tipo de Auditoria] ?? "") = "auditoria especial" then "Solicitação Externa" else e,
        type nullable text),
    // eixos fora do de-para ficam em "título" (ex.: ATENÇÃO BÁSICA -> Atenção Básica)
    DicCasing = #table(type table [Rename = text, Incluir = number, Type = text, Casing = text], {{"EixoBase", 1, "texto", "titulo"}}),
    EixoTitulo = fxAplicarCasing(ComEixoBase, DicCasing),
    Mapa = Record.FromList(MapaEixos[Eixo Temático], MapaEixos[EixoChave]),
    ComEixoTematico = Table.AddColumn(EixoTitulo, "Eixo Temático", each
        let k = fxNormalizaNome([EixoBase]) in
        if k = null then "(Não informado)" else Record.FieldOrDefault(Mapa, k, [EixoBase]),
        type text),
    Final = Table.RemoveColumns(ComEixoTematico, {"EixoBase"})
in
    Final
