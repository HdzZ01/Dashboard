-- Schema da v2 — Painel de Inteligência Hospitalar
-- Executado pelo ETL a cada carga (idempotente).
-- Referência: .context/plan/data/data_model.md (seção 4)

-- ------------------------------------------------------------------ limpeza
DROP TABLE IF EXISTS atendimento  CASCADE;
DROP TABLE IF EXISTS paciente     CASCADE;
DROP TABLE IF EXISTS bairro       CASCADE;
DROP TABLE IF EXISTS municipio    CASCADE;
DROP TABLE IF EXISTS servico      CASCADE;
DROP TABLE IF EXISTS medicamento  CASCADE;
DROP TYPE  IF EXISTS tipo_atendimento;

-- -------------------------------------------------------------------- tipos
CREATE TYPE tipo_atendimento AS ENUM
    ('ATENDIMENTO', 'CIRURGIA', 'MEDICAMENTO', 'TRIAGEM');

-- --------------------------------------------------------------- dimensões
CREATE TABLE municipio (
    id         SERIAL PRIMARY KEY,
    nome       TEXT    NOT NULL UNIQUE,
    uf         CHAR(2) NOT NULL DEFAULT 'SP',
    latitude   NUMERIC(9, 6),
    longitude  NUMERIC(9, 6)
);

CREATE TABLE bairro (
    id            SERIAL PRIMARY KEY,
    nome          TEXT    NOT NULL,
    municipio_id  INTEGER NOT NULL REFERENCES municipio (id),
    UNIQUE (nome, municipio_id)
);

CREATE TABLE servico (
    id    SERIAL PRIMARY KEY,
    nome  TEXT NOT NULL UNIQUE
);

CREATE TABLE medicamento (
    id         SERIAL PRIMARY KEY,
    descricao  TEXT NOT NULL UNIQUE
);

-- ---------------------------------------------------------------- paciente
CREATE TABLE paciente (
    id               TEXT PRIMARY KEY,               -- _id da fonte
    sexo             CHAR(1) NOT NULL CHECK (sexo IN ('F', 'M', 'I')),
    data_nascimento  DATE    NOT NULL,
    bairro_id        INTEGER REFERENCES bairro (id)  -- nulo quando sem bairro
);

-- -------------------------------------------------------------- fato
CREATE TABLE atendimento (
    id              BIGSERIAL PRIMARY KEY,
    paciente_id     TEXT             NOT NULL REFERENCES paciente (id),
    tipo            tipo_atendimento NOT NULL,
    servico_id      INTEGER REFERENCES servico (id),
    data_entrada    TIMESTAMP,
    data_saida      TIMESTAMP,
    queixa          TEXT,
    diagnostico     TEXT,
    procedimento    TEXT,
    medicamento_id  INTEGER REFERENCES medicamento (id),
    carregado_em    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- --------------------------------------------------------------- índices
CREATE INDEX ix_bairro_municipio   ON bairro      (municipio_id);
CREATE INDEX ix_paciente_bairro    ON paciente    (bairro_id);
CREATE INDEX ix_atend_paciente     ON atendimento (paciente_id);
CREATE INDEX ix_atend_servico      ON atendimento (servico_id);
CREATE INDEX ix_atend_medicamento  ON atendimento (medicamento_id);
CREATE INDEX ix_atend_tipo         ON atendimento (tipo);
CREATE INDEX ix_atend_data_entrada ON atendimento (data_entrada);
