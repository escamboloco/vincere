# -*- coding: utf-8 -*-
"""
in-Dependência · Comunidade — backend real (Flask + SQLite)
Cadastro de usuário, fórum, painel de jornada (dias limpos/economia) e admin de moderação.

Rodar localmente:
    pip install -r requirements.txt --break-system-packages
    python3 app.py
Criar o primeiro administrador:
    python3 criar_admin.py "Apelido" email@exemplo.com "senha-forte"
"""
import os, re, sqlite3, unicodedata, time
from datetime import datetime, date
from functools import wraps
from flask import (Flask, g, request, session, redirect, url_for,
                    render_template, flash, abort)
from werkzeug.security import generate_password_hash, check_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "comunidade.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "troque-esta-chave-antes-de-publicar-" + os.urandom(8).hex())

NUM_ZAP = os.environ.get("NUM_ZAP", "5511917311001")

CATEGORIAS_SEED = [
    ("apresente-se", "Apresente-se", "Novo por aqui? Conte, sem pressa, o que te trouxe até a comunidade.", 1),
    ("vitorias", "Vitórias e marcos", "24 horas, 30 dias, 1 ano — celebre aqui. Toda conquista merece testemunha.", 2),
    ("dias-dificeis", "Dias difíceis · peça apoio", "Fissura, vontade de desistir, um gatilho forte. Aqui ninguém julga.", 3),
    ("duvidas-tratamento", "Dúvidas sobre tratamento", "Perguntas sobre consulta, residência, CAPS-AD, medicação, o que for.", 4),
    ("para-familiares", "Para familiares", "Espaço de quem ama e cuida — cansaço, limites, como ajudar sem adoecer.", 5),
]

# palavras que sinalizam risco imediato — não bloqueiam a postagem (silenciar um pedido de ajuda
# seria pior), mas priorizam revisão humana e mostram recurso de crise na hora, para o autor.
_PALAVRAS_CRISE = [
    "quero morrer", "vou me matar", "nao aguento mais viver", "acabar com a minha vida",
    "acabar com tudo", "nao quero mais viver", "melhor eu morrer", "tirar minha vida",
    "sem saida", "suicidio", "me matar",
]

def _normaliza(t):
    t = unicodedata.normalize("NFD", t.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")

def contem_sinal_de_crise(texto):
    n = _normaliza(texto)
    return any(p in n for p in _PALAVRAS_CRISE)

# --------------------------------------------------------------- banco
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def fecha_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    primeira_vez = not os.path.exists(DB_PATH)
    db = sqlite3.connect(DB_PATH)
    with open(os.path.join(BASE, "schema.sql"), encoding="utf-8") as f:
        db.executescript(f.read())
    if db.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] == 0:
        db.executemany("INSERT INTO categorias(slug,nome,descricao,ordem) VALUES (?,?,?,?)", CATEGORIAS_SEED)
    db.commit()
    db.close()
    if primeira_vez:
        print("Banco criado em", DB_PATH, "— rode criar_admin.py para o primeiro administrador.")

# --------------------------------------------------------------- auxiliares
def usuario_atual():
    uid = session.get("uid")
    if not uid:
        return None
    row = get_db().execute("SELECT * FROM usuarios WHERE id=?", (uid,)).fetchone()
    if row is None or row["banido"]:
        session.clear()
        return None
    return row

@app.context_processor
def injeta_globais():
    return {"usuario": usuario_atual(), "num_zap": NUM_ZAP}

def login_obrigatorio(fn):
    @wraps(fn)
    def wrap(*a, **kw):
        if usuario_atual() is None:
            flash("Entre na sua conta para continuar.", "aviso")
            return redirect(url_for("entrar", proximo=request.path))
        return fn(*a, **kw)
    return wrap

def admin_obrigatorio(fn):
    @wraps(fn)
    def wrap(*a, **kw):
        u = usuario_atual()
        if u is None or u["tipo"] != "admin":
            abort(403)
        return fn(*a, **kw)
    return wrap

