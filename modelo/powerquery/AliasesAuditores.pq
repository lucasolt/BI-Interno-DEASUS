// De-para manual para grafias que não batem com a lista de SERVIDORES (aba APOIO),
// mesmo após remover acentos/maiúsculas. Ao surgir um nome novo na tabela dAuditor
// com Cadastrado = "Não", acrescente aqui a grafia (já normalizada) e o nome oficial.
let
    Fonte = #table(
        type table [NomeChave = text, Auditor = text],
        {
            {"angela paiva schmitz", "Angela Paiva da Silva Schmitz"},
            {"marizane silva",       "Marizane Teixeira da Silva"},
            {"elio bessa furian",    "Elio Bessa Florian"}
        }
    )
in
    Fonte
