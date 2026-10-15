// Dimensão de processos (1 linha por Nº PROA) com atributos para filtros/evoluções futuras (CRS etc.).
// Somente processos com designação de auditoria ou de monitoramento.
let
    Origem = stgProcessos,
    Mapa = {
        {"012 - Nº PROA", "Nº PROA"},
        {"Monitoramento", "Classificação Monitoramento"},
        {"003 - TIPO DE AUDITORIA", "Tipo de Auditoria"},
        {"004 - EIXO", "Eixo"},
        {"006 - AUDITADO", "Auditado"},
        {"007 - TIPO DE ESTABELECIMENTO", "Tipo de Estabelecimento"},
        {"008 - MUNICÍPIO", "Município"},
        {"009 - CRS", "CRS"},
        {"010 - REGIÃO DE SAÚDE", "Região de Saúde"},
        {"011 - MACRORREGIÃO", "Macrorregião"},
        {"M - Ciclo Atual", "Ciclo Atual"},
        {"M - Status Atual Geral do Monitoramento", "Status Geral do Monitoramento"}
    },
    Sel = Table.SelectColumns(Origem, List.Transform(Mapa, each _{0})),
    Ren = Table.RenameColumns(Sel, Mapa),
    ParaTexto = (v as any) as nullable text =>
        let t = if v = null then null else Text.Trim(Text.From(v))
        in if t = null or t = "" or t = "-" then null else t,
    Limpo = Table.TransformColumns(Ren, List.Transform(List.Transform(Mapa, each _{1}), (n) => {n, ParaTexto, type nullable text})),
    ProasFato = List.Buffer(List.Distinct(fDesignacoes[Nº PROA] & fAuditoria[Nº PROA])),
    ComDesignacao = Table.SelectRows(Limpo, each List.Contains(ProasFato, [Nº PROA])),
    Distintos = Table.Distinct(ComDesignacao, {"Nº PROA"})
in
    Distintos
