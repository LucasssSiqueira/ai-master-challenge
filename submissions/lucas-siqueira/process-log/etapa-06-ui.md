# Etapa 06 — Redesign da interface

Pedido: interface minimalista inspirada numa imagem de referência (Linear + Apple), com 4 áreas, cores com significado e sem componentes desnecessários. Detalhes e decisões em `docs/09-ui-redesign.md`.

## Processo
1. **Revisão antes de codar:** screenshot da versão anterior ([08](screenshots/08-ui-antes-redesign.jpg)) e lista de excessos (emojis, cards de texto, cromo do Streamlit, cor sem significado, três tarefas na mesma tela).
2. **Separação de camadas:** cálculo dos insights em `lead_scorer/insights.py` (testável); visual em `ui/` (tokens, CSS, HTML como funções puras com escape); `app.py` só monta as páginas.
3. **Validação no navegador real**, em 1.280–1.440 px e 760 px, e com Playwright apontando para o Chrome local, para gerar screenshots em alta resolução ([09](screenshots/09-ui-redesign-visao-geral.png), [10](screenshots/10-ui-redesign-pipeline-detalhe.png), [11](screenshots/11-ui-redesign-tela-estreita.png)).
4. **AppTest:** 113 execuções (4 páginas × todos os escopos e pessoas) nas versões mínimas e atuais.

## Onde errei e corrigi
| Erro | Como apareceu | Correção |
|---|---|---|
| A grade de 2 colunas ficava espremida em tela estreita | Screenshot no painel de 756 px | Empilha abaixo de 1.180 px; prioridades primeiro |
| CSS novo não aparecia | Inspeção do DOM: o servidor não recarregava `ui/theme.py` | Reiniciar o servidor a cada mudança de módulo |
| Link para Maureen abria Anna | Teste de deep link na mesma aba | A URL vence quando muda por fora (`adopt_url`) |
| Seletores de "ativo" e do select sem efeito | `getComputedStyle` no navegador | Atributos reais da versão: `data-selected`, `role=group` |
| Fonte Source Sans no lugar da Geist | `getComputedStyle(...).fontFamily` | `!important` preservando a fonte de ícones |
| Captura headless salvou o esqueleto de carregamento | Primeiro screenshot | Playwright esperando o card renderizar |
| Asteriscos literais no detalhe | Revisão do screenshot de alta resolução | Texto sem Markdown |
| Minha checagem acusou 33 falhas falsas | O nome completo saiu da tela (pedido do usuário) | Checagem passou a validar saudação e links |

## Ajuste pedido durante a etapa
- "Troque o nome para o vendedor selecionado ou manager": a saudação usa o primeiro nome da pessoa em foco ("Good morning, Maureen"). Em Região e Time todo, que não têm uma pessoa, usa quem opera o app. Coberto por teste.
