// Fato de designações: 1 linha por Nº PROA x Ciclo x Função x Auditor.
// Regras (PEDIDO.md):
//   Campos por ciclo -> 1º: 52/53/55/56/57 | 2º: 77/78/80/81/82 | 3º: 101/102/104/105/106
//   Data Limite = Data Final da Designação + PrazoPadraoDias (30)
//   No prazo: Relatório <= Limite | Fora do prazo: Relatório > Limite
//   Sem relatório: "Pendente (vencida)" se hoje > Limite, senão "Em andamento"
let
    Origem = stgProcessos,
    Col = (codigo as text) as text =>
        List.First(List.Select(Table.ColumnNames(Origem), each Text.StartsWith(_, "(" & codigo & ")"))),

    Ciclos = {
        [Ciclo = 1, Ini = "52",  Fim = "53",  NRel = "54",  Rel = "55",  Coord = "56",  Equipe = "57",  Status = "65"],
        [Ciclo = 2, Ini = "77",  Fim = "78",  NRel = "79",  Rel = "80",  Coord = "81",  Equipe = "82",  Status = "89"],
        [Ciclo = 3, Ini = "101", Fim = "102", NRel = "103", Rel = "104", Coord = "105", Equipe = "106", Status = "113"]
    },
    NomesPadrao = {"Nº PROA", "Data Inicial Designação", "Data Final Designação", "Nº Relatório",
                   "Data Relatório", "Coordenador", "EquipeTexto", "Status do Ciclo"},

    // ---- 1. Empilha os 3 ciclos (largo -> longo) ----
    PorCiclo = List.Transform(Ciclos, (c) =>
        let
            Sel = Table.SelectColumns(Origem, {Col("12"), Col(c[Ini]), Col(c[Fim]), Col(c[NRel]),
                                               Col(c[Rel]), Col(c[Coord]), Col(c[Equipe]), Col(c[Status])}),
            Ren = Table.RenameColumns(Sel, List.Zip({Table.ColumnNames(Sel), NomesPadrao})),
            ComCiclo = Table.AddColumn(Ren, "Ciclo Nº", each c[Ciclo], Int64.Type)
        in
            ComCiclo),
    Empilhado = Table.Combine(PorCiclo),

    // ---- 2. Limpeza de tipos ("-", vazio e textos inválidos viram null) ----
    ParaTexto = (v as any) as nullable text =>
        let t = if v = null then null else Text.Trim(Text.From(v))
        in if t = null or t = "" or t = "-" then null else t,
    ParaData = (v as any) as nullable date =>
        if v = null then null
        else if v is date then v
        else if v is datetime then Date.From(v)
        else if v is number then Date.From(v)
        else try Date.FromText(Text.Trim(Text.From(v)), [Culture = "pt-BR"]) otherwise null,
    Tipado = Table.TransformColumns(Empilhado, {
        {"Nº PROA", ParaTexto, type text},
        {"Data Inicial Designação", ParaData, type nullable date},
        {"Data Final Designação", ParaData, type nullable date},
        {"Nº Relatório", ParaTexto, type nullable text},
        {"Data Relatório", ParaData, type nullable date},
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
    // pessoas marcadas "é auditor = Não" na aba APOIO não entram nas contagens
    ListaNaoAuditores = List.Buffer(NaoAuditores),
    SoAuditores = Table.SelectRows(SemDuplicadas, each not List.Contains(ListaNaoAuditores, [Auditor])),

    // ---- 4. Prazo e classificação ----
    Hoje = Date.From(DateTime.LocalNow()),
    // ciclo arquivado/encerrado sem relatório não é pendência do auditor
    CicloFechado = (status as nullable text) as logical =>
        let t = Text.Lower(status ?? "") in Text.Contains(t, "arquivado") or Text.Contains(t, "encerrado") or Text.Contains(t, "reclassificado"),
    ComLimite = Table.AddColumn(SoAuditores, "Data Limite", each
        if [Data Final Designação] = null then null else Date.AddDays([Data Final Designação], PrazoPadraoDias),
        type nullable date),
    ComSituacao = Table.AddColumn(ComLimite, "Situação", each
        if [Data Limite] = null then "Sem prazo definido"
        else if [Data Relatório] <> null then (if [Data Relatório] <= [Data Limite] then "No prazo" else "Fora do prazo")
        else if CicloFechado([Status do Ciclo]) then "Não se aplica"
        else if Hoje > [Data Limite] then "Pendente (vencida)"
        else "Em andamento",
        type text),
    ComOrdemSituacao = Table.AddColumn(ComSituacao, "Situação Ordem", each
        List.PositionOf({"No prazo", "Fora do prazo", "Pendente (vencida)", "Em andamento", "Não se aplica", "Sem prazo definido"}, [Situação]) + 1,
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
    // carteira atual: ciclo aberto e relatório ainda não entregue
    ComCarteira = Table.AddColumn(ComDiasAtraso, "Em Carteira", each
        if [Data Relatório] = null and not CicloFechado([Status do Ciclo]) then "Sim" else "Não", type text),
    ComDiasDesig = Table.AddColumn(ComCarteira, "Dias desde a Designação", each
        if [Em Carteira] = "Sim" and [Data Inicial Designação] <> null then Duration.Days(Hoje - [Data Inicial Designação]) else null,
        Int64.Type),
    ComAlerta = Table.AddColumn(ComDiasDesig, "Alerta de Qualidade", each
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
        "Situação", "Situação Ordem", "Entregue", "Dias para Entrega", "Dias de Atraso", "Em Carteira", "Dias desde a Designação",
        "Status do Ciclo", "Alerta de Qualidade", "Data de Referência"})
in
    Final
