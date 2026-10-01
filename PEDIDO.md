Olá, Lucas.
Gostaria de solicitar o desenvolvimento de um painel em Power BI para acompanhamento da produtividade da equipe de auditoria, com foco nas atividades de monitoramento e elaboração de relatórios.
O objetivo é disponibilizar uma visão gerencial da produção dos auditores, permitindo analisar a participação em auditorias, entregas de relatórios e cumprimento dos prazos estabelecidos.
Objetivos do Painel
O painel deverá possibilitar a análise da atuação dos auditores em duas funções distintas:
Coordenador de Auditoria;
Membro da Equipe de Auditoria.
A análise deverá consolidar informações dos 1º, 2º e 3º Ciclos de Monitoramento.
Principais Indicadores
Produção
Quantidade de designações como Coordenador;
Quantidade de designações como Membro da Equipe;
Total de designações;
Quantidade de relatórios entregues;
Quantidade de relatórios pendentes;
Quantidade de relatórios entregues dentro do prazo;
Quantidade de relatórios entregues fora do prazo.
Cumprimento de Prazo
Taxa de entrega;
Taxa de pontualidade;
Dias médios para entrega dos relatórios;
Dias médios de atraso;
Quantidade de pendências vencidas.
Distribuição do Trabalho
Designações por auditor;
Designações por ciclo;
Designações por função (Coordenador x Equipe);
Evolução mensal das entregas.
Regras de Negócio
1. Identificação dos Participantes
Para cada ciclo deverão ser utilizados os seguintes campos:
1º Ciclo
Coordenador: Campo 56
Equipe: Campo 57
Data Inicial Designação: Campo 52
Data Final Designação: Campo 53
Data Relatório: Campo 55
2º Ciclo
Coordenador: Campo 81
Equipe: Campo 82
Data Inicial Designação: Campo 77
Data Final Designação: Campo 78
Data Relatório: Campo 80
3º Ciclo
Coordenador: Campo 105
Equipe: Campo 106
Data Inicial Designação: Campo 101
Data Final Designação: Campo 102
Data Relatório: Campo 104
2. Prazo para Entrega
Considerar prazo padrão de:
30 dias
A partir da data final da designação.
Data Limite:
Plain Text
1
Data Final da Designação + 30 dias
Mostrar mais linhas
3. Classificação da Entrega
No Prazo
Data Relatório ≤ Data Limite
Fora do Prazo
Data Relatório > Data Limite
Pendente
Sem data de relatório informada
Estrutura Sugerida do Dashboard
Filtros
Período
Auditor
Ciclo
Função
Situação da Auditoria
Cartões de Indicadores
Total de Designações
Relatórios Entregues
Entregas no Prazo
Entregas Fora do Prazo
Pendências Vencidas
Prazo Médio de Entrega
Gráficos
Visão Geral
Distribuição das designações por situação;
Evolução mensal de entregas;
Taxa de Entrega;
Taxa de Pontualidade;
Taxa de Pendências.
Visão por Auditor
Tabela contendo:
Auditor
Função
Designações
Relatórios Entregues
Entregues no Prazo
Entregues Fora do Prazo
Pendências
Taxa de Entrega
Taxa de Pontualidade
Tempo Médio de Entrega
Visão por Ciclo
Quantidade de designações por ciclo;
Quantidade de entregas por ciclo;
Prazo médio de entrega por ciclo;
Taxa de pontualidade por ciclo.
Evoluções Futuras
Após a primeira versão, sugiro avaliar a inclusão dos seguintes indicadores:
Quantidade de auditorias simultâneas por auditor;
Estoque de relatórios pendentes;
Distribuição das auditorias por CRS;
Produção por trimestre e exercício;
Indicadores de atendimento das recomendações;
Classificação das auditorias por complexidade ou matriz de riscos;
Comparativo histórico de produtividade.
A ideia é que o painel forneça uma visão executiva da carga de trabalho, produtividade e cumprimento dos prazos da equipe, permitindo o acompanhamento da execução das auditorias e do fluxo de monitoramento.
Caso necessário, posso auxiliar na validação das regras de negócio e dos cálculos dos indicadores.
Segue anexo imagem de Modelo de BI esperado