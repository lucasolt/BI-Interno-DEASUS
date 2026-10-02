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
| `dCalendario` | sim (DAX) | Calendário |

As colunas da planilha são localizadas pelo **código do campo** (`(56)`, `(57)`…), não pelo texto
do cabeçalho, então renomear o texto do cabeçalho não quebra o BI.

## Relacionamentos

- `fDesignacoes[Auditor]` → `dAuditor[Auditor]`
- `fDesignacoes[Nº PROA]` → `dProcesso[Nº PROA]`
- `fDesignacoes[Data Final Designação]` → `dCalendario[Data]` (**ativo** – filtro de Período)
- `fDesignacoes[Data Relatório]` → `dCalendario[Data]` (inativo – evolução mensal de entregas)
- `fDesignacoes[Data Limite]` → `dCalendario[Data]` (inativo – pendências por mês de vencimento)
- `fAuditoria`: `Auditor`, `Nº PROA`, `Data Designação` (**ativo**), `Data Entrega` e `Data Limite` (inativos)
- `fAuditoria[Função]` e `fDesignacoes[Função]` → `dFuncao`; `[Situação]` de ambas → `dSituacao`

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
