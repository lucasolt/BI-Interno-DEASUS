# Modelo de dados – BI Interno DEASUS (Produtividade de Auditores)

Cópia versionada das consultas criadas em `BI Interno DEASUS.pbix`. A fonte da verdade é o .pbix;
estes arquivos servem para revisão/diff.

## Consultas (Power Query)

| Consulta | Carrega? | Função |
|---|---|---|
| `CaminhoPlanilha` | não | Parâmetro: caminho do .xlsx fonte |
| `PrazoPadraoDias` | não | Parâmetro: prazo padrão (30 dias) |
| `fxNormalizaNome` | não | Chave de nome (minúsculas, sem acento, espaços colapsados) |
| `stgProcessos` | não | Aba PROCESSOS (cabeçalho na linha 3), só linhas com Nº PROA |
| `stgAuditores` | não | Lista SERVIDORES da aba APOIO |
| `AliasesAuditores` | não | De-para manual de grafias divergentes |
| `PrazoRAIDias` / `PrazoRAFDias` | não | Parâmetros: prazos do RAI (30) e RAF (60) a partir da designação |
| `MapaAuditores`, `fxAuditorOficial`, `fxParticipantes` | não | Regras de nomes compartilhadas pelas duas fatos |
| `fAuditoria` | sim | Fato Auditoria: Nº PROA × Relatório (RAI/RAF) × Função × Auditor |
| `fDesignacoes` | sim | Fato Monitoramento: Nº PROA × Ciclo × Função × Auditor |
| `dAuditor` | sim | Dimensão auditor (cadastro + nomes fora do cadastro) |
| `dProcesso` | sim | Dimensão processo (CRS, município, status geral…) |
| `dFuncao`, `dSituacao` | sim | Dimensões compartilhadas (filtros valem para as duas fases) |
| `dCalendario` | sim (DAX) | Calendário (ano, semestre, quadrimestre, trimestre, mês) |
| `bAtividadeMonitoramento`, `bAtividadeAuditoria` | sim | Pontes de período: 1 linha por evento (Início/Conclusão) de cada linha da fato |

As colunas da planilha são localizadas pelo **código do campo** (`(56)`, `(57)`…), não pelo texto
do cabeçalho, então renomear o texto do cabeçalho não quebra o BI.

## Relacionamentos

- `fDesignacoes` e `fAuditoria` → `dAuditor`, `dProcesso`, `dFuncao`, `dSituacao`
- **Período (ativo):** `dCalendario[Data]` → `bAtividadeMonitoramento[Data]` / `bAtividadeAuditoria[Data]`
  → (ambas as direções) `fDesignacoes[Chave]` / `fAuditoria[Chave]`
- Relações diretas fato → `dCalendario` são **inativas** e só usadas nas medidas "por Data ..."
  (evolução mensal), que desligam a ponte com `CROSSFILTER(..., NONE)`:
  `Data Relatório`/`Data Entrega` (entregas no mês), `Data Limite` (vencimentos no mês),
  `Data Final Designação`/`Data Designação` (sem uso em medida).

## Regra do período (avaliação dos auditores)

Uma designação entra no período filtrado se o auditor **iniciou OU concluiu** nele:

| Fase | Início | Conclusão |
|---|---|---|
| Auditoria (RAI e RAF, linha a linha) | Data de Designação (17) | Data de entrega do RAI (19) / RAF (21) |
| Monitoramento (ciclos 1–3) | Data Inicial da Designação (52/77/101); se vazia, Data Final (53/78/102) | Data do Relatório (55/80/104) |

- A mesma designação pode aparecer em dois períodos (no que começou e no que terminou).
- Linhas sem nenhuma data somem quando há filtro de período.
- Pendências antigas (iniciadas antes e ainda sem entrega) **não** entram no período; para o estoque
  de pendências, use a página sem filtro de período ou as medidas "(por Data Limite)".
- A coluna `Evento` das pontes permite restringir a só "Início" ou só "Conclusão".
- `dCalendario` tem Semestre (`Ano/Semestre`) e Quadrimestre (`Ano/Quadrimestre`).

## Regras de negócio aplicadas

### Auditoria
- **RAI**: Data Limite = Data de Designação (17) + 30 dias; entrega = campo (19).
- **RAF**: Data Limite = Data de Designação (17) + 60 dias (igual à coluna 22); entrega = campo (21).
- Sem entrega em processo `ARQUIVADO` / `FASE DE AUDITORIA FINALIZADA` → `Não se aplica` (fora das taxas).
- Matrizes de Qualidade: colunas `Qtde Martiz Qualidade RIA/RFA`; média = matrizes ÷ relatórios avaliados.

### Monitoramento

- **Data Limite** = Data Final da Designação + 30 dias.
- **Situação**: `No prazo` (Relatório ≤ Limite) · `Fora do prazo` (Relatório > Limite) ·
  `Pendente (vencida)` (sem relatório e hoje > Limite) · `Em andamento` (sem relatório, dentro do prazo) ·
  `Sem prazo definido` (sem Data Final da Designação).
- **Dias para Entrega** = Data Relatório − Data Inicial da Designação.
- **Dias de Atraso** = Data Relatório − Data Limite (entregues fora do prazo) ou hoje − Data Limite (pendências vencidas).
- **Taxa de Entrega** = Entregues ÷ (Entregues + Pendências vencidas).
- **Taxa de Pontualidade** = No prazo ÷ Entregues.
- **Índice de Produtividade** = 40% Taxa de Entrega + 40% Pontualidade + 20% Participação relativa.
- Equipe: nomes separados por `;` `,` `/` ou ` e `. Cada membro conta 1 designação.
- "Hoje" = data da última atualização do modelo (coluna `Data de Referência`).

## Manutenção

- Nome novo aparecendo com `dAuditor[Cadastrado] = "Não"` → incluir em `AliasesAuditores`
  (chave já normalizada → nome oficial) ou corrigir na aba APOIO.
- `fDesignacoes[Alerta de Qualidade]` sinaliza registros a revisar na planilha.

## Relatório (visuais)

Gerado por `modelo/gerar_relatorio.py` (formato PBIR). Rodar **com o Desktop fechado**;
ajustes manuais feitos nas páginas pelo Desktop são sobrescritos ao rodar de novo.
