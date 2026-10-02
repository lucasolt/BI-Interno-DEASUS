// Cadastro de servidores (aba APOIO, colunas N:Q) + chave normalizada. Não é carregada no modelo.
let
    Fonte = Excel.Workbook(File.Contents(CaminhoPlanilha), null, true),
    Planilha = Fonte{[Item = "APOIO", Kind = "Sheet"]}[Data],
    Cabecalhos = Table.PromoteHeaders(Planilha, [PromoteAllScalars = true]),
    Colunas = Table.SelectColumns(Cabecalhos, {"SERVIDORES", "é auditor", "Lotação", "Ativo?"}),
    Renomeado = Table.RenameColumns(Colunas, {{"SERVIDORES", "Auditor"}, {"é auditor", "É Auditor"}, {"Ativo?", "Ativo"}}),
    ComNome = Table.SelectRows(Renomeado, each [Auditor] <> null and Text.Trim(Text.From([Auditor])) <> ""),
    Limpo = Table.TransformColumns(ComNome, {
        {"Auditor", each Text.Combine(List.Select(Text.SplitAny(Text.From(_), " #(lf)#(cr)#(tab)#(00A0)"), each _ <> ""), " "), type text},
        {"É Auditor", each if _ = null then null else Text.Proper(Text.Trim(Text.From(_))), type nullable text},
        {"Lotação", each if _ = null then null else Text.Trim(Text.From(_)), type nullable text},
        {"Ativo", each if _ = null then null else Text.Proper(Text.Trim(Text.From(_))), type nullable text}
    }),
    ComChave = Table.AddColumn(Limpo, "NomeChave", each fxNormalizaNome([Auditor]), type text),
    Distintos = Table.Distinct(ComChave, {"NomeChave"})
in
    Distintos
