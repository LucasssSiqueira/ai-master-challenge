# Auditoria final da submissão — Challenge 003 (Lead Scorer)

> Data: 15/10/2026 · Branch `submission/lucas-siqueira` · PR [Gestao-Quatro-Ponto-Zero/ai-master-challenge#196](https://github.com/Gestao-Quatro-Ponto-Zero/ai-master-challenge/pull/196) · Commit auditado: `cdd24fe`
> **Fontes oficiais:** o README do challenge, o `submission-guide.md`, o template e o `CONTRIBUTING.md` foram relidos do upstream na data da auditoria. O commit `4aed364` é idêntico ao lido na Etapa 01 (verificado com `diff`).
> **Método:** clone novo do PR, venv novo, só os comandos documentados ([resultados](../process-log/test-results.md)), mais inspeção do código, da documentação e do export da conversa.
> **Legenda:** Aprovado · Parcial · Não atendido · Não verificado

## A. Resumo executivo

**A aplicação funciona e cumpre todos os requisitos obrigatórios do desafio:**
- Roda a partir de um clone limpo seguindo o README.
- Usa os dados reais (8.800 deals reconciliados).
- Tem scoring que não é só "ordenar por valor" e explica cada score.
- Tem documentação de setup, lógica e limitações.
- A estrutura segue o `CONTRIBUTING.md`, e o PR só altera a pasta da submissão.

**A auditoria encontrou problemas na documentação, não no software:**
- Uma funcionalidade descrita que não existe mais.
- O process log não dizia quem detectou cada erro (a IA ou o humano).
- A seção "O que eu adicionei" tinha uma afirmação contrafactual sem evidência.
- O checklist de evidências havia sido alterado em relação ao template.
- O histórico de commits não é cronológico.

Todos foram corrigidos nesta revisão. Restam itens que **dependem do autor**, porque são afirmações em primeira pessoa e um teste com usuário real.

**Veredito: pronta para avaliação.** As duas ações que dependiam do autor foram concluídas em 15/10/2026:
1. A seção "O que eu adicionei" foi confirmada como está, e o autor declarou não ter usado outras ferramentas de IA.
2. O envio desta revisão ao PR 196 foi autorizado.

Nenhum problema crítico está em aberto. As pendências restantes (D.4 a D.7) são opcionais ou de baixa prioridade.

## B. Matriz de conformidade

### B.1 README do challenge (`build-003-lead-scorer`)

| Requisito | Status | Evidência | Ação |
|---|---|---|---|
| Solução funcional ("precisa rodar") | **Aprovado** | Clone limpo + `pip install` + `streamlit run`: health `ok`; 113 execuções AppTest sem erro ([test-results](../process-log/test-results.md)) | — |
| Usa os dados reais do dataset | **Aprovado** | 4 CSVs do Kaggle (CC0) em `solution/data/`; 8.800 linhas reconciliadas (`test_record_counts_reconcile`) | — |
| Lógica de scoring, não só ordenar por valor | **Aprovado** | Valor 60 + Momento 40 com faixas; Spearman 0,75 com o preço (`test_score_is_not_just_sorting_by_value`) | — |
| Vendedor entende por que o score é alto ou baixo | **Aprovado** | Motivos por deal (3–4), tooltip com Valor/Momento, painel com fatores; testes em `test_scoring`, `test_pipeline_table` e e2e | — |
| Doc: Setup | **Aprovado** | `solution/README.md` e README da submissão; comandos executados nesta auditoria | — |
| Doc: Lógica (critérios e porquê) | **Aprovado** | `solution/README.md` § Lógica, docs 02, 04, 08 e a página "Como o score funciona" | — |
| Doc: Limitações e o que precisa para escalar | **Aprovado** | `solution/README.md` § Limitações e Para escalar; README § Limitações | — |
| Process log (obrigatório) | **Aprovado** | `process-log/` + seção no README; export da conversa com todos os prompts; seção "O que eu adicionei" confirmada pelo autor | — |
| Bônus: filtro por vendedor/manager/região | **Aprovado** | Barra de escopo + filtro de vendedor no Pipeline (e2e `test_search_filters_and_reset`) | — |
| Critério: o scoring faz sentido e vai além do óbvio | **Aprovado** | Holdout temporal, snapshots point-in-time e backtest de pesos (doc 04, README) | — |
| Critério: vendedor não técnico consegue usar | **Não verificado** | Nenhum teste com usuário real (CA9) | Teste de corredor com 1 pessoa (opcional) |
| Critério: a interface ajuda a decidir | **Aprovado (inspeção)** | Prioridades do dia, insight com ação, fila de parados, ação por deal | — |
| Critério: código manutenível | **Aprovado** | Domínio em `lead_scorer/`, interface em `ui/`, 64 testes; ressalva P3 em C.3 | — |

### B.2 Guia de submissão e template

| Requisito | Status | Evidência | Ação |
|---|---|---|---|
| Solução + process log | **Aprovado** | `solution/`, `process-log/` | — |
| Process log: ferramentas e por quê | **Aprovado** | README § Ferramentas; o autor confirmou não ter usado outras ferramentas de IA | — |
| Process log: como decompôs o problema | **Aprovado** | Docs 01–03; prompts por etapa no export | — |
| Process log: onde a IA errou e como corrigiu | **Aprovado (corrigido)** | Tabela agora com quem detectou cada erro | — |
| Process log: o que o humano adicionou | **Aprovado** | Decisões comprovadas pelos prompts; seção confirmada pelo autor em 15/10/2026 | — |
| Process log: quantas iterações | **Aprovado** | 7 etapas e 15 mensagens do autor no export | — |
| Envio via Pull Request | **Aprovado** | PR 196 aberto, `MERGEABLE` | — |
| README segue o template | **Aprovado (corrigido)** | Seções do template na ordem; checklist de evidências restaurado como no template | — |

### B.3 `CONTRIBUTING.md`

| Requisito | Status | Evidência |
|---|---|---|
| Pasta `submissions/lucas-siqueira/` | **Aprovado** | 66 arquivos, 0 fora da pasta (`gh pr view --json files`) |
| `README.md` pelo template, `solution/`, `process-log/`, `docs/` | **Aprovado** | Estrutura da pasta |
| Instruções de setup incluídas | **Aprovado** | README e `solution/README.md` |
| Branch `submission/<nome>` e título `[Submission] Nome — Challenge XXX` | **Aprovado** | `submission/lucas-siqueira`; "[Submission] Lucas Siqueira — Challenge 003" |
| Um PR por pessoa, atualizações na mesma branch | **Aprovado** | Só o PR 196 |
| Não modificar arquivos fora da pasta | **Aprovado** | O `.gitignore` do upstream ignora `submissions/`; os arquivos foram adicionados com `git add -f`, sem alterar o `.gitignore` (mesmo procedimento de outros PRs, ex.: 191 e 192) |

### B.4 Auditoria técnica

| Item | Status | Evidência |
|---|---|---|
| Integridade do CRM (chaves e joins) | **Aprovado** | Validação de PK/FK, `validate="many_to_one"`, reconciliação de contagens (`test_data_processing.py`) |
| Tratamento de ausentes e vazamento | **Aprovado** | Política explícita de nulos; colunas de desfecho marcadas; data de referência reconstruída no ponto no tempo (`test_qa_regressions.py`) |
| Tratamento de erros | **Aprovado** | CSV ausente mostra mensagem amigável (AppTest); `DataQualityError` interrompe dados inconsistentes; não há `except` genérico |
| Segurança básica | **Aprovado** | Sem segredos, `eval` ou rede além do Google Fonts; todo HTML com escape; JSON embutido com `</` escapado (`test_data_cannot_break_out_of_the_script`) |
| Dependências e instalação | **Aprovado** | Versões mínimas testadas (doc 08); clone limpo testado nesta auditoria |
| Testes de unidade | **Aprovado** | 64 passed |
| Testes no navegador | **Parcial** | 13/13 em 3 de 4 execuções; 1 falha intermitente sem causa identificada ([test-results](../process-log/test-results.md)) |

## C. Problemas encontrados

### C.1 Críticos (poderiam comprometer a avaliação), todos corrigidos nesta revisão
1. **Afirmação falsa no README:** "As visões de gestão incluem o resumo por vendedor". Essa tabela foi removida no redesign da interface (`grep` no `app.py`: 0 ocorrências). Corrigido para descrever o filtro de vendedor e o vendedor em cada linha.
2. **Autoria dos erros no process log:** a seção "Onde a IA errou e como corrigi" sugeria que o autor detectou erros que, pelo export, foram detectados pela própria IA em testes ou auditorias. Para o avaliador, isso conta como julgamento humano. Agora cada linha diz **quem detectou**, com base no export.
3. **Contrafactual sem evidência:** "A IA teria partido direto para um score." Não há como comprovar. Removido.
4. **Atribuição incorreta:** "Critério de funciona de verdade: instalação limpa e teste no navegador" estava como decisão do autor. A instalação limpa foi iniciativa da IA; o autor exigiu "não declarar testes aprovados sem executá-los" (Etapa 05) e "executar a aplicação e verificar responsividade" (Pipeline). Reescrito com as palavras que constam nos prompts.

### C.2 Médios
5. **Histórico de commits não cronológico:** os 4 primeiros commits têm o mesmo horário (15/10 15:42), porque foram criados juntos no envio. O README agora diz isso; a cronologia real está no export da conversa.
6. **Checklist de evidências diferente do template:** o primeiro item do template ("Screenshots das conversas com IA") tinha sido trocado. Foi restaurado como no template, desmarcado, porque não existem screenshots de conversa; o export cobre esse papel.
7. **Falha intermitente no e2e:** 1 em 4 execuções, sem mensagem registrada. Documentada como pendência.

### C.3 Baixos (P3, sem correção: exigem mudar código funcional)
8. `app.py` repete "138 dias" no rótulo de Deals parados em vez de ler `config.stale_days`. Se o limite mudar, o rótulo fica errado.
9. Erros de pontuação no README (vírgulas na lista de docs e de narrativas). Corrigidos.

## D. Pendências

| # | Pendência | Responsável | Bloqueia a avaliação? |
|---|---|---|---|
| 1 | ~~Confirmar ou ajustar a seção "O que eu adicionei"~~ | Autor | ✅ Concluído em 15/10/2026 |
| 2 | ~~Autorizar o envio desta revisão ao PR 196~~ | Autor | ✅ Concluído em 15/10/2026 |
| 3 | ~~Confirmar se usou outra ferramenta de IA~~ | Autor | ✅ Não usou outras ferramentas |
| 4 | Teste com uma pessoa não técnica (CA9) | Autor | Não |
| 5 | Decidir se inclui o export bruto da conversa (zip no Downloads, contém e-mail e caminhos locais) ou um vídeo | Autor | Não (o export sanitizado já atende) |
| 6 | Causa da falha intermitente no e2e | Técnica | Não |
| 7 | Rótulo "138 dias" fixo em `app.py` (P3) | Técnica | Não |

## E. Qualidade da documentação

**Pontos fortes:**
- Cada número do README tem origem reproduzível (backtest, `exploratory_analysis.py`, testes).
- As limitações são honestas: a falta de sinal preditivo está declarada, sem precisão vendida.
- Fato e hipótese ficam separados nos docs 01 e 04.
- O process log tem erros reais, com screenshots de antes e depois.

**Pontos fracos (antes desta revisão):**
- O README ficou longo e acumulou descrições de versões anteriores da interface.
- Faltava distinguir o que foi decisão humana e o que foi iniciativa da IA.
- Os docs 01–03 descrevem o plano original (pesos 50/30/20, `st.dataframe`). São registros históricos; o doc 02 tem nota de atualização, mas um leitor apressado pode tomá-los como estado atual.
- `process-log/` não tinha um índice; agora tem [`process-log/README.md`](../process-log/README.md).

## F. Plano de correção (em ordem de prioridade)

1. ✅ Corrigir as afirmações falsas e as atribuições do README (C.1).
2. ✅ Restaurar o checklist do template e explicar o histórico de commits (C.2).
3. ✅ Registrar os resultados dos testes desta auditoria ([test-results](../process-log/test-results.md)).
4. ✅ Criar o índice do process log, organizado nas 6 etapas pedidas.
5. ✅ Autor confirmou a seção "O que eu adicionei" e que não usou outras ferramentas de IA.
6. ✅ Autor autorizou o envio ao PR 196.
7. Opcional: teste com um usuário (CA9), rótulo "138 dias" lido da configuração, investigação da falha intermitente.

## G. Checklist final

- [x] Li o README do challenge, o guia de submissão, o template e o `CONTRIBUTING.md` (versão atual do upstream)
- [x] Solução em `submissions/lucas-siqueira/`
- [x] Aplicação roda a partir de um clone limpo seguindo o README
- [x] Usa os dados reais; contagens reconciliadas
- [x] Scoring documentado e explicável
- [x] Testes executados: 64 de unidade; navegador 13/13 em 3 de 4 execuções
- [x] README com Setup, Lógica e Limitações, seguindo o template
- [x] Process log com ferramentas, workflow, erros (com quem detectou) e prompts (export)
- [x] Evidências organizadas e referenciadas (índice no `process-log/`)
- [x] Nenhum arquivo fora da pasta da submissão; título e branch no formato
- [x] Autor confirmou "O que eu adicionei"
- [x] Revisão enviada ao PR 196
- [ ] (Opcional) Teste com usuário real, CA9
