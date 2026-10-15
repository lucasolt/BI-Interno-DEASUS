// Fato da fase de AUDITORIA: 1 linha por Nº PROA x Relatório (RAI/RAF) x Função x Auditor.
// Campos: Coordenador (14), Equipe (18), Data de Designação (17), Nº RAI (15), Entrega RAI (19),
//         Nº RAF (20), Entrega RAF (21), Qtde Matriz Qualidade RIA/RFA, Status (42).
// Prazos: RAI = Designação + PrazoRAIDias (30) | RAF = Designação + PrazoRAFDias (60).
// Sem data de entrega em processo ARQUIVADO / FASE DE AUDITORIA FINALIZADA -> "Não se aplica".
let
    Origem = stgProcessos,
    Col = (codigo as text) as text =>
        List.First(List.Select(Table.ColumnNames(Origem), each Text.StartsWith(_, "(" & codigo & ")"))),
    Mapa = {
        {Col("12"), "Nº PROA"}, {Col("14"), "Coordenador"}, {Col("18"), "EquipeTexto"},
        {Col("17"), "Data Designação"}, {Col("15"), "Nº RAI"}, {Col("19"), "Data RAI"},
        {Col("20"), "Nº RAF"}, {Col("21"), "Data RAF"},
        {"Qtde Martiz Qualidade RIA", "Matriz RAI"}, {"Qtde Martiz Qualidade RFA", "Matriz RAF"},
        {Col("42"), "Status do Processo"}
    },
    Sel = Table.RenameColumns(Table.SelectColumns(Origem, List.Transform(Mapa, each _{0})), Mapa),

    ParaTexto = (v as any) as nullable text =>
        let t = if v = null then null else Text.Trim(Text.From(v))
        in if t = null or t = "" or t = "-" then null else t,
    ParaData = (v as any) as nullable date =>
        if v = null then null
        else if v is date then v
        else if v is datetime then Date.From(v)
        else if v is number then Date.From(v)
        else try Date.FromText(Text.Trim(Text.From(v)), [Culture = "pt-BR"]) otherwise null,
    ParaNumero = (v as any) as nullable number =>
        if v = null then null else if v is number then v else try Number.From(Text.Trim(Text.From(v))) otherwise null,
    Tipado = Table.TransformColumns(Sel, {
        {"Nº PROA", ParaTexto, type text}, {"Coordenador", ParaTexto, type nullable text},
        {"EquipeTexto", ParaTexto, type nullable text}, {"Data Designação", ParaData, type nullable date},
        {"Nº RAI", ParaTexto, type nullable text}, {"Data RAI", ParaData, type nullable date},
        {"Nº RAF", ParaTexto, type nullable text}, {"Data RAF", ParaData, type nullable date},
        {"Matriz RAI", ParaNumero, type nullable number}, {"Matriz RAF", ParaNumero, type nullable number},
        {"Status do Processo", ParaTexto, type nullable text}
    }),
    ComDesignacao = Table.SelectRows(Tipado, each [Data Designação] <> null or [Coordenador] <> null),

    // Participantes
    ComParticipantes = Table.AddColumn(ComDesignacao, "Participantes", each fxParticipantes([Coordenador], [EquipeTexto])),
    Expandido = Table.ExpandRecordColumn(
        Table.ExpandListColumn(Table.RemoveColumns(ComParticipantes, {"Coordenador", "EquipeTexto"}), "Participantes"),
        "Participantes", {"Função", "Nome"}),
    ComAuditor = Table.AddColumn(Expandido, "Auditor", each fxAuditorOficial([Nome]), type text),
    SemDuplicadas = Table.Distinct(Table.RenameColumns(ComAuditor, {{"Nome", "Nome na Planilha"}}), {"Nº PROA", "Função", "Auditor"}),

    // Um registro por relatório (RAI e RAF)
    ComRelatorios = Table.AddColumn(SemDuplicadas, "Rel", each {
        [Relatório = "RAI", #"Relatório Ordem" = 1, Prazo = PrazoRAIDias, #"Data Entrega" = [Data RAI],
         #"Nº Relatório" = [Nº RAI], #"Matrizes de Qualidade" = [Matriz RAI]],
        [Relatório = "RAF", #"Relatório Ordem" = 2, Prazo = PrazoRAFDias, #"Data Entrega" = [Data RAF],
         #"Nº Relatório" = [Nº RAF], #"Matrizes de Qualidade" = [Matriz RAF]]
    }),
    PorRelatorio = Table.ExpandRecordColumn(Table.ExpandListColumn(ComRelatorios, "Rel"), "Rel",
        {"Relatório", "Relatório Ordem", "Prazo", "Data Entrega", "Nº Relatório", "Matrizes de Qualidade"}),

    // Prazo e classificação
    Hoje = Date.From(DateTime.LocalNow()),
    Encerrados = {"ARQUIVADO", "FASE DE AUDITORIA FINALIZADA"},
    ComLimite = Table.AddColumn(PorRelatorio, "Data Limite", each
        if [Data Designação] = null then null else Date.AddDays([Data Designação], [Prazo]), type nullable date),
    ComSituacao = Table.AddColumn(ComLimite, "Situação", each
        if [Data Limite] = null then "Sem prazo definido"
        else if [Data Entrega] <> null then (if [Data Entrega] <= [Data Limite] then "No prazo" else "Fora do prazo")
        else if List.Contains(Encerrados, Text.Upper([Status do Processo] ?? "")) then "Não se aplica"
        else if Hoje > [Data Limite] then "Pendente (vencida)"
        else "Em andamento",
        type text),
    ComDiasEntrega = Table.AddColumn(ComSituacao, "Dias para Entrega", each
        if [Data Entrega] = null or [Data Designação] = null then null else Duration.Days([Data Entrega] - [Data Designação]),
        Int64.Type),
    ComDiasAtraso = Table.AddColumn(ComDiasEntrega, "Dias de Atraso", each
        if [Situação] = "Fora do prazo" then Duration.Days([Data Entrega] - [Data Limite])
        else if [Situação] = "Pendente (vencida)" then Duration.Days(Hoje - [Data Limite])
        else null,
        Int64.Type),
    ComAlerta = Table.AddColumn(ComDiasAtraso, "Alerta de Qualidade", each
        if [Auditor] = "(Não informado)" then "Auditor não informado"
        else if [Data Designação] = null then "Sem Data de Designação"
        else if [Data Entrega] <> null and [Data Entrega] < [Data Designação] then "Entrega anterior à designação"
        else if [Relatório] = "RAF" and [Data Entrega] <> null and [Data RAI] <> null and [Data Entrega] < [Data RAI]
            then "RAF anterior ao RAI"
        else if [Relatório] = "RAF" and [Data Entrega] <> null and [Data RAI] = null then "RAF sem data de RAI"
        else null,
        type nullable text),

    ComId = Table.AddColumn(ComAlerta, "ID Relatório", each [Nº PROA] & " | " & [Relatório], type text),
    ComRef = Table.AddColumn(ComId, "Data de Referência", each Hoje, type date),
    Tipos = Table.TransformColumnTypes(ComRef, {
        {"Função", type text}, {"Nome na Planilha", type nullable text}, {"Relatório", type text},
        {"Relatório Ordem", Int64.Type}, {"Data Entrega", type nullable date}, {"Nº Relatório", type nullable text},
        {"Matrizes de Qualidade", Int64.Type}}),

    Final = Table.SelectColumns(Tipos, {
        "ID Relatório", "Nº PROA", "Relatório", "Relatório Ordem", "Função", "Auditor", "Nome na Planilha",
        "Data Designação", "Data Limite", "Data Entrega", "Nº Relatório", "Situação",
        "Dias para Entrega", "Dias de Atraso", "Matrizes de Qualidade", "Status do Processo",
        "Alerta de Qualidade", "Data de Referência"})
in
    Final
