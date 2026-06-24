REQUISICOES_LENTES_SQL = """
SELECT
    r.nr_requisicao,

    r.cd_pessoa_solicitante,
    r.cd_pessoa_solicitante                  AS cd_pessoa_fisica,
    obter_nome_pf(r.cd_pessoa_solicitante)   AS paciente,
    pf.nr_telefone_celular,

    r.cd_pessoa_requisitante,
    obter_nome_pf(r.cd_pessoa_requisitante)  AS requisitante,

    r.dt_solicitacao_requisicao              AS dt_solicitacao,
    r.dt_solicitacao_requisicao,
    r.dt_liberacao,
    r.dt_aprovacao,
    r.dt_baixa,

    r.nm_usuario_aprov,
    r.nm_usuario_lib,

    hc.dt_inicial                            AS dt_chegada_lente,
    hc.nm_usuario_nrec                       AS usuario_chegada,
    hc.ds_historico                          AS historico_chegada,

    CASE
        WHEN EXISTS (
            SELECT 1
            FROM pessoa_fisica_historico h
            WHERE h.cd_pessoa_fisica = r.cd_pessoa_solicitante
              AND UPPER(h.ds_historico) LIKE '%PACIENTE LEVOU%'
        )
        THEN 1
        ELSE 0
    END                                      AS has_paciente_levou,

    CASE
        WHEN EXISTS (
            SELECT 1
            FROM solic_compra_item sci
            WHERE sci.nr_requisicao = r.nr_requisicao
        )
        THEN 1
        ELSE 0
    END                                      AS has_solic_compra_item

FROM requisicao_material r

LEFT JOIN pessoa_fisica pf
       ON pf.cd_pessoa_fisica = r.cd_pessoa_solicitante

LEFT JOIN pessoa_fisica_historico hc
       ON hc.cd_pessoa_fisica = r.cd_pessoa_solicitante
      AND hc.dt_inicial = (
            SELECT MAX(h2.dt_inicial)
            FROM pessoa_fisica_historico h2
            WHERE h2.cd_pessoa_fisica = r.cd_pessoa_solicitante
              AND UPPER(h2.ds_historico) LIKE '%CHEG LC%'
              AND h2.dt_inicial >= r.dt_solicitacao_requisicao
       )

WHERE r.cd_local_estoque = 22
  AND r.cd_pessoa_requisitante IN (47,120,15226)
  AND (
        r.dt_solicitacao_requisicao >= SYSDATE - :days_back
        OR hc.dt_inicial >= SYSDATE - :days_back
      )

ORDER BY
    CASE
        WHEN hc.cd_pessoa_fisica IS NOT NULL THEN 1
        ELSE 2
    END,
    r.dt_solicitacao_requisicao DESC
"""


HISTORICO_PACIENTE_SQL = """
SELECT
    h.cd_pessoa_fisica  AS cd_pessoa_fisica,
    h.dt_inicial        AS dt_historico,
    h.nm_usuario_nrec   AS nm_usuario_nrec,
    h.ds_historico      AS ds_historico
FROM pessoa_fisica_historico h
WHERE h.cd_pessoa_fisica IN ({binds})
  AND h.dt_inicial >= SYSDATE - :days_back
  AND (
        UPPER(h.ds_historico) LIKE '%CHEG LC%'
        OR UPPER(h.ds_historico) LIKE '%PACIENTE LEVOU%'
      )
ORDER BY h.dt_inicial DESC
"""
