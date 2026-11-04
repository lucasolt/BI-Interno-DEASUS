# Documentos de Acompanhamento Periódico do Auditor — passo a passo

Gera um documento Word por auditor, com os números da aba **Acompanhamento Periódico** do BI.
Leva uns 5 minutos. Não precisa instalar nada.

## Você vai precisar
- Acesso ao BI Interno DEASUS (área da chefia).
- Uma conta Google (para abrir o Colab).
- Dois arquivos desta pasta:
  `Gerador_Acompanhamento_Periodico.ipynb` e `Modelo_Documento_de_Acompanhamento_Quadrimestral_do_Auditor.docx`.

## 1. Exportar os dados do BI
1. Abra o BI → **Área da chefia** → **Acompanhamento Periódico**.
2. Escolha o período no filtro **Semestre** ou **Quadrimestre**.
3. Na tabela, passe o mouse e clique em **…** (canto superior direito) → **Exportar dados**.
4. Escolha **Dados com layout atual** e o formato **.xlsx** → **Exportar**.
5. (Opcional) Abra o Excel e acrescente uma coluna **Avaliação Descritiva** com o texto de cada auditor.
   Se preferir, escreva depois direto em cada documento.

## 2. Gerar os documentos
1. Acesse https://colab.research.google.com → **Arquivo → Fazer upload de notebook** →
   escolha `Gerador_Acompanhamento_Periodico.ipynb`.
   (Na próxima vez ele aparece em **Arquivo → Abrir notebook → Recentes**.)
2. No bloco **1. Dados do período**, preencha **PERIODO** (ex.: `1º/2026`) e **AVALIADORES**.
3. Menu **Ambiente de execução → Executar tudo**.
4. Quando aparecer o botão **Escolher arquivos**, selecione **os dois arquivos juntos**
   (o Excel exportado e o modelo .docx).
5. No fim, o navegador baixa `documentos_acompanhamento.zip` com um documento por auditor.

## Se der problema
| Mensagem | O que fazer |
|---|---|
| `Não achei a coluna 'Auditor'` | O Excel não é o da tabela da aba Acompanhamento Periódico. Exporte de novo (passo 1). |
| `Faltou arquivo` | Rode o bloco 3 de novo e selecione os **dois** arquivos juntos. |
| `colunas não encontradas` | Alguém renomeou uma coluna no BI. O documento sai com o número em branco; avise quem mantém o BI. |
| Pede para "confiar" ou "executar mesmo assim" | Normal no Colab. Clique em **Executar mesmo assim**. |

## Para quem mantém (técnico)
- O código fica em `gerar_documentos.py` (fonte única). Depois de alterar, rode `python montar_notebook.py`
  para atualizar o notebook.
- As 5 linhas do documento estão na lista `ATIVIDADES` (texto no documento → coluna do Excel).
- As colunas são lidas pelo nome, não pela posição. A coluna `PROAs` vem do BI separada por `; `.
- Teste no computador: `python gerar_documentos.py exportacao.xlsx modelo.docx --periodo "1º/2026"`.
