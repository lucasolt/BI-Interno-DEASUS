// Nome como digitado na planilha -> nome oficial do auditor.
// Fora do cadastro: devolve o próprio nome com espaços normalizados (aparece em dAuditor com Cadastrado = "Não").
(nome as nullable text) as text =>
let
    Chave = fxNormalizaNome(nome),
    Limpo = if nome = null then null
            else Text.Combine(List.Select(Text.SplitAny(nome, " #(lf)#(cr)#(tab)#(00A0)"), each _ <> ""), " "),
    Resultado = if Chave = null then "(Não informado)" else Record.FieldOrDefault(MapaAuditores, Chave, Limpo)
in
    Resultado
