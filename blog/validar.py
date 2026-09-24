#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validador das materias da Biblioteca (in-Dependencia).

Este site nao tem build: cada materia e um index.html autocontido. Este script faz o
papel do build na etapa 6 da skill blog-post.

Uso:
    python blog/validar.py <slug> [--kw "palavra-chave primaria"]
    python blog/validar.py --todos          (checa estrutura de todas as materias)

Saida: lista de ERRO e AVISO. Codigo de saida 1 se houver qualquer ERRO.
"""

import json
import os
import re
import sys
import unicodedata

try:  # o console do Windows nao vem em UTF-8
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLOG = os.path.join(RAIZ, "blog")
HOST = "https://in-dependencia.onrender.com"

CATEGORIAS = {
    "Para famílias", "Escolhendo tratamento", "Tratamento", "Substâncias",
    "Recuperação", "Guia legal", "Saúde mental", "Entenda a adicção",
}

erros = []
avisos = []


def erro(msg):
    erros.append(msg)


def aviso(msg):
    avisos.append(msg)


def ler(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read()


def sem_tags(html):
    html = re.sub(r"<[^>]+>", " ", html)
    html = (html.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"'))
    return re.sub(r"\s+", " ", html).strip()


def bloco(html, inicio, fim):
    """Trecho entre dois marcadores, exclusivo. Devolve '' se nao achar."""
    i = html.find(inicio)
    if i < 0:
        return ""
    i += len(inicio)
    j = html.find(fim, i)
    return html[i:j] if j > 0 else html[i:]


def normalizar(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


# --------------------------------------------------------------------------- #
# checagens de repositorio (valem para qualquer execucao)
# --------------------------------------------------------------------------- #

def checar_repo(slug):
    for rel in ("blog/index.html", "sitemap.xml", "robots.txt"):
        caminho = os.path.join(RAIZ, rel)
        if not os.path.exists(caminho):
            erro("%s nao existe" % rel)
            continue
        if "<<<<<<<" in ler(caminho):
            erro("%s tem marcador de conflito de merge nao resolvido; "
                 "resolva o merge antes de publicar" % rel)

    if not slug:
        return

    indice = os.path.join(RAIZ, "blog", "index.html")
    if os.path.exists(indice):
        html = ler(indice)
        if ('href="/blog/%s/"' % slug) not in html:
            erro('blog/index.html nao tem o card do artigo (href="/blog/%s/")' % slug)

    mapa = os.path.join(RAIZ, "sitemap.xml")
    if os.path.exists(mapa):
        if ("%s/blog/%s/" % (HOST, slug)) not in ler(mapa):
            erro("sitemap.xml nao tem a <url> de %s/blog/%s/" % (HOST, slug))


# --------------------------------------------------------------------------- #
# checagens do artigo
# --------------------------------------------------------------------------- #

def checar_artigo(slug, keyword=None, completo=True):
    caminho = os.path.join(BLOG, slug, "index.html")
    if not os.path.exists(caminho):
        erro("blog/%s/index.html nao existe" % slug)
        return
    html = ler(caminho)

    if "<<<<<<<" in html:
        erro("[%s] marcador de conflito de merge dentro do artigo" % slug)

    # --- title ---------------------------------------------------------------
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    title = m.group(1).strip() if m else ""
    if not title:
        erro("[%s] sem <title>" % slug)
    elif len(title) > 65:
        erro("[%s] <title> com %d caracteres (limite 65): %s" % (slug, len(title), title))

    # --- meta description ----------------------------------------------------
    m = re.search(r'<meta name="description" content="(.*?)">', html, re.S)
    desc = m.group(1).strip() if m else ""
    if not desc:
        erro("[%s] sem meta description" % slug)
    elif not (140 <= len(desc) <= 160):
        erro("[%s] meta description com %d caracteres (faixa 140-160)" % (slug, len(desc)))

    # --- URLs canonicas ------------------------------------------------------
    url = "%s/blog/%s/" % (HOST, slug)
    for rotulo, padrao in (
        ("canonical", r'<link rel="canonical" href="(.*?)"'),
        ("og:url", r'<meta property="og:url" content="(.*?)"'),
    ):
        m = re.search(padrao, html)
        if not m:
            erro("[%s] sem %s" % (slug, rotulo))
        elif m.group(1) != url:
            erro("[%s] %s aponta para %s, esperado %s" % (slug, rotulo, m.group(1), url))

    # --- JSON-LD -------------------------------------------------------------
    tipos = {}
    for corpo in re.findall(
            r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        try:
            dado = json.loads(corpo)
        except ValueError as e:
            erro("[%s] JSON-LD invalido: %s" % (slug, e))
            continue
        tipos[dado.get("@type")] = dado

    for t in ("Article", "BreadcrumbList", "FAQPage"):
        if t not in tipos:
            erro("[%s] falta o bloco JSON-LD %s" % (slug, t))

    art = tipos.get("Article", {})
    if art:
        pub, mod = art.get("datePublished", ""), art.get("dateModified", "")
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", pub):
            erro("[%s] datePublished invalido: %r" % (slug, pub))
        if pub != mod:
            aviso("[%s] datePublished (%s) diferente de dateModified (%s)" % (slug, pub, mod))
        alvo = art.get("mainEntityOfPage", {})
        if isinstance(alvo, dict) and alvo.get("@id") != url:
            erro("[%s] JSON-LD mainEntityOfPage aponta para %r, esperado %s"
                 % (slug, alvo.get("@id"), url))

    # --- FAQ: HTML espelhado no JSON-LD --------------------------------------
    perg_html = [sem_tags(x) for x in
                 re.findall(r"<summary>(.*?)</summary>", html, re.S)]
    perg_ld = [q.get("name", "") for q in tipos.get("FAQPage", {}).get("mainEntity", [])]
    if perg_html and perg_ld and perg_html != perg_ld:
        erro("[%s] as perguntas do FAQ em HTML nao batem com as do JSON-LD FAQPage" % slug)
    if not perg_html:
        erro("[%s] sem bloco de FAQ no HTML" % slug)

    # --- corpo (.prosa) ------------------------------------------------------
    prosa = bloco(html, '<div class="prosa">', '</div><aside class="box-cta">')
    if not prosa:
        erro("[%s] nao encontrei o bloco <div class=\"prosa\">" % slug)
        return

    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    h1 = sem_tags(m.group(1)) if m else ""
    if not h1:
        erro("[%s] sem <h1>" % slug)

    # --- travessao (so no conteudo autoral; o CSS do portal usa travessao) ----
    for rotulo, trecho in (("title", title), ("meta description", desc),
                           ("h1", h1), ("corpo", prosa)):
        if "—" in trecho or "–" in trecho:
            erro("[%s] travessao encontrado em %s; a regra do DNA proibe" % (slug, rotulo))

    # --- tamanho -------------------------------------------------------------
    palavras = len(sem_tags(prosa).split())
    if not (900 <= palavras <= 1500):
        erro("[%s] corpo com %d palavras (faixa 900-1500)" % (slug, palavras))

    # --- H2 com id e sumario -------------------------------------------------
    h2s = re.findall(r'<h2 id="([^"]+)"', prosa)
    if not (3 <= len(h2s) <= 6):
        erro("[%s] %d secoes H2 com id (faixa 3-6)" % (slug, len(h2s)))

    sumario = bloco(html, '<nav class="sumario"', "</nav>")
    ancoras = [a for a in re.findall(r'href="#([^"]+)"', sumario) if a != "faq"]
    if ancoras and ancoras != h2s:
        erro("[%s] sumario nao bate com os ids dos H2: sumario=%s h2=%s"
             % (slug, ancoras, h2s))

    # --- lista pratica -------------------------------------------------------
    if "<ol" not in prosa and "<ul" not in prosa:
        erro("[%s] o corpo nao tem nenhuma lista; o DNA exige passos numerados "
             "ou lista pratica" % slug)

    # --- links internos ------------------------------------------------------
    internos = re.findall(r'href="(/[^"#]*)"', prosa)
    if len(internos) < 3:
        erro("[%s] apenas %d links internos no corpo (minimo 3)" % (slug, len(internos)))
    if not any(l.startswith(("/consulta", "/residencia")) for l in internos):
        erro("[%s] o corpo nao linka para /consulta/ nem para /residencia/" % slug)
    for destino in set(internos):
        alvo = os.path.join(RAIZ, destino.strip("/").replace("/", os.sep))
        if not (os.path.isdir(alvo) or os.path.exists(alvo)
                or os.path.exists(alvo + ".html")):
            erro("[%s] link interno quebrado: %s" % (slug, destino))

    # --- blocos obrigatorios -------------------------------------------------
    for classe, nome in (('class="box-aviso"', "aviso legal"),
                         ('class="revisao"', "bloco de revisao"),
                         ('class="box-cta"', "CTA"),
                         ('class="capa"', "capa SVG"),
                         ('class="migalhas"', "migalhas")):
        if classe not in html:
            erro("[%s] falta o %s (%s)" % (slug, nome, classe))

    if "[inserir]" not in html:
        aviso("[%s] o bloco de revisao nao traz mais o marcador [inserir] do registro "
              "profissional; confirme que o registro real foi preenchido" % slug)

    # --- categoria -----------------------------------------------------------
    indice = os.path.join(RAIZ, "blog", "index.html")
    if os.path.exists(indice):
        m = re.search(r'<a class="post" data-cat="([^"]+)" href="/blog/%s/"' % re.escape(slug),
                      ler(indice))
        if m and m.group(1) not in CATEGORIAS:
            erro("[%s] categoria %r fora do conjunto fechado do DNA" % (slug, m.group(1)))

    # --- palavra-chave -------------------------------------------------------
    if keyword:
        kw = normalizar(keyword)
        primeiro_p = ""
        m = re.search(r"<p>(.*?)</p>", prosa, re.S)
        if m:
            primeiro_p = sem_tags(m.group(1))
        alvos = {
            "title": title,
            "meta description": desc,
            "primeiro paragrafo": primeiro_p,
            "algum H2": " ".join(sem_tags(x) for x in
                                 re.findall(r"<h2[^>]*>(.*?)</h2>", prosa, re.S)),
        }
        for onde, texto in alvos.items():
            if kw not in normalizar(texto):
                erro("[%s] palavra-chave primaria %r ausente em: %s" % (slug, keyword, onde))

    if completo:
        print("[%s] %d palavras, %d secoes H2, %d links internos, %d perguntas no FAQ."
              % (slug, palavras, len(h2s), len(internos), len(perg_html)))


def main():
    args = [a for a in sys.argv[1:]]
    keyword = None
    if "--kw" in args:
        i = args.index("--kw")
        keyword = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]

    if not args:
        print(__doc__)
        return 2

    if args[0] == "--todos":
        checar_repo(None)
        slugs = sorted(d for d in os.listdir(BLOG)
                       if os.path.isdir(os.path.join(BLOG, d)))
        for s in slugs:
            checar_artigo(s, None, completo=False)
        print("%d materias verificadas." % len(slugs))
    else:
        slug = args[0].strip("/").replace("blog/", "")
        checar_repo(slug)
        checar_artigo(slug, keyword)

    for a in avisos:
        print("AVISO: %s" % a)
    for e in erros:
        print("ERRO: %s" % e)

    if erros:
        print("\nFALHOU: %d erro(s), %d aviso(s)." % (len(erros), len(avisos)))
        return 1
    print("\nOK: 0 erros, %d aviso(s)." % len(avisos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
