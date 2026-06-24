from django.core.management.base import BaseCommand

from apps.lentes.services import get_dashboard_payload


class Command(BaseCommand):
    help = "Atualiza o cache de requisicoes de lentes consultando o Oracle/Tasy."

    def handle(self, *args, **options):
        payload = get_dashboard_payload(force_refresh=True)
        self.stdout.write(
            self.style.SUCCESS(
                f"Cache atualizado: {len(payload['items'])} requisicoes, "
                f"{payload['kpis']['total_em_aberto']} em aberto."
            )
        )
