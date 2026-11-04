// Ponte de período: 1 linha por linha da fato x evento (Início / Conclusão).
// dCalendario filtra a ponte, que filtra a fato (ambas as direções):
// a linha entra no período se INICIOU OU CONCLUIU dentro dele.
let
    Fonte = Table.SelectColumns(fAuditoria, {"Chave", "Data Designação", "Data Entrega"}),
    Inicio = Table.AddColumn(
        Table.AddColumn(Fonte, "Data", each [Data Designação], type nullable date),
        "Evento", each "Início", type text),
    Conclusao = Table.AddColumn(
        Table.AddColumn(Fonte, "Data", each [Data Entrega], type nullable date),
        "Evento", each "Conclusão", type text),
    Uniao = Table.Combine({
        Table.SelectColumns(Inicio, {"Chave", "Data", "Evento"}),
        Table.SelectColumns(Conclusao, {"Chave", "Data", "Evento"})}),
    ComData = Table.SelectRows(Uniao, each [Data] <> null),
    Tipos = Table.TransformColumnTypes(ComData, {{"Chave", type text}, {"Data", type date}, {"Evento", type text}})
in
    Tipos
