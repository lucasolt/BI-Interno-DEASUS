// Nomes oficiais marcados "é auditor = Não" na aba APOIO. Excluídos das fatos e da dAuditor.
let
    Lista = Table.SelectRows(stgAuditores, each [É Auditor] = "Não")[Auditor]
in
    List.Buffer(Lista)
