from datetime import timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from core.services.status_engine import LensStatus, build_dashboard_payload


class LocalControle:
    def __init__(self, **values):
        self.paciente_contatado = values.get("paciente_contatado", False)
        self.dt_contato = values.get("dt_contato")
        self.usuario_contato = values.get("usuario_contato", "")
        self.retirada_paciente = values.get("retirada_paciente", False)
        self.dt_retirada = values.get("dt_retirada")
        self.usuario_retirada = values.get("usuario_retirada", "")


class StatusEngineTests(SimpleTestCase):
    def build_item(self, local_record=None, **overrides):
        now = timezone.now()
        record = {
            "nr_requisicao": "123",
            "paciente": "Paciente Teste",
            "requisitante": "Setor de Lentes",
            "dt_solicitacao": now - timedelta(days=2),
            "historicos": [],
        }
        record.update(overrides)
        local_records = {"123": local_record} if local_record else {}
        return build_dashboard_payload([record], local_records)["items"][0]

    def test_requisitada_when_only_request_exists(self):
        item = self.build_item()

        self.assertEqual(item["status"], LensStatus.REQUISITADA)

    def test_em_compra_when_purchase_item_exists_without_baixa(self):
        item = self.build_item(has_solic_compra_item=1)

        self.assertEqual(item["status"], LensStatus.EM_COMPRA)

    def test_comprada_when_dt_baixa_exists(self):
        item = self.build_item(has_solic_compra_item=1, dt_baixa=timezone.now())

        self.assertEqual(item["status"], LensStatus.COMPRADA)

    def test_lente_chegou_when_history_has_cheg_lc(self):
        item = self.build_item(
            has_solic_compra_item=1,
            dt_baixa=timezone.now() - timedelta(days=1),
            historicos=[{"ds_historico": "CHEG LC", "dt_historico": timezone.now()}],
        )

        self.assertEqual(item["status"], LensStatus.LENTE_CHEGOU)

    def test_old_cheg_lc_before_request_does_not_mark_lens_as_arrived(self):
        now = timezone.now()
        item = self.build_item(
            dt_solicitacao=now,
            has_solic_compra_item=1,
            dt_baixa=now - timedelta(days=1),
            historicos=[{"ds_historico": "CHEG LC", "dt_historico": now - timedelta(days=900)}],
        )

        self.assertEqual(item["status"], LensStatus.COMPRADA)
        self.assertIsNone(item["dt_chegada_lente"])

    def test_old_dt_chegada_from_query_is_ignored_when_before_request(self):
        now = timezone.now()
        item = self.build_item(
            dt_solicitacao=now,
            has_solic_compra_item=1,
            dt_baixa=now - timedelta(days=1),
            dt_chegada_lente=now - timedelta(days=900),
        )

        self.assertEqual(item["status"], LensStatus.COMPRADA)
        self.assertIsNone(item["dt_chegada_lente"])

    def test_paciente_levou_no_oracle_does_not_close_operational_flow(self):
        item = self.build_item(
            historicos=[
                {"ds_historico": "CHEG LC", "dt_historico": timezone.now() - timedelta(days=2)},
                {"ds_historico": "PACIENTE LEVOU", "dt_historico": timezone.now()},
            ],
        )

        self.assertEqual(item["status"], LensStatus.LENTE_CHEGOU)

    def test_oracle_flag_paciente_levou_does_not_close_operational_flow(self):
        item = self.build_item(has_paciente_levou=1)

        self.assertEqual(item["status"], LensStatus.REQUISITADA)

    def test_paciente_contatado_comes_from_local_control(self):
        item = self.build_item(
            local_record=LocalControle(paciente_contatado=True, dt_contato=timezone.now()),
            historicos=[{"ds_historico": "CHEG LC", "dt_historico": timezone.now()}],
        )

        self.assertEqual(item["status"], LensStatus.PACIENTE_CONTATADO)

    def test_retirada_pelo_paciente_comes_from_local_control(self):
        item = self.build_item(
            local_record=LocalControle(
                paciente_contatado=True,
                dt_contato=timezone.now() - timedelta(days=1),
                retirada_paciente=True,
                dt_retirada=timezone.now(),
            ),
            historicos=[{"ds_historico": "CHEG LC", "dt_historico": timezone.now() - timedelta(days=2)}],
        )

        self.assertEqual(item["status"], LensStatus.RETIRADA_PELO_PACIENTE)
