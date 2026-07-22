CREATE TABLE IF NOT EXISTS usuarios (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  apelido TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  senha_hash TEXT NOT NULL,
  tipo TEXT NOT NULL DEFAULT 'paciente',           -- paciente | familiar | admin
  sobrio_desde TEXT,                                -- data ISO, opcional
  gasto_semanal REAL NOT NULL DEFAULT 0,
  banido INTEGER NOT NULL DEFAULT 0,
  criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categorias (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  slug TEXT UNIQUE NOT NULL,
  nome TEXT NOT NULL,
  descricao TEXT NOT NULL,
  ordem INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS topicos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  categoria_id INTEGER NOT NULL REFERENCES categorias(id),
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
  titulo TEXT NOT NULL,
  criado_em TEXT NOT NULL,
  fixado INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS posts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  topico_id INTEGER NOT NULL REFERENCES topicos(id),
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
  corpo TEXT NOT NULL,
  criado_em TEXT NOT NULL,
  removido INTEGER NOT NULL DEFAULT 0,
  sinalizado_crise INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS denuncias (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  post_id INTEGER NOT NULL REFERENCES posts(id),
  usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
  motivo TEXT,
  criado_em TEXT NOT NULL,
  resolvida INTEGER NOT NULL DEFAULT 0
);
