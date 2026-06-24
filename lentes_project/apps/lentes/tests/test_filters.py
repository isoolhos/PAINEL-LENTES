from datetime import datetime

from django.test import SimpleTestCase
from django.utils import timezone

from apps.lentes.services import filter_items
from core.services.status_engine import LensStatus


class DashboardFilterTests(SimpleTestCase):
    def build_item(self, nr_requisicao, dt_solicitacao, dt_chegada_lente=None):
        return {
            "nr_requisicao": nr_requisicao,
            "paciente": f"Paciente {nr_requisicao}",
            "telefone": "",
            "status": LensStatus.REQUISITADA,
            "dt_solicitacao": timezone.make_aware(dt_solicitacao),
            "dt_chegada_lente": timezone.make_aware(dt_chegada_lente) if dt_chegada_lente else None,
        }

    def test_filters_by_solicitation_date_range(self):
        items = [
            self.build_item("1", datetime(2026, 6, 1, 9, 0)),
            self.build_item("2", datetime(2026, 6, 10, 9, 0)),
            self.build_item("3", datetime(2026, 6, 20, 9, 0)),
        ]

        filtered = filter_items(
            items,
            dt_solicitacao_inicio="2026-06-05",
            dt_solicitacao_fim="2026-06-15",
        )

        self.assertEqual([item["nr_requisicao"] for item in filtered], ["2"])

    def test_filters_by_arrival_date_range(self):
        items = [
            self.build_item("1", datetime(2026, 6, 1, 9, 0), datetime(2026, 6, 5, 10, 0)),
            self.build_item("2", datetime(2026, 6, 1, 9, 0), datetime(2026, 6, 12, 10, 0)),
            self.build_item("3", datetime(2026, 6, 1, 9, 0), None),
        ]

        filtered = filter_items(
            items,
            dt_chegada_inicio="2026-06-10",
            dt_chegada_fim="2026-06-15",
        )

        self.assertEqual([item["nr_requisicao"] for item in filtered], ["2"])
