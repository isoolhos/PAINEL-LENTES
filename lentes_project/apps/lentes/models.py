from django.conf import settings
from django.db import models


class RequisicaoLente(models.Model):
    nr_requisicao = models.CharField("numero da requisicao", max_length=50, unique=True)
    status_atual = models.CharField("status calculado em cache", max_length=30, blank=True)
    dt_contatado = models.DateTimeField("paciente contatado em", null=True, blank=True)
    usuario_contatou = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="usuario que contatou",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="requisicoes_lente_contatadas",
    )
    dt_ultima_atualizacao = models.DateTimeField("ultima atualizacao calculada", null=True, blank=True)
    cache_paciente = models.CharField("paciente", max_length=255, blank=True)
    cache_telefone = models.CharField("telefone", max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-dt_ultima_atualizacao", "cache_paciente"]
        verbose_name = "requisicao de lente"
        verbose_name_plural = "requisicoes de lentes"

    def __str__(self) -> str:
        return f"{self.nr_requisicao} - {self.cache_paciente}".strip(" -")


class ControleLente(models.Model):
    nr_requisicao = models.CharField("numero da requisicao", max_length=50, unique=True)

    paciente_contatado = models.BooleanField(default=False)
    dt_contato = models.DateTimeField(null=True, blank=True)
    usuario_contato = models.CharField(max_length=100, blank=True)

    retirada_paciente = models.BooleanField(default=False)
    dt_retirada = models.DateTimeField(null=True, blank=True)
    usuario_retirada = models.CharField(max_length=100, blank=True)

    observacao = models.TextField(blank=True)

    cache_paciente = models.CharField(max_length=255, blank=True)
    cache_telefone = models.CharField(max_length=50, blank=True)
    cache_dt_solicitacao = models.DateTimeField(null=True, blank=True)
    cache_dt_chegada_lente = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-dt_retirada", "-dt_contato", "cache_paciente"]
        verbose_name = "controle operacional de lente"
        verbose_name_plural = "controles operacionais de lentes"

    def __str__(self) -> str:
        return f"{self.nr_requisicao} - {self.cache_paciente}".strip(" -")


class MovimentoRequisicaoLente(models.Model):
    TIPO_CONTATO_PACIENTE = "CONTATO_PACIENTE"
    TIPO_RETIRADA_PACIENTE = "RETIRADA_PACIENTE"

    TIPO_CHOICES = [
        (TIPO_CONTATO_PACIENTE, "Paciente contatado"),
        (TIPO_RETIRADA_PACIENTE, "Retirada pelo paciente"),
    ]

    requisicao = models.ForeignKey(
        RequisicaoLente,
        on_delete=models.CASCADE,
        related_name="movimentos",
    )
    tipo = models.CharField(max_length=40, choices=TIPO_CHOICES)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="movimentos_lentes",
    )
    status_calculado = models.CharField(max_length=30, blank=True)
    observacao = models.TextField(blank=True)
    dt_movimento = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-dt_movimento"]
        verbose_name = "movimento de requisicao de lente"
        verbose_name_plural = "movimentos de requisicoes de lentes"

    def __str__(self) -> str:
        return f"{self.requisicao.nr_requisicao} - {self.get_tipo_display()}"
