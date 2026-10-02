// Dimensão de auditores: cadastro de SERVIDORES (APOIO) + nomes que aparecem nas
// designações mas não estão no cadastro (Cadastrado = "Não" -> revisar AliasesAuditores).
let
    Cadastro = Table.AddColumn(Table.RemoveColumns(stgAuditores, {"NomeChave"}), "Cadastrado", each "Sim", type text),
    NomesFato = List.Buffer(List.Distinct(fDesignacoes[Auditor])),
    Faltantes = List.Difference(NomesFato, Cadastro[Auditor]),
    TabFaltantes = Table.FromRecords(
        List.Transform(Faltantes, each [Auditor = _, #"É Auditor" = null, Lotação = null, Ativo = null, Cadastrado = "Não"]),
        type table [Auditor = text, #"É Auditor" = nullable text, Lotação = nullable text, Ativo = nullable text, Cadastrado = text]),
    Unido = Table.Combine({Cadastro, TabFaltantes}),
    ComDesignacao = Table.AddColumn(Unido, "Possui Designação", each if List.Contains(NomesFato, [Auditor]) then "Sim" else "Não", type text),
    Tipado = Table.TransformColumnTypes(ComDesignacao, {
        {"Auditor", type text}, {"É Auditor", type nullable text}, {"Lotação", type nullable text},
        {"Ativo", type nullable text}, {"Cadastrado", type text}})
in
    Tipado
