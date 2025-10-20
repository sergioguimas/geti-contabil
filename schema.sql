CREATE TABLE contador(  
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    senha_hash TEXT NOT NULL
);

CREATE TABLE empresa(
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
    razao_social TEXT NOT NULL,
    cnpj TEXT NOT NULL UNIQUE,
    g_drve_folder_id TEXT UNIQUE,
    nome_fantasia TEXT,
    email TEXT NOT NULL,
    contato TEXT NOT NULL,
    ativo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE contador_empresa(
    id_contador INTEGER NOT NULL,
    id_empresa INTEGER NOT NULL,
    PRIMARY KEY (id_contador,id_empresa),
    FOREIGN KEY (id_contador) REFERENCES contador(id) ON DELETE CASCADE,
    FOREIGN KEY (id_empresa) REFERENCES empresa(id) ON DELETE CASCADE
);

CREATE TABLE log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    operacao TEXT NOT NULL,
    natureza TEXT NOT NULL,
    id_autor INTEGER,
    tipo_entidade TEXT,
    id_entidade INTEGER,
    acao TEXT NOT NULL,
    descricao TEXT
);