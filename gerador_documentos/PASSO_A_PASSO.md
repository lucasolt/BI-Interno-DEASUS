# Documentos de Acompanhamento Periódico do Auditor — passo a passo

Gera um documento Word por auditor, com os números da aba **Acompanhamento Periódico** do BI.
Leva uns 5 minutos. Não precisa instalar nada.

## Você vai precisar
- Acesso ao BI Interno DEASUS (área da chefia).
- O arquivo **`Gerador_Acompanhamento_Periodico.html`** (deixe uma cópia numa pasta da rede ou no SharePoint).
  Não precisa instalar nada nem de internet: abre no Edge ou no Chrome e os arquivos não saem do computador.

## 1. Exportar os dados do BI
1. Abra o BI → **Área da chefia** → **Acompanhamento Periódico**.
2. Escolha o período no filtro **Semestre** ou **Quadrimestre**.
3. Na tabela, passe o mouse e clique em **…** (canto superior direito) → **Exportar dados**.
4. Escolha **Dados com layout atual** e o formato **.xlsx** → **Exportar**.
5. (Opcional) Abra o Excel e acrescente uma coluna **Avaliação Descritiva** com o texto de cada auditor.
   Se preferir, escreva depois direto em cada documento.

## 2. Gerar os documentos
1. **Baixe** `Gerador_Acompanhamento_Periodico.html` para o computador (no SharePoint: "…" → Baixar) e dê dois cliques no arquivo baixado. Não abra direto pelo SharePoint: lá ele não funciona.
2. Preencha **Período** (ex.: `1º/2026`) e **Avaliadores**.
3. **Escolher Excel…** → selecione o Excel exportado.
4. **Gerar documentos (.zip)** → o navegador baixa um .zip com um documento Word por auditor.
5. Para usar outro modelo de documento: abra "Usar outro modelo de documento" e escolha o `.docx`.

## Se der problema
| Mensagem | O que fazer |
|---|---|
| `Não achei a coluna 'Auditor'` | O Excel não é o da tabela da aba Acompanhamento Periódico. Exporte de novo (passo 1). |
| Botão **Gerar** cinza | Falta escolher o Excel. |
| `Preencha o Período` | Preencha o campo Período e clique em gerar de novo. |
| `colunas não encontradas` | Alguém renomeou uma coluna no BI. O documento sai com o número em branco; avise quem mantém o BI. |
| O download não aparece | Veja a barra de downloads do navegador (pode pedir para "Manter" o arquivo). |

## Alternativa: Colab
`Gerador_Acompanhamento_Periodico.ipynb` faz o mesmo no Google Colab (Arquivo → Fazer upload de notebook →
Executar tudo → painel com botões). Atenção: no Colab o Excel é enviado para uma máquina do Google.

## Para quem mantém (técnico)
- **Página HTML:** o código está em `html/gerador.template.html`; as bibliotecas em `html/vendor/`
  (SheetJS 0.18.5, PizZip 3.3.0, docxtemplater 3.71.1). Depois de alterar o template, as bibliotecas ou
  o modelo .docx, rode `python gerador_documentos/html/montar_html.py` (gera o .html único, com tudo embutido).
  As linhas do documento ficam na constante `ATIVIDADES` do template.
- **Colab/Python:**
- O código fica em `gerar_documentos.py` (geração) e `painel.py` (botões). O notebook é montado a partir
  deles e do modelo `.docx` (embutido): depois de alterar qualquer um, rode `python montar_notebook.py`.
- As 5 linhas do documento estão na lista `ATIVIDADES` (texto no documento → coluna do Excel).
- As colunas são lidas pelo nome, não pela posição. A coluna `PROAs` vem do BI separada por `; `.
- Teste no computador: `python gerar_documentos.py exportacao.xlsx modelo.docx --periodo "1º/2026"`.
