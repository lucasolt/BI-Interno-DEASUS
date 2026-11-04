// Ponte de período: 1 linha por linha da fato x evento (Início / Conclusão).
// dCalendario filtra a ponte, que filtra a fato (ambas as direções):
// a linha entra no período se INICIOU OU CONCLUIU dentro dele.
let
    Fonte = Table.SelectColumns(fDesignacoes, {"Chave", "Data Inicial Designação", "Data Final Designação", "Data Relatório"}),
    Inicio = Table.AddColumn(
        Table.AddColumn(Fonte, "Data", each [Data Inicial Designação] ?? [Data Final Designação], type nullable date),
        "Evento", each "Início", type text),
    Conclusao = Table.AddColumn(
        Table.AddColumn(Fonte, "Data", each [Data Relatório], type nullable date),
        "Evento", each "Conclusão", type text),
    Uniao = Table.Combine({
        Table.SelectColumns(Inicio, {"Chave", "Data", "Evento"}),
        Table.SelectColumns(Conclusao, {"Chave", "Data", "Evento"})}),
    ComData = Table.SelectRows(Uniao, each [Data] <> null),
    Tipos = Table.TransformColumnTypes(ComData, {{"Chave", type text}, {"Data", type date}, {"Evento", type text}})
in
    Tipos
