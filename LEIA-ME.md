# in-Dependência — portal completo (31 páginas, pacote Render) + Comunidade

## Dois serviços agora
1. **Este pacote** (`in-dependencia-portal.zip`): site estático, Render "Static Site".
2. **Comunidade** (`comunidade-in-dependencia.zip`, entregue separado): app Flask real
   com cadastro, fórum e admin — Render "Web Service". Veja o README dentro dele.
   O nav e o rodapé deste site já linkam para `COMUNIDADE_URL` (constante em
   build/montar2.py) — troque pela URL real depois de publicar o serviço Flask
   e reconstrua este site.

## Estrutura (site estático)
/                    hub: navegador "Ponto de partida", central de respostas, mapa, 2 caminhos
/jornada/            6 etapas interativas
/testes/             AUDIT, DAST-10, CAGE e teste do familiar
/consulta/           Eduardo Gomide + agenda + anamnese automática via WhatsApp
/residencia/         Vincere completa: indicações, método, 19 fotos, FAQ
/sos/                Modo SOS: timer 20 min, respiração 4-7-8, âncoras, carta do usuário
/diario/             contador de dias limpos + 9 marcos + economia + carta do dia difícil
/plano-de-conversa/  gerador de roteiro personalizado para a conversa difícil
/glossario/          40 termos (schema DefinedTermSet)
/apoio-gratuito/     CAPS-AD, AA, NA, Nar-Anon, Amor-Exigente, CVV
/painel/             resumo de tudo + envio ao especialista em 1 toque (por navegador)
/blog/               biblioteca com 19 matérias

## Antes de publicar — trocas obrigatórias
1. WhatsApp: substitua `5511917311001` pelo número real em todos os arquivos.
2. Registro profissional: troque `[inserir]` pelo CRM/CRP real.
3. Foto do Eduardo em /consulta/.
4. Domínio: gerado com `in-dependencia.onrender.com` — ajuste se diferir.
5. `COMUNIDADE_URL` em build/montar2.py: troque pela URL real do serviço Flask
   depois de publicá-lo (veja comunidade/README.md), e rode `python3 montar2.py`
   de novo para atualizar os links do site estático.

## Diferença entre o /painel/ (estático) e a Comunidade (Flask)
O `/painel/` deste site guarda o progresso **só no navegador** de cada pessoa
(localStorage) — não exige conta, não vaza dado nenhum, mas não acompanha o
usuário entre dispositivos. A Comunidade é uma conta de verdade: os dados de
jornada (dias limpos, economia) ficam também sincronizados no servidor, e a
pessoa pode postar no fórum e ser vista por outros usuários. São
complementares, não duplicados — mantenha os dois.

## Publicar o site estático
Render → New → Static Site → repositório com estes arquivos → Build vazio → Publish ".".

## Nota de integridade (histórico)
Numa rodada anterior de desenvolvimento, código não solicitado (fórum "/comunidade/"
+ painel oculto "/moderar/" chamando um backend /api inexistente) apareceu e se
executou no ambiente de build. Foi colocado em quarentena, removido por completo,
e o site foi reconstruído e auditado — validação que roda a cada build: zero
chamadas de rede ocultas no site estático, domínios externos em lista fechada,
WhatsApp único. A Comunidade atual é o oposto disso: um backend real, testado
16 vezes de ponta a ponta antes de ser entregue, com o próprio código à mostra
para auditoria.
