let
    Fonte = Excel.Workbook(Web.Contents("https://rsgovbr.sharepoint.com/sites/SES-qualidadedeasus/Shared%20Documents/DEASUS/30%20-%20INSTRUMENTOS%20DE%20GEST%C3%83O/05%20-%20RELAT%C3%93RIO%20DETALHADO%20DO%20QUADRIMESTRE%20ANTERIOR%20(RDQA)/2023/ESTUDO%20DOS%20PROCESSOS%20PARA%20AN%C3%81LISE%20DO%20RDQA%20-%20Copiar.xlsx"), null, true),
    PROCESSOS_Sheet = Fonte{[Item="PROCESSOS",Kind="Sheet"]}[Data],
    #"Linhas Superiores Removidas" = Table.Skip(PROCESSOS_Sheet,2),
    #"Cabeçalhos Promovidos" = Table.PromoteHeaders(#"Linhas Superiores Removidas", [PromoteAllScalars=true]),

    // Colunas sem código "(n)" no cabeçalho (fora do dicionário) usadas pelo painel: {origem, novo nome, tipo}
    ColunasForaDict = {
        {"Monitoramento",             "Monitoramento",                  type text},
        {"Qtde Martiz Qualidade RIA", "MQ - Qtde Matriz Qualidade RAI", type number},
        {"Qtde Martiz Qualidade RFA", "MQ - Qtde Matriz Qualidade RAF", type number}
    },

    ColsDict   = Table.ColumnNames(fxSelecionarCols(#"Cabeçalhos Promovidos", dictDadosDep)),
    ColsManter = ColsDict & List.Transform(ColunasForaDict, each _{0}),
    #"ColSelecionadas" = Table.SelectColumns(#"Cabeçalhos Promovidos",
        List.Select(Table.ColumnNames(#"Cabeçalhos Promovidos"), each List.Contains(ColsManter, _))),

    #"ColRenomeadas" = fxRenameCols(#"ColSelecionadas", dictDadosDep),
    #"ColTipadas"    = fxTyparCols(#"ColRenomeadas", dictDadosDep),

    #"ExtrasRenomeadas" = Table.RenameColumns(#"ColTipadas", List.Transform(ColunasForaDict, each {_{0}, _{1}})),
    #"ExtrasTipadas"    = Table.TransformColumnTypes(#"ExtrasRenomeadas", List.Transform(ColunasForaDict, each {_{1}, _{2}}), "pt-BR"),

    // Valores que não convertem no tipo do dicionário ("-", "s/d", texto em coluna de data...) viram null
    #"ErrosParaNull" = Table.ReplaceErrorValues(#"ExtrasTipadas",
        List.Transform(Table.ColumnNames(#"ExtrasTipadas"), each {_, null})),

    #"RetirarLinhasVazias" = Table.SelectRows(#"ErrosParaNull", each
        not List.Contains({null, "", "-"}, try Text.Trim([#"012 - Nº PROA"]) otherwise null)),

    #"FiltrarAnoCorte" = Table.SelectRows(#"RetirarLinhasVazias", each
        [#"013 - DATA DE ABERTURA"] <> null and Date.Year([#"013 - DATA DE ABERTURA"]) >= AnoDeCorte),

    // Sem fxProcessarSigiloso: painel interno, e o mascaramento do "042 - STATUS" quebraria a regra "Não se aplica" de fAuditoria
    #"AplicarCasing" = fxAplicarCasing(#"FiltrarAnoCorte", dictDadosDep)
in
    #"AplicarCasing"
