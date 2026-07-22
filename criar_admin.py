# -*- coding: utf-8 -*-
"""Cria (ou promove) um usuário administrador.
Uso: python3 criar_admin.py "Apelido" email@exemplo.com "senha-forte-aqui"
"""
import sys, sqlite3, os
from datetime import datetime
from werkzeug.security import generate_password_hash

BASE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "comunidade.db")

def main():
    if len(sys.argv) != 4:
        print("Uso: python3 criar_admin.py \"Apelido\" email@exemplo.com \"senha-forte\"")
        sys.exit(1)
    apelido, email, senha = sys.argv[1], sys.argv[2].lower(), sys.argv[3]
    if len(senha) < 8:
        print("A senha precisa ter pelo menos 8 caracteres."); sys.exit(1)
    if not os.path.exists(DB_PATH):
        print("Banco não encontrado — rode 'python3 app.py' uma vez antes (ele cria o banco) e pare com Ctrl+C.")
        sys.exit(1)
    db = sqlite3.connect(DB_PATH)
    existente = db.execute("SELECT id FROM usuarios WHERE email=?", (email,)).fetchone()
    if existente:
        db.execute("UPDATE usuarios SET tipo='admin', senha_hash=?, apelido=? WHERE email=?",
                   (generate_password_hash(senha), apelido, email))
        print("Usuário existente promovido a admin:", email)
    else:
        db.execute("INSERT INTO usuarios(apelido,email,senha_hash,tipo,criado_em) VALUES (?,?,?,?,?)",
                   (apelido, email, generate_password_hash(senha), "admin", datetime.utcnow().isoformat()))
        print("Administrador criado:", email)
    db.commit(); db.close()

if __name__ == "__main__":
    main()