_ultimo_post_por_usuario = {}
def pode_postar(uid):
    """Limite simples: 1 postagem a cada 15s por usuário, para reduzir spam/flood."""
    agora = time.time()
    ultimo = _ultimo_post_por_usuario.get(uid, 0)
    if agora - ultimo < 15:
        return False
    _ultimo_post_por_usuario[uid] = agora
    return True

def dias_limpos(sobrio_desde):
    if not sobrio_desde:
        return None
    try:
        d0 = date.fromisoformat(sobrio_desde)
    except ValueError:
        return None
    return max(0, (date.today() - d0).days)

app.jinja_env.filters["dias_limpos"] = dias_limpos

# --------------------------------------------------------------- auth
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        apelido = request.form.get("apelido", "").strip()[:40]
        email = request.form.get("email", "").strip().lower()[:120]
        senha = request.form.get("senha", "")
        tipo = request.form.get("tipo", "paciente")
        aceite = request.form.get("aceite")
        erros = []
        if not re.fullmatch(r"[A-Za-zÀ-ÿ0-9 _\-\.]{2,40}", apelido or ""):
            erros.append("Escolha um apelido de 2 a 40 caracteres (pode ser só um primeiro nome ou nome fictício).")
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""):
            erros.append("E-mail inválido.")
        if len(senha) < 8:
            erros.append("A senha precisa ter pelo menos 8 caracteres.")
        if tipo not in ("paciente", "familiar"):
            tipo = "paciente"
        if not aceite:
            erros.append("É preciso concordar com as diretrizes da comunidade para se cadastrar.")
        db = get_db()
        if not erros:
            if db.execute("SELECT 1 FROM usuarios WHERE email=?", (email,)).fetchone():
                erros.append("Já existe uma conta com este e-mail.")
            if db.execute("SELECT 1 FROM usuarios WHERE apelido=?", (apelido,)).fetchone():
                erros.append("Este apelido já está em uso — escolha outro.")
        if erros:
            for e in erros:
                flash(e, "erro")
            return render_template("cadastro.html", apelido=apelido, email=email, tipo=tipo)
        cur = db.execute(
            "INSERT INTO usuarios(apelido,email,senha_hash,tipo,criado_em) VALUES (?,?,?,?,?)",
            (apelido, email, generate_password_hash(senha), tipo, datetime.utcnow().isoformat()))
        db.commit()
        session["uid"] = cur.lastrowid
        flash("Bem-vindo(a) à comunidade — seu cadastro foi criado.", "ok")
        return redirect(url_for("perfil"))
    return render_template("cadastro.html", apelido="", email="", tipo="paciente")

@app.route("/entrar", methods=["GET", "POST"])
def entrar():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        row = get_db().execute("SELECT * FROM usuarios WHERE email=?", (email,)).fetchone()
        if row and not row["banido"] and check_password_hash(row["senha_hash"], senha):
            session["uid"] = row["id"]
            flash("Login realizado.", "ok")
            return redirect(request.args.get("proximo") or url_for("comunidade_home"))
        flash("E-mail ou senha incorretos.", "erro")
    return render_template("entrar.html")

@app.route("/sair")
def sair():
    session.clear()
    flash("Você saiu da conta.", "ok")
    return redirect(url_for("comunidade_home"))

