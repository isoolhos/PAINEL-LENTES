from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from core.services.status_engine import calculate_kpis

from .services import (
    confirm_patient_withdrawal,
    filter_items,
    get_dashboard_payload,
    list_completed_withdrawals,
    mark_patient_contact,
)


@login_required
def dashboard(request: HttpRequest):
    date_filters = {
        "dt_solicitacao_inicio": request.GET.get("dt_solicitacao_inicio", ""),
        "dt_solicitacao_fim": request.GET.get("dt_solicitacao_fim", ""),
        "dt_chegada_inicio": request.GET.get("dt_chegada_inicio", ""),
        "dt_chegada_fim": request.GET.get("dt_chegada_fim", ""),
    }
    payload = get_dashboard_payload(
        force_refresh=request.GET.get("refresh") == "1",
        date_filters=date_filters,
    )
    status_filter = request.GET.get("status", "")
    search = request.GET.get("q", "")
    include_retiradas = request.GET.get("include_retiradas") == "1"
    items = filter_items(
        payload["items"],
        status=status_filter,
        search=search,
        include_retiradas=include_retiradas,
        **date_filters,
    )

    return render(
        request,
        "lentes/dashboard.html",
        {
            **payload,
            "items": items,
            "kpis": calculate_kpis(items),
            "filtered_count": len(items),
            "total_items": len(payload["items"]),
            "status_filter": status_filter,
            "search": search,
            "include_retiradas": include_retiradas,
            **date_filters,
        },
    )


@login_required
def kanban(request: HttpRequest):
    payload = get_dashboard_payload(force_refresh=request.GET.get("refresh") == "1")
    return render(request, "lentes/kanban.html", payload)


@login_required
def retiradas(request: HttpRequest):
    rows = list_completed_withdrawals()
    return render(
        request,
        "lentes/retiradas.html",
        {
            "rows": rows,
            "total_retiradas": len(rows),
        },
    )


@login_required
@require_POST
def marcar_paciente_contatado(request: HttpRequest):
    nr_requisicao = request.POST.get("nr_requisicao", "").strip()
    if not nr_requisicao:
        return HttpResponseBadRequest("Numero da requisicao nao informado.")

    controle = mark_patient_contact(nr_requisicao, request.user)
    messages.success(
        request,
        f"Contato registrado para requisicao {controle.nr_requisicao}.",
    )
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("lentes:dashboard")


@login_required
@require_POST
def confirmar_retirada_paciente(request: HttpRequest):
    nr_requisicao = request.POST.get("nr_requisicao", "").strip()
    if not nr_requisicao:
        return HttpResponseBadRequest("Numero da requisicao nao informado.")

    controle = confirm_patient_withdrawal(nr_requisicao, request.user)
    messages.success(
        request,
        f"Retirada registrada para requisicao {controle.nr_requisicao}.",
    )
    next_url = request.POST.get("next", "")
    if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return redirect(next_url)
    return redirect("lentes:dashboard")
