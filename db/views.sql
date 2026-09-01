-- Views consumidas pelo dashboard (v2).
-- O painel lê estas views — nunca monta SQL de coluna crua.
-- Referência: .context/plan/data/data_model.md (seção 5)

DROP VIEW IF EXISTS vw_demanda_municipio;
DROP VIEW IF EXISTS vw_volume_mensal;
DROP VIEW IF EXISTS vw_atendimento;

-- Linha analítica completa, já com derivados (idade, ano/mês).
CREATE VIEW vw_atendimento AS
SELECT
    a.id,
    a.tipo,
    s.nome                                        AS servico,
    a.data_entrada,
    date_trunc('month', a.data_entrada)::date     AS ano_mes,
    a.data_saida,
    a.queixa,
    a.diagnostico,
    a.procedimento,
    m.descricao                                   AS medicamento,
    p.id                                          AS paciente_id,
    p.sexo,
    p.data_nascimento,
    EXTRACT(YEAR FROM age(
        COALESCE(a.data_entrada, CURRENT_DATE), p.data_nascimento
    ))::int                                       AS idade,
    b.nome                                        AS bairro,
    mu.nome                                       AS municipio,
    mu.latitude,
    mu.longitude
FROM atendimento a
JOIN      paciente    p  ON p.id = a.paciente_id
LEFT JOIN bairro      b  ON b.id = p.bairro_id
LEFT JOIN municipio   mu ON mu.id = b.municipio_id
LEFT JOIN servico     s  ON s.id = a.servico_id
LEFT JOIN medicamento m  ON m.id = a.medicamento_id;

-- Volume mensal de atendimentos.
CREATE VIEW vw_volume_mensal AS
SELECT
    date_trunc('month', data_entrada)::date AS ano_mes,
    count(*)                                AS atendimentos
FROM atendimento
WHERE data_entrada IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- Demanda agregada por município (para o mapa).
CREATE VIEW vw_demanda_municipio AS
SELECT
    mu.nome       AS municipio,
    mu.latitude,
    mu.longitude,
    count(*)      AS atendimentos
FROM atendimento a
JOIN paciente  p  ON p.id = a.paciente_id
JOIN bairro    b  ON b.id = p.bairro_id
JOIN municipio mu ON mu.id = b.municipio_id
GROUP BY 1, 2, 3
ORDER BY atendimentos DESC;
