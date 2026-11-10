# in-Dependência — portal estático

Site HTML estático hospedado no Hostinger (hospedagem web, plano Business),
no domínio https://www.in-dependencia.com.

## Publicar
O site `in-dependencia.com` no hPanel clona a branch `main` deste repositório
direto para a `public_html` (hPanel → Sites → Gerenciar → Avançado → Git).
Depois de um push na `main`, clique em **Implantar** nessa tela para puxar a
versão nova — ou ative a implantação automática (webhook) ali mesmo.

Não há build: os arquivos são servidos como estão. Regras de redirecionamento
e bloqueio ficam no `.htaccess`.

## Estrutura
/, /jornada/, /testes/, /consulta/, /residencia/, /sos/, /diario/,
/plano-de-conversa/, /glossario/, /apoio-gratuito/, /painel/, /blog/
