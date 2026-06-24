from datetime import timedelta

from django.utils import timezone


def get_sample_lens_records() -> list[dict]:
    now = timezone.now()
    return [
        {
            "nr_requisicao": "100245",
            "cd_pessoa_fisica": "501",
            "paciente": "Maria Oliveira",
            "nr_telefone_celular": "(11) 99999-0101",
            "requisitante": "Setor de Lentes",
            "dt_solicitacao": now - timedelta(days=2),
            "has_solic_compra_item": 0,
            "historicos": [],
        },
        {
            "nr_requisicao": "100246",
            "cd_pessoa_fisica": "502",
            "paciente": "Joao Santos",
            "nr_telefone_celular": "(11) 98888-0202",
            "requisitante": "Setor de Lentes",
            "dt_solicitacao": now - timedelta(days=5),
            "dt_solic_compra": now - timedelta(days=4),
            "has_solic_compra_item": 1,
            "historicos": [],
        },
        {
            "nr_requisicao": "100247",
            "cd_pessoa_fisica": "503",
            "paciente": "Ana Costa",
            "nr_telefone_celular": "(11) 97777-0303",
            "requisitante": "Setor de Lentes",
            "dt_solicitacao": now - timedelta(days=9),
            "dt_solic_compra": now - timedelta(days=8),
            "dt_baixa": now - timedelta(days=2),
            "has_solic_compra_item": 1,
            "historicos": [],
        },
        {
            "nr_requisicao": "100248",
            "cd_pessoa_fisica": "504",
            "paciente": "Carlos Pereira",
            "nr_telefone_celular": "(11) 96666-0404",
            "requisitante": "Setor de Lentes",
            "dt_solicitacao": now - timedelta(days=12),
            "dt_solic_compra": now - timedelta(days=11),
            "dt_baixa": now - timedelta(days=7),
            "has_solic_compra_item": 1,
            "historicos": [
                {"dt_historico": now, "ds_historico": "CHEG LC - lente recebida na farmacia"},
            ],
        },
        {
            "nr_requisicao": "100249",
            "cd_pessoa_fisica": "505",
            "paciente": "Beatriz Lima",
            "nr_telefone_celular": "(11) 95555-0505",
            "requisitante": "Setor de Lentes",
            "dt_solicitacao": now - timedelta(days=18),
            "dt_solic_compra": now - timedelta(days=17),
            "dt_baixa": now - timedelta(days=13),
            "has_solic_compra_item": 1,
            "historicos": [
                {"dt_historico": now - timedelta(days=4), "ds_historico": "CHEG LC"},
                {"dt_historico": now - timedelta(days=1), "ds_historico": "PACIENTE LEVOU"},
            ],
        },
    ]
