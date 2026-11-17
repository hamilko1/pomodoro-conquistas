-- =====================================================================
-- Pomodoro com Conquistas - Projeto físico do banco de dados
-- SGBD: PostgreSQL 14+
-- =====================================================================

DROP TABLE IF EXISTS usuarios_conquistas;
DROP TABLE IF EXISTS conquistas;
DROP TABLE IF EXISTS metas;
DROP TABLE IF EXISTS sessoes_pomodoro;
DROP TABLE IF EXISTS materias;
DROP TABLE IF EXISTS usuarios;

-- ---------------------------------------------------------------------
-- USUARIOS
-- ---------------------------------------------------------------------
CREATE TABLE usuarios (
    id             SERIAL       PRIMARY KEY,
    nome           VARCHAR(100) NOT NULL,
    email          VARCHAR(150) NOT NULL UNIQUE,
    senha_hash     VARCHAR(255) NOT NULL,
    data_cadastro  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ---------------------------------------------------------------------
-- MATERIAS (assunto/objetivo de estudo de cada usuário)
-- ---------------------------------------------------------------------
CREATE TABLE materias (
    id          SERIAL       PRIMARY KEY,
    usuario_id  INTEGER      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    nome        VARCHAR(80)  NOT NULL,
    CONSTRAINT uq_materia_usuario UNIQUE (usuario_id, nome)
);

-- ---------------------------------------------------------------------
-- SESSOES_POMODORO (cada ciclo de foco ou pausa)
-- ---------------------------------------------------------------------
CREATE TABLE sessoes_pomodoro (
    id           SERIAL      PRIMARY KEY,
    usuario_id   INTEGER     NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    materia_id   INTEGER     REFERENCES materias(id) ON DELETE SET NULL,
    inicio       TIMESTAMP   NOT NULL,
    duracao_min  SMALLINT    NOT NULL CHECK (duracao_min > 0),
    tipo         VARCHAR(12) NOT NULL DEFAULT 'foco'
                 CHECK (tipo IN ('foco', 'pausa_curta', 'pausa_longa')),
    concluida    BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_sessoes_usuario_inicio ON sessoes_pomodoro (usuario_id, inicio);

-- ---------------------------------------------------------------------
-- METAS (ex.: "10 pomodoros de Cálculo até sexta")
-- ---------------------------------------------------------------------
CREATE TABLE metas (
    id               SERIAL       PRIMARY KEY,
    usuario_id       INTEGER      NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    materia_id       INTEGER      REFERENCES materias(id) ON DELETE SET NULL,
    descricao        VARCHAR(150) NOT NULL,
    quantidade_alvo  SMALLINT     NOT NULL CHECK (quantidade_alvo > 0),
    prazo            DATE,
    concluida        BOOLEAN      NOT NULL DEFAULT FALSE,
    data_conclusao   TIMESTAMP
);

CREATE INDEX idx_metas_usuario ON metas (usuario_id);

-- ---------------------------------------------------------------------
-- CONQUISTAS (catálogo de medalhas)
-- criterio_tipo + criterio_valor permitem avaliar a regra automaticamente
-- ---------------------------------------------------------------------
CREATE TABLE conquistas (
    id              SERIAL       PRIMARY KEY,
    codigo          VARCHAR(40)  NOT NULL UNIQUE,
    nome            VARCHAR(60)  NOT NULL,
    descricao       VARCHAR(200) NOT NULL,
    icone           VARCHAR(10)  NOT NULL,
    criterio_tipo   VARCHAR(20)  NOT NULL
                    CHECK (criterio_tipo IN (
                        'total_sessoes',    -- total de pomodoros de foco concluídos
                        'sequencia_dias',   -- dias seguidos com ao menos 1 pomodoro
                        'sessoes_no_dia',   -- pomodoros concluídos no mesmo dia
                        'metas_concluidas', -- total de metas cumpridas
                        'hora_apos',        -- sessão concluída a partir de X horas
                        'hora_antes'        -- sessão concluída antes de X horas
                    )),
    criterio_valor  SMALLINT     NOT NULL CHECK (criterio_valor > 0)
);

-- ---------------------------------------------------------------------
-- USUARIOS_CONQUISTAS (N:N - quais medalhas cada usuário já ganhou)
-- ---------------------------------------------------------------------
CREATE TABLE usuarios_conquistas (
    usuario_id     INTEGER   NOT NULL REFERENCES usuarios(id)   ON DELETE CASCADE,
    conquista_id   INTEGER   NOT NULL REFERENCES conquistas(id) ON DELETE CASCADE,
    data_obtencao  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (usuario_id, conquista_id)
);

-- ---------------------------------------------------------------------
-- DADOS INICIAIS: catálogo de conquistas
-- ---------------------------------------------------------------------
INSERT INTO conquistas (codigo, nome, descricao, icone, criterio_tipo, criterio_valor) VALUES
('primeiro_foco',  'Primeiro Foco',   'Conclua seu primeiro pomodoro.',               '🥉', 'total_sessoes',    1),
('dez_focos',      'Pegando Ritmo',   'Conclua 10 pomodoros.',                        '🥈', 'total_sessoes',    10),
('cem_focos',      'Mestre do Foco',  'Conclua 100 pomodoros.',                       '🥇', 'total_sessoes',    100),
('sequencia_3',    'Aquecendo',       'Estude 3 dias seguidos.',                      '🔥', 'sequencia_dias',   3),
('sequencia_7',    'Semana Perfeita', 'Estude 7 dias seguidos.',                      '🔥', 'sequencia_dias',   7),
('sequencia_30',   'Hábito Formado',  'Estude 30 dias seguidos.',                     '🏆', 'sequencia_dias',   30),
('maratonista',    'Maratonista',     'Conclua 4 pomodoros no mesmo dia.',            '📚', 'sessoes_no_dia',   4),
('meta_cumprida',  'Meta Cumprida',   'Cumpra sua primeira meta.',                    '🎯', 'metas_concluidas', 1),
('coruja',         'Coruja',          'Conclua um pomodoro depois das 22h.',          '🦉', 'hora_apos',        22),
('madrugador',     'Madrugador',      'Conclua um pomodoro antes das 7h.',            '🌅', 'hora_antes',       7);
