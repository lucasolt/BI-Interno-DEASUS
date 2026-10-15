// De-para Eixo (campo 04) -> Eixo Temático. Chave normalizada por fxNormalizaNome.
let
    Fonte = #table(
        type table [EixoChave = text, #"Eixo Temático" = text],
        {
            {"aih", "AIH"},
            {"auditoria aih", "AIH"},
            {"uti", "AIH"},

            {"amb gestacao alto risco (agar)", "Rede Materno Paterno Infantil"},
            {"materno infantil", "Rede Materno Paterno Infantil"},
            {"rede materno paterno infantil", "Rede Materno Paterno Infantil"},
            {"uti neonatal", "Rede Materno Paterno Infantil"},

            {"auditiva", "Pessoas com Deficiência - Auditiva"},
            {"politicas de atencao as pessoas com deficiencia - auditiva", "Pessoas com Deficiência - Auditiva"},

            {"citopatologia", "Saúde da Mulher"}, // será?
            {"politicas de saude da mulher", "Saúde da Mulher"},
            {"politicas de saude da mulher - cito", "Saúde da Mulher"},

            {"doencas cronicas", "Doenças Crônicas"},
            {"doencas cronicas - cardiovascular", "Doenças Crônicas"},
            {"doencas cronicas -trs", "Doenças Crônicas"},
            {"politicas de atencao a doencas cronicas - bariatrica", "Doenças Crônicas"},
            {"politicas de atencao a doencas cronicas - nefro", "Doenças Crônicas"},
            {"politicas de atencao a doencas cronicas - onco", "Doenças Crônicas"},

            {"mental", "Rede de Atenção Psicossocial (RAPS)"}, // será?
            {"rede de atencao psicossocial (raps)", "Rede de Atenção Psicossocial (RAPS)"}
        }
    )
in
    Fonte
