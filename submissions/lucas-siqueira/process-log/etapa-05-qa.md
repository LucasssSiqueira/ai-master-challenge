# Etapa 05 — Quality Assurance & Technical Audit

Auditoria completa em `docs/08-quality-assurance.md`. Resumo do processo:

1. **Auditoria antes de corrigir:** scripts independentes recalcularam os totais direto do CSV bruto, testaram limites do score, todas as 37 combinações de filtro (Streamlit AppTest) e a seleção de linhas no navegador real.
2. **Achados que só apareceram testando de verdade:**
   - O crash ao trocar de vendedor com uma linha selecionada (P0) só aparece no navegador; o AppTest não simula a seleção.
   - As versões mínimas do `requirements.txt` nunca tinham sido instaladas. Testá-las revelou dois P1 (numpy/pyarrow e `width="stretch"` no Streamlit < 1.49).
   - A data de referência "ajustável" usava o futuro no histórico (P1). O bug só aparece ao mudar a configuração, que a documentação convidava a fazer.
3. **Erros meus durante a auditoria:**
   - Contei 12 duplicatas olhando só os deals abertos; o teste mostrou 13 (um aberto cujo gêmeo já fechou). Corrigi o teste, não o código.
   - Um servidor antigo continuou rodando após uma troca de versão, porque o comando que o encerraria foi bloqueado. Os primeiros resultados com o Streamlit 1.49 vinham do processo velho; reiniciei e refiz o teste.
   - O primeiro rascunho do doc 08 contava 6 itens P3 (eram 5) e citava a versão errada do numpy. Corrigido após conferência.
4. **Resultado:** 1 P0, 3 P1 e 5 P2 corrigidos, com testes de regressão (41 no total) e evidência no navegador (screenshots 06 e 07). Pendentes: 2 P3 e o CA9, que precisa de uma pessoa.
