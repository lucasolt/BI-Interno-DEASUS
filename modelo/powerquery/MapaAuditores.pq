// Record NomeChave -> nome oficial (cadastro APOIO, sobrescrito pelo de-para manual).
let
    Cadastro = Record.FromList(stgAuditores[Auditor], stgAuditores[NomeChave]),
    Alias = Record.FromList(AliasesAuditores[Auditor], AliasesAuditores[NomeChave]),
    Mapa = Record.Combine({Cadastro, Alias})
in
    Mapa
