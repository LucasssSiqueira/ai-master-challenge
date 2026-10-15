# Etapa 07 — Redesign da experiência do Pipeline

Pedido: transformar a tabela em uma experiência simples, bonita e funcional (Linear, Apple, Raycast), com busca, filtros, ordenação, score legível e painel lateral, sem alterar o score. Detalhes em `docs/10-pipeline-ux.md`.

## Processo
1. **Inspeção antes de codar:** a tabela era `st.dataframe` (canvas, sem estilo, sem hover nem tooltip). O único filtro eram os 4 botões de `st.pills`. O detalhe aparecia abaixo da tabela. Daí o plano de um componente HTML/JS único.
2. **Implementação:** `ui/pipeline_table.py`. O Python entrega as linhas reais do recorte como JSON; o navegador cuida de busca, filtros, ordenação estável, paginação, tooltip e painel. Pipeline e Deals parados usam o mesmo componente, e o código antigo de tabela e detalhe foi removido.
3. **Validação:** 5 testes de unidade (fidelidade ao motor e escape) e 13 testes no navegador real com Playwright. Os resultados esperados vêm do próprio motor, em pandas, e não de valores fixados à mão. Rodados em Streamlit 1.49 e 1.66.

## Onde errei e corrigi
| Erro | Como apareceu | Correção |
|---|---|---|
| Faixa cinza na borda direita | Screenshot em alta resolução + `elementFromPoint` | A sombra do painel fechado vazava; o painel fechado agora fica invisível |
| Cabeçalho desalinhado em tablet | Screenshot em 900 px; o teste de larguras não pegou | `!important` nas colunas ocultas; o teste passou a comparar cabeçalho e células |
| Teste chamava `frame.keyboard` | Primeira execução da suíte | Teclado vem de `page` |
| Testes nas versões mínimas rodaram contra um servidor antigo | O texto antigo apareceu na falha | `pkill` com padrão que não casava; reiniciado pela porta, com cuidado para não encerrar o processo de rede do app Claude que também estava na porta |