# --------------------------------------------------------------- perfil / jornada
@app.route("/perfil", methods=["GET", "POST"])
@login_obrigatorio
def perfil():
    u = usuario_atual()
    db = get_db()
    if request.method == "POST":
        sobrio_desde = request.form.get("sobrio_desde") or None
        try:
            gasto = float(request.form.get("gasto_semanal") or 0)
        except ValueError:
            gasto = 0
        if sobrio_desde:
            try:
                if date.fromisoformat(sobrio_desde) > date.today():
                    sobrio_desde = date.today().isoformat()
            except ValueError:
                sobrio_desde = None
        db.execute("UPDATE usuarios SET sobrio_desde=?, gasto_semanal=? WHERE id=?",
                   (sobrio_desde, max(0, gasto), u["id"]))
        db.commit()
        flash("Painel atualizado.", "ok")
        return redirect(url_for("perfil"))
    dl = dias_limpos(u["sobrio_desde"])
    economia = round(dl / 7 * u["gasto_semanal"], 2) if dl is not None and u["gasto_semanal"] else None
    meus_topicos = db.execute(
        "SELECT t.*, c.nome AS cat_nome FROM topicos t JOIN categorias c ON c.id=t.categoria_id "
        "WHERE t.usuario_id=? ORDER BY t.criado_em DESC LIMIT 10", (u["id"],)).fetchall()
    return render_template("perfil.html", u=u, dias=dl, economia=economia, meus_topicos=meus_topicos)

@app.route("/perfil/excluir", methods=["POST"])
@login_obrigatorio
def excluir_conta():
    """Autoatendimento LGPD (direito ao esquecimento): apaga os dados pessoais
    identificáveis (e-mail, senha, apelido, dados de jornada) e anonimiza as
    mensagens já publicadas. A linha do usuário é mantida (anonimizada, com
    login desativado) em vez de removida por completo, porque tópicos e
    respostas de outras pessoas referenciam esse registro — apagar a linha
    quebraria essas conversas para todo mundo. O efeito para quem pediu a
    exclusão é o mesmo: nenhum dado pessoal identificável permanece."""
    u = usuario_atual()
    db = get_db()
    db.execute("UPDATE posts SET corpo='[mensagem removida — autor excluiu a conta]', removido=1 WHERE usuario_id=?", (u["id"],))
    db.execute(
        "UPDATE usuarios SET apelido=?, email=?, senha_hash=?, sobrio_desde=NULL, "
        "gasto_semanal=0, banido=1 WHERE id=?",
        (f"conta-excluida-{u['id']}", f"excluido-{u['id']}@removido.local",
         generate_password_hash(os.urandom(16).hex()), u["id"]))
    db.commit()
    session.clear()
    flash("Sua conta e seus dados pessoais foram excluídos.", "ok")
    return redirect(url_for("comunidade_home"))

# --------------------------------------------------------------- fórum
@app.route("/")
@app.route("/comunidade")
def comunidade_home():
    db = get_db()
    categorias = db.execute("SELECT * FROM categorias ORDER BY ordem").fetchall()
    contagens = {r["categoria_id"]: r["n"] for r in db.execute(
        "SELECT categoria_id, COUNT(*) AS n FROM topicos GROUP BY categoria_id").fetchall()}
    recentes = db.execute(
        "SELECT t.*, c.nome AS cat_nome, c.slug AS cat_slug, u.apelido, "
        "(SELECT COUNT(*) FROM posts p WHERE p.topico_id=t.id AND p.removido=0) AS n_posts "
        "FROM topicos t JOIN categorias c ON c.id=t.categoria_id JOIN usuarios u ON u.id=t.usuario_id "
        "ORDER BY t.criado_em DESC LIMIT 12").fetchall()
    return render_template("home.html", categorias=categorias, contagens=contagens, recentes=recentes)

@app.route("/comunidade/<slug>")
def categoria_view(slug):
    db = get_db()
    cat = db.execute("SELECT * FROM categorias WHERE slug=?", (slug,)).fetchone()
    if not cat:
        abort(404)
    topicos = db.execute(
        "SELECT t.*, u.apelido, (SELECT COUNT(*) FROM posts p WHERE p.topico_id=t.id AND p.removido=0) AS n_posts "
        "FROM topicos t JOIN usuarios u ON u.id=t.usuario_id WHERE t.categoria_id=? "
        "ORDER BY t.fixado DESC, t.criado_em DESC", (cat["id"],)).fetchall()
    return render_template("categoria.html", cat=cat, topicos=topicos)

