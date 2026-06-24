from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RequisicaoLente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("nr_requisicao", models.CharField(max_length=50, unique=True, verbose_name="numero da requisicao")),
                ("status_atual", models.CharField(blank=True, max_length=30, verbose_name="status calculado em cache")),
                ("dt_contatado", models.DateTimeField(blank=True, null=True, verbose_name="paciente contatado em")),
                (
                    "dt_ultima_atualizacao",
                    models.DateTimeField(blank=True, null=True, verbose_name="ultima atualizacao calculada"),
                ),
                ("cache_paciente", models.CharField(blank=True, max_length=255, verbose_name="paciente")),
                ("cache_telefone", models.CharField(blank=True, max_length=50, verbose_name="telefone")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "usuario_contatou",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="requisicoes_lente_contatadas",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="usuario que contatou",
                    ),
                ),
            ],
            options={
                "verbose_name": "requisicao de lente",
                "verbose_name_plural": "requisicoes de lentes",
                "ordering": ["-dt_ultima_atualizacao", "cache_paciente"],
            },
        ),
        migrations.CreateModel(
            name="MovimentoRequisicaoLente",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "tipo",
                    models.CharField(choices=[("CONTATO_PACIENTE", "Paciente contatado")], max_length=40),
                ),
                ("status_calculado", models.CharField(blank=True, max_length=30)),
                ("observacao", models.TextField(blank=True)),
                ("dt_movimento", models.DateTimeField(auto_now_add=True)),
                (
                    "requisicao",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="movimentos",
                        to="lentes.requisicaolente",
                    ),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="movimentos_lentes",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "movimento de requisicao de lente",
                "verbose_name_plural": "movimentos de requisicoes de lentes",
                "ordering": ["-dt_movimento"],
            },
        ),
    ]
