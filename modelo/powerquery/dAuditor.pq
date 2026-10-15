// Dimensão de auditores: cadastro de SERVIDORES (APOIO) + nomes que aparecem nas
// designações mas não estão no cadastro (Cadastrado = "Não" -> revisar AliasesAuditores).
let
    // quem não é auditor fica fora da dimensão (e das fatos, via NaoAuditores)
    SoAuditores = Table.SelectRows(stgAuditores, each [É Auditor] <> "Não"),
    Cadastro = Table.AddColumn(Table.RemoveColumns(SoAuditores, {"NomeChave"}), "Cadastrado", each "Sim", type text),
    NomesMonit = List.Distinct(fDesignacoes[Auditor]),
    NomesAud = List.Distinct(fAuditoria[Auditor]),
    NomesFato = List.Buffer(List.Distinct(NomesMonit & NomesAud)),
    Faltantes = List.Difference(NomesFato, Cadastro[Auditor]),
    TabFaltantes = Table.FromRecords(
        List.Transform(Faltantes, each [Auditor = _, #"É Auditor" = null, Lotação = null, Ativo = null, Cadastrado = "Não"]),
        type table [Auditor = text, #"É Auditor" = nullable text, Lotação = nullable text, Ativo = nullable text, Cadastrado = text]),
    Unido = Table.Combine({Cadastro, TabFaltantes}),
    ComDesignacao = Table.AddColumn(Unido, "Possui Designação", each if List.Contains(NomesFato, [Auditor]) then "Sim" else "Não", type text),
    // Ativo sempre preenchido (Sim / Não / Não cadastrado / Não informado): base do filtro "Auditores ativos"
    AtivoPreenchido = Table.ReplaceValue(ComDesignacao, each [Ativo], each
        if [Cadastrado] = "Não" then "Não cadastrado" else if [Ativo] = null then "Não informado" else [Ativo],
        Replacer.ReplaceValue, {"Ativo"}),
    Tipado = Table.TransformColumnTypes(AtivoPreenchido, {
        {"Auditor", type text}, {"É Auditor", type nullable text}, {"Lotação", type nullable text},
        {"Ativo", type nullable text}, {"Cadastrado", type text}})
in
    Tipado
