// Aba PROCESSOS crua (linha 1 = aviso, linha 2 = agrupadores, linha 3 = cabeçalho).
// Apenas linhas com Nº PROA preenchido. Não é carregada no modelo.
let
    Fonte = Excel.Workbook(File.Contents(CaminhoPlanilha), null, true),
    Planilha = Fonte{[Item = "PROCESSOS", Kind = "Sheet"]}[Data],
    SemAviso = Table.Skip(Planilha, 2),
    Cabecalhos = Table.PromoteHeaders(SemAviso, [PromoteAllScalars = true]),
    ColProa = List.First(List.Select(Table.ColumnNames(Cabecalhos), each Text.StartsWith(_, "(12)"))),
    ComProa = Table.SelectRows(Cabecalhos, each
        let v = Record.Field(_, ColProa) in v <> null and Text.Trim(Text.From(v)) <> "" and Text.Trim(Text.From(v)) <> "-")
in
    ComProa