@app.route("/comunidade/<slug>/novo", methods=["GET", "POST"])
@login_obrigatorio
def novo_topico(slug):
    db = get_db()
    cat = db.execute("SELECT * FROM categorias WHERE slug=?", (slug,)).fetchone()
    if not cat:
        abort(404)
    if request.method == "POST":
        u = usuario_atual()
        titulo = request.form.get("titulo", "").strip()[:140]
        corpo = request.form.get("corpo", "").strip()[:4000]
        if len(titulo) < 4 or len(corpo) < 10:
            flash("Escreva um título (mín. 4 caracteres) e uma mensagem (mín. 10 caracteres).", "erro")
            return render_template("novo_topico.html", cat=cat, titulo=titulo, corpo=corpo)
        if not pode_postar(u["id"]):
            flash("Você acabou de postar — aguarde alguns segundos antes de tentar de novo.", "erro")
            return render_template("novo_topico.html", cat=cat, titulo=titulo, corpo=corpo)
        agora = datetime.utcnow().isoformat()
        cur = db.execute("INSERT INTO topicos(categoria_id,usuario_id,titulo,criado_em) VALUES (?,?,?,?)",
                          (cat["id"], u["id"], titulo, agora))
        topico_id = cur.lastrowid
        crise = contem_sinal_de_crise(titulo + " " + corpo)
        db.execute("INSERT INTO posts(topico_id,usuario_id,corpo,criado_em,sinalizado_crise) VALUES (?,?,?,?,?)",
                   (topico_id, u["id"], corpo, agora, int(crise)))
        db.commit()
        if crise:
            flash("Percebemos que você pode estar passando por um momento muito difícil. "
                  "Se for uma emergência, ligue 188 (CVV, 24h, gratuito) ou 192 (SAMU). "
                  "Sua mensagem foi publicada e também sinalizada para nossa equipe.", "crise")
        return redirect(url_for("topico_view", topico_id=topico_id))
    return render_template("novo_topico.html", cat=cat, titulo="", corpo="")

@app.route("/comunidade/topico/<int:topico_id>", methods=["GET", "POST"])
def topico_view(topico_id):
    db = get_db()
    topico = db.execute(
        "SELECT t.*, u.apelido, c.nome AS cat_nome, c.slug AS cat_slug "
        "FROM topicos t JOIN usuarios u ON u.id=t.usuario_id JOIN categorias c ON c.id=t.categoria_id "
        "WHERE t.id=?", (topico_id,)).fetchone()
    if not topico:
        abort(404)
    if request.method == "POST":
        u = usuario_atual()
        if u is None:
            flash("Entre na sua conta para responder.", "aviso")
            return redirect(url_for("entrar", proximo=request.path))
        corpo = request.form.get("corpo", "").strip()[:4000]
        if len(corpo) < 3:
            flash("Escreva uma resposta um pouco maior.", "erro")
        elif not pode_postar(u["id"]):
            flash("Você acabou de postar — aguarde alguns segundos antes de tentar de novo.", "erro")
        else:
            agora = datetime.utcnow().isoformat()
            crise = contem_sinal_de_crise(corpo)
            db.execute("INSERT INTO posts(topico_id,usuario_id,corpo,criado_em,sinalizado_crise) VALUES (?,?,?,?,?)",
                       (topico_id, u["id"], corpo, agora, int(crise)))
            db.commit()
            if crise:
                flash("Percebemos que você pode estar passando por um momento muito difícil. "
                      "Se for uma emergência, ligue 188 (CVV, 24h, gratuito) ou 192 (SAMU). "
                      "Sua mensagem foi publicada e também sinalizada para nossa equipe.", "crise")
        return redirect(url_for("topico_view", topico_id=topico_id))
    posts = db.execute(
        "SELECT p.*, u.apelido, u.tipo AS autor_tipo FROM posts p JOIN usuarios u ON u.id=p.usuario_id "
        "WHERE p.topico_id=? ORDER BY p.criado_em ASC", (topico_id,)).fetchall()
    return render_template("topico.html", topico=topico, posts=posts)

