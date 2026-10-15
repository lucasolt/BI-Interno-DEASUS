// De-para Status do processo (42) -> Fase e "Com Quem".
let
    Fonte = #table(
        type table [StatusChave = text, Fase = text, #"Fase Ordem" = Int64.Type, #"Com Quem" = text],
        {
            {"aguarda criacao de rai",            "Elaboração do RAI",          1,  "Com a equipe"},
            {"aguarda acolhimento rai",           "Revisão do RAI (chefia)",    2,  "Com a chefia"},
            {"aguarda envio do rai ao auditado",  "RAI enviado ao auditado",    3,  "Aguardando auditado"},
            {"aguarda apresentacao de defesa",    "Prazo de defesa",            4,  "Aguardando auditado"},
            {"aguarda analise de defesa",         "Análise de defesa",          5,  "Com a equipe"},
            {"aguarda emissao raf",               "Elaboração do RAF",          6,  "Com a equipe"},
            {"aguarda acolhimento raf",           "Revisão do RAF (chefia)",    7,  "Com a chefia"},
            {"aguarda envio do raf ao auditado",  "RAF enviado ao auditado",    8,  "Aguardando auditado"},
            {"aguarda interposicao de recurso",   "Prazo de recurso",           9,  "Aguardando auditado"},
            {"aguarda analise de recurso",        "Análise de recurso",         10, "Com a equipe"},
            {"aguarda decisao",                   "Decisão",                    11, "Com a chefia"},
            {"encaminhado ao fes",                "Encaminhado ao FES",         12, "Fora da equipe"}
        }
    )
in
    Fonte
