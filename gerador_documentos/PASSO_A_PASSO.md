# Documentos de Acompanhamento Periódico do Auditor — passo a passo

Gera um documento Word por auditor, com os números da aba **Acompanhamento Periódico** do BI.
Leva uns 5 minutos. Não precisa instalar nada.

## Você vai precisar
- Acesso ao BI Interno DEASUS (área da chefia).
- Uma conta Google (para abrir o Colab).
- O arquivo `Gerador_Acompanhamento_Periodico.ipynb` (o modelo do documento já vem dentro dele).

## 1. Exportar os dados do BI
1. Abra o BI → **Área da chefia** → **Acompanhamento Periódico**.
2. Escolha o período no filtro **Semestre** ou **Quadrimestre**.
3. Na tabela, passe o mouse e clique em **…** (canto superior direito) → **Exportar dados**.
4. Escolha **Dados com layout atual** e o formato **.xlsx** → **Exportar**.
5. (Opcional) Abra o Excel e acrescente uma coluna **Avaliação Descritiva** com o texto de cada auditor.
   Se preferir, escreva depois direto em cada documento.

## 2. Gerar os documentos (painel com botões)
1. Abra o notebook no Colab (https://colab.research.google.com → **Arquivo → Fazer upload de notebook**,
   ou direto do Google Drive, se já tiver salvo uma cópia lá).
2. Menu **Ambiente de execução → Executar tudo**. Aparece o painel:
   - **Período** (ex.: `1º/2026`) e **Avaliadores**;
   - **1. Escolher Excel do BI** → selecione o Excel exportado;
   - **2. Gerar documentos**;
   - **3. Baixar ZIP** → baixa um documento por auditor.
     Se o download não começar, use o link que aparece ao lado do botão.
3. Para usar outro modelo de documento, escolha o `.docx` junto com o Excel no botão 1.

**Plano B:** se o botão *Escolher Excel* não abrir a janela de arquivos, role até o bloco **Plano B**,
preencha Período e Avaliadores, clique no ▶ do bloco e escolha o Excel no botão que aparecer.

## Se der problema
| Mensagem | O que fazer |
|---|---|
| `Não achei a coluna 'Auditor'` | O Excel não é o da tabela da aba Acompanhamento Periódico. Exporte de novo (passo 1). |
| Botão **2. Gerar** cinza | Falta escolher o Excel no botão 1. |
| `Preencha o Período` | Preencha o campo Período e clique em gerar de novo. |
| `colunas não encontradas` | Alguém renomeou uma coluna no BI. O documento sai com o número em branco; avise quem mantém o BI. |
| Pede para "confiar" ou "executar mesmo assim" | Normal no Colab. Clique em **Executar mesmo assim**. |

## Para quem mantém (técnico)
- O código fica em `gerar_documentos.py` (geração) e `painel.py` (botões). O notebook é montado a partir
  deles e do modelo `.docx` (embutido): depois de alterar qualquer um, rode `python montar_notebook.py`.
- As 5 linhas do documento estão na lista `ATIVIDADES` (texto no documento → coluna do Excel).
- As colunas são lidas pelo nome, não pela posição. A coluna `PROAs` vem do BI separada por `; `.
- Teste no computador: `python gerar_documentos.py exportacao.xlsx modelo.docx --periodo "1º/2026"`.
