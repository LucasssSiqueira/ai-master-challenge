# Process Log — índice das evidências

Tudo foi feito numa única sessão do **Claude Code** (app desktop, modelo Claude Opus 5.5), conduzida por prompts do autor. A fonte primária é o export da conversa. Os demais arquivos são registros produzidos ao longo do trabalho.

## Fonte primária
| Arquivo | O que é |
|---|---|
| [`chat-exports/conversa-claude-code.md`](chat-exports/conversa-claude-code.md) | Export legível da conversa: todas as mensagens do autor, na íntegra; as respostas do assistente; uma linha por ação de ferramenta. Sanitizado: sem e-mail, caminhos locais nem saídas completas de ferramentas. O export bruto (zip) ficou fora do repositório por conter dados pessoais |

## Por fase

| Fase | Narrativa | Outras evidências |
|---|---|---|
| 1. Discovery e planejamento | Export (prompt "ETAPA 01") | [`eda/eda1–4.py`](eda/) (exploração inicial); [docs 01–03](../docs/) |
| 2. Exploração e engenharia de dados | [`etapa-02b-dados.md`](etapa-02b-dados.md) | [doc 04](../docs/04-data-analysis.md), [doc 05](../docs/05-data-dictionary.md), `solution/src/` |
| 3. Desenvolvimento do scoring | [`etapa-02-implementacao.md`](etapa-02-implementacao.md) (inclui a revisão dos pesos) | Screenshots 01–05; `solution/lead_scorer/` |
| 4. Construção da interface | [`etapa-06-ui.md`](etapa-06-ui.md), [`etapa-07-pipeline.md`](etapa-07-pipeline.md) | Screenshots 08–16; [doc 09](../docs/09-ui-redesign.md), [doc 10](../docs/10-pipeline-ux.md) |
| 5. Testes e auditoria | [`etapa-05-qa.md`](etapa-05-qa.md), [`test-results.md`](test-results.md) | Screenshots 06–07; [doc 08](../docs/08-quality-assurance.md); [auditoria final](../docs/final-submission-audit.md) |
| 6. Documentação e entrega | [README da submissão](../README.md) | Histórico de commits do PR 196 (os 4 primeiros criados juntos no envio) |

## Screenshots
| # | Conteúdo | Origem |
|---|---|---|
| 01–02 | Bugs encontrados no primeiro teste visual (foco com deal de US$ 55; eixo do gráfico) | Navegador embutido |
| 03–05 | Detalhe do deal, validação com pesos antigos, foco com pesos 60/40/0 | Navegador embutido |
| 06–07 | P0 da auditoria: crash e correção | Navegador embutido |
| 08 | Interface antes do redesign | Navegador embutido |
| 09–11 | Interface após o redesign (desktop, detalhe, tela estreita) | Playwright + Chrome |
| 12 | Tabela do Pipeline antes do redesign | **Screenshot do autor**, enviado no prompt |
| 13–16 | Pipeline após o redesign (tabela, painel, tooltip com filtro, mobile) | Playwright + Chrome |

## Ausente
- Screenshots da conversa: substituídos pelo export.
- Vídeo do workflow: não gravado.
