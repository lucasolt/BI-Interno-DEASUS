// Fato de designações: 1 linha por Nº PROA x Ciclo x Função x Auditor.
// Regras (PEDIDO.md):
//   Campos por ciclo (dictDadosDep) -> "1C - ...", "2C - ...", "3C - ..." (códigos 52-65 | 77-89 | 101-113)
//   Data Limite = Data Final da Designação + PrazoPadraoDias (30)
//   No prazo: Relatório <= Limite | Fora do prazo: Relatório > Limite
//   Sem relatório: "Pendente (vencida)" se hoje > Limite, senão "Em andamento"
let
    Origem = stgProcessos,

    Ciclos = {[Ciclo = 1, Prefixo = "1C - "], [Ciclo = 2, Prefixo = "2C - "], [Ciclo = 3, Prefixo = "3C - "]},
    CamposCiclo = {"Data Inicial Designação", "Data Final Designação", "Nº Relatório",
                   "Data Relatório", "Coordenador", "Equipe", "Status Atual"},
    NomesPadrao = {"Nº PROA", "Data Inicial Designação", "Data Final Designação", "Nº Relatório",
                   "Data Relatório", "Coordenador", "EquipeTexto", "Status do Ciclo"},

    // ---- 1. Empilha os 3 ciclos (largo -> longo) ----
    PorCiclo = List.Transform(Ciclos, (c) =>
        let
            Sel = Table.SelectColumns(Origem, {"012 - Nº PROA"} & List.Transform(CamposCiclo, each c[Prefixo] & _)),
            Ren = Table.RenameColumns(Sel, List.Zip({Table.ColumnNames(Sel), NomesPadrao})),
            ComCiclo = Table.AddColumn(Ren, "Ciclo Nº", each c[Ciclo], Int64.Type)
        in
            ComCiclo),
    Empilhado = Table.Combine(PorCiclo),

    // ---- 2. Limpeza de textos ("-" e vazio viram null; datas já chegam tipadas pelo dicionário) ----
    ParaTexto = (v as any) as nullable text =>
        let t = if v = null then null else Text.Trim(Text.From(v))
        in if t = null or t = "" or t = "-" then null else t,
    Tipado = Table.TransformColumns(Empilhado, {
        {"Nº PROA", ParaTexto, type text},
        {"Nº Relatório", ParaTexto, type nullable text},
        {"Coordenador", ParaTexto, type nullable text},
        {"EquipeTexto", ParaTexto, type nullable text},
        {"Status do Ciclo", ParaTexto, type nullable text}
    }),

    // Só ciclos com designação (coordenador, equipe ou data final preenchidos)
    ComDesignacao = Table.SelectRows(Tipado, each
        [Coordenador] <> null or [EquipeTexto] <> null or [Data Final Designação] <> null),

    // ---- 3. Participantes e nome oficial (funções compartilhadas com fAuditoria) ----
    ComParticipantes = Table.AddColumn(ComDesignacao, "Participantes", each fxParticipantes([Coordenador], [EquipeTexto])),
    Expandido = Table.ExpandRecordColumn(
        Table.ExpandListColumn(Table.RemoveColumns(ComParticipantes, {"Coordenador", "EquipeTexto"}), "Participantes"),
        "Participantes", {"Função", "Nome"}),
    ComAuditor = Table.AddColumn(Expandido, "Auditor", each fxAuditorOficial([Nome]), type text),
    SemNomeOriginal = Table.RenameColumns(ComAuditor, {{"Nome", "Nome na Planilha"}}),
    // mesma pessoa repetida na mesma função do mesmo ciclo conta uma vez
    SemDuplicadas = Table.Distinct(SemNomeOriginal, {"Nº PROA", "Ciclo Nº", "Função", "Auditor"}),

    // ---- 4. Prazo e classificação ----
    Hoje = Date.From(DateTime.LocalNow()),
    ComLimite = Table.AddColumn(SemDuplicadas, "Data Limite", each
        if [Data Final Designação] = null then null else Date.AddDays([Data Final Designação], PrazoPadraoDias),
        type nullable date),
    ComSituacao = Table.AddColumn(ComLimite, "Situação", each
        if [Data Limite] = null then "Sem prazo definido"
        else if [Data Relatório] <> null then (if [Data Relatório] <= [Data Limite] then "No prazo" else "Fora do prazo")
        else if Hoje > [Data Limite] then "Pendente (vencida)"
        else "Em andamento",
        type text),
    ComOrdemSituacao = Table.AddColumn(ComSituacao, "Situação Ordem", each
        List.PositionOf({"No prazo", "Fora do prazo", "Pendente (vencida)", "Em andamento", "Sem prazo definido"}, [Situação]) + 1,
        Int64.Type),
    ComEntregue = Table.AddColumn(ComOrdemSituacao, "Entregue", each
        if [Data Relatório] <> null then "Entregue" else "Não entregue", type text),
    ComDiasEntrega = Table.AddColumn(ComEntregue, "Dias para Entrega", each
        if [Data Relatório] = null or [Data Inicial Designação] = null then null
        else Duration.Days([Data Relatório] - [Data Inicial Designação]),
        Int64.Type),
    ComDiasAtraso = Table.AddColumn(ComDiasEntrega, "Dias de Atraso", each
        if [Situação] = "Fora do prazo" then Duration.Days([Data Relatório] - [Data Limite])
        else if [Situação] = "Pendente (vencida)" then Duration.Days(Hoje - [Data Limite])
        else null,
        Int64.Type),
    ComAlerta = Table.AddColumn(ComDiasAtraso, "Alerta de Qualidade", each
        if [Auditor] = "(Não informado)" then "Auditor não informado"
        else if [Data Final Designação] = null then "Sem Data Final de Designação"
        else if [Data Relatório] <> null and [Data Inicial Designação] <> null and [Data Relatório] < [Data Inicial Designação]
            then "Relatório anterior ao início da designação"
        else null,
        type nullable text),

    // ---- 5. Colunas de apoio ----
    ComCiclo = Table.AddColumn(ComAlerta, "Ciclo", each Text.From([Ciclo Nº]) & "º Ciclo", type text),
    ComFuncaoOrdem = Table.AddColumn(ComCiclo, "Função Ordem", each if [Função] = "Coordenador" then 1 else 2, Int64.Type),
    ComId = Table.AddColumn(ComFuncaoOrdem, "ID Designação", each [Nº PROA] & " | " & [Ciclo], type text),
    ComRef = Table.AddColumn(ComId, "Data de Referência", each Hoje, type date),
    Tipos = Table.TransformColumnTypes(ComRef, {{"Função", type text}, {"Nome na Planilha", type nullable text}}),

    Final = Table.SelectColumns(Tipos, {
        "ID Designação", "Nº PROA", "Ciclo", "Ciclo Nº", "Função", "Função Ordem", "Auditor", "Nome na Planilha",
        "Data Inicial Designação", "Data Final Designação", "Data Limite", "Data Relatório", "Nº Relatório",
        "Situação", "Situação Ordem", "Entregue", "Dias para Entrega", "Dias de Atraso",
        "Status do Ciclo", "Alerta de Qualidade", "Data de Referência"})
in
    Final
