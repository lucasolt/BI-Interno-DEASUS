// Situação do relatório quanto ao prazo (dimensão compartilhada por fAuditoria e fDesignacoes).
#table(
    type table [Situação = text, #"Situação Ordem" = Int64.Type, Grupo = text, #"Entra nas Taxas" = text],
    {
        {"No prazo", 1, "Entregue", "Sim"},
        {"Fora do prazo", 2, "Entregue", "Sim"},
        {"Pendente (vencida)", 3, "Pendente", "Sim"},
        {"Em andamento", 4, "Pendente", "Não"},
        {"Não se aplica", 5, "Outros", "Não"},
        {"Sem prazo definido", 6, "Outros", "Não"}
    })
