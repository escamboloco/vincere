# in-Dependência · Comunidade (backend real)

Serviço **separado** do site estático (`in-dependencia-portal.zip`). Este é um
aplicativo Flask de verdade, com banco de dados, senhas com hash e um painel
de administração real — precisa rodar como processo vivo, não como site estático.

Testado de ponta a ponta antes da entrega: cadastro, login, hash de senha,
criação de tópico, resposta, denúncia, sinalização automática de risco,
painel de admin, remoção de mensagem, banimento e exclusão de conta (LGPD) —
16 cenários, todos passando contra o servidor real.

## O que tem

- **Cadastro e login** de verdade (senha com hash `scrypt`, nunca texto puro)
- **Fórum** com 5 categorias (Apresente-se, Vitórias, Dias difíceis, Dúvidas
  sobre tratamento, Para familiares), tópicos e respostas
- **Painel de jornada** por conta (não mais só no navegador): dias limpos e
  economia calculados no servidor, sincronizados entre dispositivos
- **Denúncia de mensagem** por qualquer usuário logado
- **Sinalização automática de risco**: mensagens com sinais de ideação
  suicida são publicadas normalmente (nunca silenciadas) e priorizadas na
  fila do admin, além de mostrar na hora um aviso com CVV 188 / SAMU 192
  para quem escreveu
- **Limite de flood**: 1 postagem a cada 15s por conta
- **Admin real**: fila de denúncias, fila de mensagens de risco, remoção de
  mensagem, banir/desbanir usuário — tudo atrás de checagem de sessão no
  servidor (não é um botão de JavaScript, é controle de acesso de verdade)
- **Exclusão de conta (LGPD)**: o próprio usuário apaga e-mail, senha e
  apelido; mensagens já publicadas são anonimizadas, não apagadas — porque
  apagar a linha quebraria os tópicos de quem respondeu a ela

## Rodando localmente

```bash
cd comunidade
pip install -r requirements.txt --break-system-packages
python3 app.py            # cria comunidade.db na primeira vez, sobe em :8004
```
Em outro terminal, crie o primeiro administrador:
```bash
python3 criar_admin.py "Equipe in-Dependência" admin@seudominio.com "uma-senha-forte-de-verdade"
```
Abra `http://localhost:8004`.

## Publicando (Render)

Este é um **Web Service** (processo vivo), não um Static Site:
1. Render → New → **Web Service** → aponte para a pasta `comunidade/`.
2. Build command: `pip install -r requirements.txt`
3. Start command: `gunicorn app:app` (já incluso em `Procfile`)
4. Variáveis de ambiente obrigatórias:
   - `SECRET_KEY`: uma string aleatória longa (sem ela, todo mundo é
     deslogado a cada reinício, e o valor padrão do código não é seguro
     para produção)
   - `NUM_ZAP`: o número real do WhatsApp (rodapé do fórum)
5. **Banco de dados**: por padrão usa um arquivo SQLite (`comunidade.db`) no
   disco do serviço. **O disco do Render é efêmero em planos sem "Persistent
   Disk"** — a cada deploy, o banco pode ser apagado. Para produção real,
   escolha uma destas duas opções antes de divulgar o fórum:
   - Ativar um **Persistent Disk** no Render e apontar `DB_PATH` para ele; ou
   - Migrar para **PostgreSQL** (Render oferece um banco gerenciado) — é a
     opção recomendada para uma comunidade com usuários de verdade.
6. Depois de publicado, pegue a URL real do serviço e atualize a constante
   `COMUNIDADE_URL` em `build/montar2.py` (site principal) e reconstrua o
   site estático — hoje ela aponta para um endereço-exemplo.

## Segurança e privacidade — decisões importantes

- Senhas: `werkzeug.security` com `scrypt`, nunca texto puro.
- Sessão: cookie assinado pelo Flask (`SECRET_KEY`); troque o valor padrão.
- Controle de admin: verificado no servidor a cada requisição (`tipo=='admin'`
  no banco), não por um campo escondido no HTML.
- **Este código constrói a infraestrutura técnica de moderação — ele não
  substitui moderação humana.** Um fórum de dependência química real precisa
  de pessoas revisando a fila de denúncias e de risco em um SLA definido
  (ex.: menos de algumas horas). O admin criado aqui é a ferramenta; a
  operação contínua é responsabilidade de quem publica o site.
- A sinalização de crise é por palavra-chave — é um auxílio de priorização,
  não um filtro perfeito. Nunca bloqueia a publicação da mensagem: silenciar
  um pedido de ajuda seria pior do que deixá-lo passar sem sinalização.
- Diretrizes da comunidade (sem doses, sem incentivo ao uso, sem julgamento)
  aparecem no formulário de novo tópico e na aceitação obrigatória do
  cadastro — mas dependem de moderação humana para valer na prática.

## O que NÃO está incluso (próximos passos possíveis)

- Recuperação de senha por e-mail (hoje não há envio de e-mail configurado)
- Notificações (nova resposta no meu tópico)
- Mensagens privadas entre usuários
- Edição/exclusão do próprio post pelo autor
- Paginação (hoje a home lista os 12 tópicos mais recentes; em volume alto,
  vale paginar)

Nenhum desses foi fingido ou simulado — foram propositalmente deixados de
fora desta entrega para manter o núcleo (auth + fórum + moderação + LGPD)
sólido e testado, em vez de espalhar em funcionalidades meio-prontas.
