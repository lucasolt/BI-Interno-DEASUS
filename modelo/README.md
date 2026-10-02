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
| `fDesignacoes` | sim | Fato: Nº PROA × Ciclo × Função × Auditor |
| `dAuditor` | sim | Dimensão auditor (cadastro + nomes fora do cadastro) |
| `dProcesso` | sim | Dimensão processo (CRS, município, status geral…) |
| `dCalendario` | sim (DAX) | Calendário |

As colunas da planilha são localizadas pelo **código do campo** (`(56)`, `(57)`…), não pelo texto
do cabeçalho, então renomear o texto do cabeçalho não quebra o BI.

## Relacionamentos

- `fDesignacoes[Auditor]` → `dAuditor[Auditor]`
- `fDesignacoes[Nº PROA]` → `dProcesso[Nº PROA]`
- `fDesignacoes[Data Final Designação]` → `dCalendario[Data]` (**ativo** – filtro de Período)
- `fDesignacoes[Data Relatório]` → `dCalendario[Data]` (inativo – evolução mensal de entregas)
- `fDesignacoes[Data Limite]` → `dCalendario[Data]` (inativo – pendências por mês de vencimento)

## Regras de negócio aplicadas

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
