// Monitoramentos em aberto (regra do Painel: monitorável e Status GERAL 01 a 06) x participantes do ciclo atual.
let
    Origem = stgProcessos,
    Col = (codigo as text) as text =>
        List.First(List.Select(Table.ColumnNames(Origem), each Text.StartsWith(_, "(" & codigo & ")"))),
    Sel = Table.SelectColumns(Origem, {Col("12"), Col("46"), Col("60"), Col("117"), Col("118"), Col("119")}),
    Ren = Table.RenameColumns(Sel, List.Zip({Table.ColumnNames(Sel),
        {"Nº PROA", "Recebimento Ofício", "Reclassificação", "Ciclo Atual", "Status Geral", "Data do Status"}})),
    ParaTexto = (v as any) as nullable text =>
        let t = if v = null then null else Text.Trim(Text.From(v))
        in if t = null or t = "" or t = "-" then null else t,
    ParaData = (v as any) as nullable date =>
        if v = null then null
        else if v is date then v
        else if v is datetime then Date.From(v)
        else if v is number then Date.From(v)
        else try Date.FromText(Text.Trim(Text.From(v)), [Culture = "pt-BR"]) otherwise null,
    Tipado = Table.TransformColumns(Ren, {
        {"Nº PROA", ParaTexto, type text}, {"Recebimento Ofício", ParaData, type nullable date},
        {"Reclassificação", ParaData, type nullable date}, {"Ciclo Atual", ParaTexto, type nullable text},
        {"Status Geral", ParaTexto, type nullable text}, {"Data do Status", ParaData, type nullable date}}),

    // mesma regra do Painel de Auditorias: monitorável (ofício recebido e não reclassificado)
    // e Status GERAL (118) com prefixo 01 a 06 = "Ciclo ativo"
    Prefixo = (t as nullable text) as nullable number =>
        if t = null or not Text.Contains(t, " - ") then null
        else try Number.From(Text.BeforeDelimiter(t, " - ")) otherwise null,
    Abertos = Table.SelectRows(Tipado, each
        [Reclassificação] = null and [Recebimento Ofício] <> null
        and Prefixo([Status Geral]) <> null and Prefixo([Status Geral]) < 7),
    ComCicloNo = Table.AddColumn(Abertos, "Ciclo Nº", each
        try Number.From(Text.Select([Ciclo Atual] ?? "", {"0".."9"})) otherwise null, Int64.Type),

    // participantes do ciclo atual (designação do monitoramento); sem designação = linha "(Sem designação)"
    Designados = Table.SelectColumns(fDesignacoes, {"Nº PROA", "Ciclo Nº", "Função", "Auditor", "Data Inicial Designação", "Data Relatório"}),
    Juntado = Table.NestedJoin(ComCicloNo, {"Nº PROA", "Ciclo Nº"}, Designados, {"Nº PROA", "Ciclo Nº"}, "D", JoinKind.LeftOuter),
    Expandido = Table.ExpandTableColumn(Juntado, "D", {"Função", "Auditor", "Data Inicial Designação", "Data Relatório"}),
    SemDesignacao = Table.ReplaceValue(Expandido, null, "(Sem designação)", Replacer.ReplaceValue, {"Auditor"}),

    Hoje = Date.From(DateTime.LocalNow()),
    ComQuem = Table.AddColumn(SemDesignacao, "Com Quem", each
        let n = Prefixo([Status Geral]) in
        if n = 1 then "Aguardando auditado"
        else if n = 2 or n = 4 then "Com a equipe"   // 04: coordenador já designado
        else if n = 6 then "Com a chefia"            // 06: conclusão técnica do ciclo pela chefia
        else "A classificar", type text),
    ComQuemOrdem = Table.AddColumn(ComQuem, "Com Quem Ordem", each
        List.PositionOf({"Com a equipe", "Com a chefia", "Aguardando auditado", "Fora da equipe", "A classificar"}, [Com Quem]) + 1,
        Int64.Type),
    ComOrdem = Table.AddColumn(ComQuemOrdem, "Status Ordem", each Prefixo([Status Geral]), Int64.Type),
    ComDiasStatus = Table.AddColumn(ComOrdem, "Dias no Status Atual", each
        if [Data do Status] = null then null else Duration.Days(Hoje - [Data do Status]), Int64.Type),
    ComDiasDesig = Table.AddColumn(ComDiasStatus, "Dias desde a Designação", each
        if [Data Inicial Designação] = null then null else Duration.Days(Hoje - [Data Inicial Designação]), Int64.Type),
    ComCiclo = Table.AddColumn(ComDiasDesig, "Ciclo", each if [Ciclo Nº] = null then [Ciclo Atual] else Text.From([Ciclo Nº]) & "º Ciclo", type nullable text),
    Tipos = Table.TransformColumnTypes(ComCiclo, {{"Função", type nullable text}, {"Auditor", type text},
        {"Data Inicial Designação", type nullable date}, {"Data Relatório", type nullable date}}),
    Final = Table.SelectColumns(Tipos, {"Nº PROA", "Ciclo", "Ciclo Nº", "Função", "Auditor", "Status Geral", "Status Ordem",
        "Com Quem", "Com Quem Ordem", "Data do Status", "Dias no Status Atual", "Data Inicial Designação",
        "Data Relatório", "Dias desde a Designação"})
in
    Final
