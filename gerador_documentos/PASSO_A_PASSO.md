# Documentos de Acompanhamento Periódico do Auditor — passo a passo

Gera um documento Word por auditor, com os números da aba **Acompanhamento Periódico** do BI.
Leva uns 5 minutos.

## Você vai precisar
- Acesso ao BI Interno DEASUS (área da chefia).
- Jupyter instalado (ex.: Anaconda, ou VS Code com a extensão Jupyter).
- Esta pasta inteira (`gerador_documentos`), com: `Gerador_Acompanhamento_Periodico.ipynb`,
  `gerar_documentos.py` e `Modelo_Documento_de_Acompanhamento_Quadrimestral_do_Auditor.docx`.

## 1. Exportar os dados do BI
1. Abra o BI → **Área da chefia** → **Acompanhamento Periódico**.
2. Escolha o período no filtro **Semestre** ou **Quadrimestre**.
3. Na tabela, passe o mouse e clique em **…** (canto superior direito) → **Exportar dados**.
4. Escolha **Dados com layout atual** e o formato **.xlsx** → **Exportar**.
5. **Salve o arquivo dentro da pasta `gerador_documentos`.**
6. (Opcional) Abra o Excel e acrescente uma coluna **Avaliação Descritiva** com o texto de cada auditor.
   Se preferir, escreva depois direto em cada documento.

## 2. Gerar os documentos
1. Abra `Gerador_Acompanhamento_Periodico.ipynb` no Jupyter.
2. Na primeira célula (**1. Configuração**), preencha **PERIODO** (ex.: `"1º/2026"`) e **AVALIADORES**.
   Deixe **ARQUIVO_EXCEL** vazio para usar o Excel mais recente da pasta.
3. Menu **Run → Run All Cells** (ou *Executar tudo*).
4. Os documentos aparecem numa pasta nova, ex.: `documentos_1º_2026`, mais um `.zip` com todos.
   No Windows, a pasta abre sozinha.

## Se der problema
| Mensagem | O que fazer |
|---|---|
| `Nenhum Excel nesta pasta` | Salve o Excel exportado dentro da pasta `gerador_documentos`. |
| `Não achei a coluna 'Auditor'` | O Excel usado não é o da tabela do Acompanhamento Periódico. Confira a linha `Excel usado:` e exporte de novo. |
| `Modelo não encontrado` | O modelo .docx precisa estar na pasta, com o mesmo nome da célula de configuração. |
| `No module named 'gerar_documentos'` | O notebook foi aberto fora da pasta. Abra o que está dentro de `gerador_documentos`. |
| `colunas não encontradas` | Alguém renomeou uma coluna no BI. O documento sai com o número em branco; avise quem mantém o BI. |
| O Excel aberto dá erro de permissão | Feche o Excel antes de rodar. |

## Para quem mantém (técnico)
- O código fica em `gerar_documentos.py`; o notebook só configura e chama `gerar()`.
- As 5 linhas do documento estão na lista `ATIVIDADES` (texto no documento → coluna do Excel).
- As colunas são lidas pelo nome, não pela posição. A coluna `PROAs` vem do BI separada por `; `.
- Teste no computador: `python gerar_documentos.py exportacao.xlsx modelo.docx --periodo "1º/2026"`.