@app.route("/comunidade/post/<int:post_id>/denunciar", methods=["POST"])
@login_obrigatorio
def denunciar(post_id):
    u = usuario_atual()
    db = get_db()
    post = db.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone()
    if not post:
        abort(404)
    motivo = request.form.get("motivo", "").strip()[:300]
    db.execute("INSERT INTO denuncias(post_id,usuario_id,motivo,criado_em) VALUES (?,?,?,?)",
               (post_id, u["id"], motivo, datetime.utcnow().isoformat()))
    db.commit()
    flash("Obrigado — a mensagem foi enviada para revisão da equipe.", "ok")
    return redirect(url_for("topico_view", topico_id=post["topico_id"]))

# --------------------------------------------------------------- admin
@app.route("/admin")
@admin_obrigatorio
def admin_home():
    db = get_db()
    denuncias = db.execute(
        "SELECT d.*, p.corpo AS post_corpo, p.topico_id, p.sinalizado_crise, "
        "au.apelido AS autor_post, ru.apelido AS quem_denunciou "
        "FROM denuncias d JOIN posts p ON p.id=d.post_id JOIN usuarios au ON au.id=p.usuario_id "
        "JOIN usuarios ru ON ru.id=d.usuario_id WHERE d.resolvida=0 ORDER BY d.criado_em DESC").fetchall()
    crise = db.execute(
        "SELECT p.*, u.apelido, t.titulo, t.id AS topico_id FROM posts p "
        "JOIN usuarios u ON u.id=p.usuario_id JOIN topicos t ON t.id=p.topico_id "
        "WHERE p.sinalizado_crise=1 AND p.removido=0 ORDER BY p.criado_em DESC LIMIT 20").fetchall()
    usuarios = db.execute("SELECT * FROM usuarios ORDER BY criado_em DESC LIMIT 50").fetchall()
    totais = db.execute(
        "SELECT (SELECT COUNT(*) FROM usuarios) AS n_usuarios, "
        "(SELECT COUNT(*) FROM topicos) AS n_topicos, "
        "(SELECT COUNT(*) FROM posts WHERE removido=0) AS n_posts").fetchone()
    return render_template("admin.html", denuncias=denuncias, crise=crise, usuarios=usuarios, totais=totais)

@app.route("/admin/post/<int:post_id>/remover", methods=["POST"])
@admin_obrigatorio
def admin_remover_post(post_id):
    db = get_db()
    db.execute("UPDATE posts SET removido=1 WHERE id=?", (post_id,))
    db.execute("UPDATE denuncias SET resolvida=1 WHERE post_id=?", (post_id,))
    db.commit()
    flash("Mensagem removida.", "ok")
    return redirect(url_for("admin_home"))

@app.route("/admin/denuncia/<int:den_id>/dispensar", methods=["POST"])
@admin_obrigatorio
def admin_dispensar_denuncia(den_id):
    db = get_db()
    db.execute("UPDATE denuncias SET resolvida=1 WHERE id=?", (den_id,))
    db.commit()
    flash("Denúncia marcada como revisada, sem remoção.", "ok")
    return redirect(url_for("admin_home"))

@app.route("/admin/usuario/<int:uid>/banir", methods=["POST"])
@admin_obrigatorio
def admin_banir(uid):
    db = get_db()
    db.execute("UPDATE usuarios SET banido=1-banido WHERE id=? AND tipo!='admin'", (uid,))
    db.commit()
    flash("Status do usuário atualizado.", "ok")
    return redirect(url_for("admin_home"))

# --------------------------------------------------------------- boot
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    app.run(host="0.0.0.0", port=port, debug=False)
