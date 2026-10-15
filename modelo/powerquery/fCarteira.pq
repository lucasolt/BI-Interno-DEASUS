// Carteira atual da fase de Auditoria: processo em aberto x Função x Auditor, com fase e com quem está a próxima ação.
let
    Hoje = Date.From(DateTime.LocalNow()),
    Encerrados = {"arquivado", "fase de auditoria finalizada"},
    // 1 linha por Nº PROA x Função x Auditor (fAuditoria tem uma linha para RAI e outra para RAF)
    Agrupado = Table.Group(fAuditoria, {"Nº PROA", "Função", "Auditor", "Data Designação", "Status do Processo"}, {
        {"Data RAI", each List.Max(Table.SelectRows(_, each [Relatório] = "RAI")[Data Entrega]), type nullable date},
        {"Data RAF", each List.Max(Table.SelectRows(_, each [Relatório] = "RAF")[Data Entrega]), type nullable date}
    }),
    ComChave = Table.AddColumn(Agrupado, "StatusChave", each fxNormalizaNome([Status do Processo]), type nullable text),
    // processos encerrados não estão na carteira
    Abertos = Table.SelectRows(ComChave, each not List.Contains(Encerrados, [StatusChave])),
    Fases = Table.Buffer(MapaFases),
    ComFase = Table.NestedJoin(Abertos, {"StatusChave"}, Fases, {"StatusChave"}, "F", JoinKind.LeftOuter),
    Expandido = Table.ExpandTableColumn(ComFase, "F", {"Fase", "Fase Ordem", "Com Quem"}),
    // status fora do de-para: mostra o próprio status e fica "A classificar" (incluir em MapaFases)
    Renomeado = Table.RenameColumns(Expandido, {{"Fase", "FaseMapa"}, {"Fase Ordem", "OrdemMapa"}, {"Com Quem", "QuemMapa"}}),
    ComFaseFinal = Table.AddColumn(Renomeado, "Fase", each
        if [FaseMapa] <> null then [FaseMapa]
        else if [Status do Processo] = null then "Sem status"
        else Text.Proper([Status do Processo]), type text),
    ComOrdemFinal = Table.AddColumn(ComFaseFinal, "Fase Ordem", each [OrdemMapa] ?? 99, Int64.Type),
    ComQuemFinal = Table.AddColumn(ComOrdemFinal, "Com Quem", each [QuemMapa] ?? "A classificar", type text),
    Tabela = Table.RemoveColumns(ComQuemFinal, {"FaseMapa", "OrdemMapa", "QuemMapa", "StatusChave"}),
    ComOrdemQuem = Table.AddColumn(Tabela, "Com Quem Ordem", each
        List.PositionOf({"Com a equipe", "Com a chefia", "Aguardando auditado", "Fora da equipe", "A classificar"}, [Com Quem]) + 1,
        Int64.Type),
    ComDias = Table.AddColumn(ComOrdemQuem, "Dias desde a Designação", each
        if [Data Designação] = null then null else Duration.Days(Hoje - [Data Designação]), Int64.Type),
    // aproximação de "tempo na fase": última data registrada entre designação, RAI e RAF
    ComUltima = Table.AddColumn(ComDias, "Última Movimentação", each
        List.Max(List.RemoveNulls({[Data Designação], [Data RAI], [Data RAF]})), type nullable date),
    ComDiasUltima = Table.AddColumn(ComUltima, "Dias desde a Última Movimentação", each
        if [Última Movimentação] = null then null else Duration.Days(Hoje - [Última Movimentação]), Int64.Type),
    ComId = Table.AddColumn(ComDiasUltima, "ID Trabalho", each [Nº PROA] & " | " & [Função] & " | " & [Auditor], type text),
    Tipos = Table.TransformColumnTypes(ComId, {
        {"Nº PROA", type text}, {"Função", type text}, {"Auditor", type text}, {"Data Designação", type nullable date},
        {"Status do Processo", type nullable text}, {"Fase", type text}, {"Fase Ordem", Int64.Type}, {"Com Quem", type text}}),
    Final = Table.SelectColumns(Tipos, {
        "ID Trabalho", "Nº PROA", "Função", "Auditor", "Fase", "Fase Ordem", "Com Quem", "Com Quem Ordem",
        "Status do Processo", "Data Designação", "Data RAI", "Data RAF", "Última Movimentação",
        "Dias desde a Designação", "Dias desde a Última Movimentação"})
in
    Final
