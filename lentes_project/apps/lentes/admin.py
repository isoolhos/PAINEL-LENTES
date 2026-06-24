from django.contrib import admin

from .models import ControleLente, MovimentoRequisicaoLente, RequisicaoLente


@admin.register(RequisicaoLente)
class RequisicaoLenteAdmin(admin.ModelAdmin):
    list_display = (
        "nr_requisicao",
        "status_atual",
        "cache_paciente",
        "cache_telefone",
        "dt_contatado",
        "usuario_contatou",
        "dt_ultima_atualizacao",
    )
    search_fields = ("nr_requisicao", "cache_paciente", "cache_telefone")
    list_filter = ("status_atual", "dt_contatado")
    readonly_fields = ("created_at", "updated_at")


@admin.register(MovimentoRequisicaoLente)
class MovimentoRequisicaoLenteAdmin(admin.ModelAdmin):
    list_display = ("requisicao", "tipo", "usuario", "status_calculado", "dt_movimento")
    search_fields = ("requisicao__nr_requisicao", "requisicao__cache_paciente")
    list_filter = ("tipo", "status_calculado", "dt_movimento")


@admin.register(ControleLente)
class ControleLenteAdmin(admin.ModelAdmin):
    list_display = (
        "nr_requisicao",
        "cache_paciente",
        "cache_telefone",
        "paciente_contatado",
        "dt_contato",
        "usuario_contato",
        "retirada_paciente",
        "dt_retirada",
        "usuario_retirada",
    )
    search_fields = ("nr_requisicao", "cache_paciente", "cache_telefone")
    list_filter = ("paciente_contatado", "retirada_paciente", "dt_contato", "dt_retirada")
    readonly_fields = ("created_at", "updated_at")
