// Fato da fase de AUDITORIA: 1 linha por Nº PROA x Relatório (RAI/RAF) x Função x Auditor.
// Campos (nomes do dictDadosDep): Coordenador (014), Equipe (018), Data de Designação (017), Nº RAI (015),
//         Entrega RAI (019), Nº RAF (020), Entrega RAF (021), Matriz de Qualidade RAI/RAF (MQ), Status (042).
// Prazos: RAI = Designação + PrazoRAIDias (30) | RAF = Designação + PrazoRAFDias (60).
// Sem data de entrega em processo ARQUIVADO / FASE DE AUDITORIA FINALIZADA -> "Não se aplica".
let
    Origem = stgProcessos,
    Mapa = {
        {"012 - Nº PROA", "Nº PROA"},
        {"014 - COORDENADOR", "Coordenador"},
        {"018 - EQUIPE", "EquipeTexto"},
        {"017 - DATA DE DESIGNAÇÃO", "Data Designação"},
        {"015 - N° RELATÓRIO INICIAL", "Nº RAI"},
        {"019 - DATA ENTREGA RELATÓRIO INICIAL EQUIPE => CHEFIA", "Data RAI"},
        {"020 - N° RELATÓRIO FINAL", "Nº RAF"},
        {"021 - DATA ENTREGA RELATÓRIO FINAL EQUIPE => CHEFIA", "Data RAF"},
        {"MQ - Qtde Matriz Qualidade RAI", "Matriz RAI"},
        {"MQ - Qtde Matriz Qualidade RAF", "Matriz RAF"},
        {"042 - STATUS", "Status do Processo"}
    },
    Sel = Table.RenameColumns(Table.SelectColumns(Origem, List.Transform(Mapa, each _{0})), Mapa),

    ParaTexto = (v as any) as nullable text =>
        let t = if v = null then null else Text.Trim(Text.From(v))
        in if t = null or t = "" or t = "-" then null else t,
    // Datas e matrizes já chegam tipadas pelo dicionário; textos: "-" e vazio viram null
    Tipado = Table.TransformColumns(Sel, {
        {"Nº PROA", ParaTexto, type text}, {"Coordenador", ParaTexto, type nullable text},
        {"EquipeTexto", ParaTexto, type nullable text}, {"Nº RAI", ParaTexto, type nullable text},
        {"Nº RAF", ParaTexto, type nullable text}, {"Status do Processo", ParaTexto, type nullable text}
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
