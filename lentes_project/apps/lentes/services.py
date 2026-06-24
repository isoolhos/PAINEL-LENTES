from __future__ import annotations

from datetime import date, datetime
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from core.services.status_engine import (
    LensStatus,
    STATUS_LABELS,
    STATUS_ORDER,
    build_dashboard_payload,
    days_between,
    days_label,
)
from integrations.oracle.repositories import TasyLentesRepository

from .models import ControleLente, MovimentoRequisicaoLente, RequisicaoLente


ORACLE_CACHE_KEY = "lentes:tasy:requisicoes:v1"


def parse_filter_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def item_local_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        if timezone.is_naive(value):
            value = timezone.make_aware(value, timezone.get_current_timezone())
        return timezone.localtime(value).date()
    if isinstance(value, date):
        return value
    return None


def date_in_range(value: Any, start_value: str = "", end_value: str = "") -> bool:
    start = parse_filter_date(start_value)
    end = parse_filter_date(end_value)
    if not start and not end:
        return True

    value_date = item_local_date(value)
    if value_date is None:
        return False
    if start and value_date < start:
        return False
    if end and value_date > end:
        return False
    return True


def resolve_query_days_back(date_filters: dict[str, str] | None = None) -> int:
    date_filters = date_filters or {}
    selected_dates = [
        parsed
        for parsed in (parse_filter_date(value) for value in date_filters.values())
        if parsed is not None
    ]
    if not selected_dates:
        return settings.ORACLE_QUERY_DAYS_BACK

    oldest_selected_date = min(selected_dates)
    days_back = max((timezone.localdate() - oldest_selected_date).days + 2, 1)
    return max(settings.ORACLE_QUERY_DAYS_BACK, days_back)


def get_oracle_records(force_refresh: bool = False, days_back: int | None = None) -> list[dict[str, Any]]:
    days_back = days_back or settings.ORACLE_QUERY_DAYS_BACK
    cache_key = f"{ORACLE_CACHE_KEY}:days:{days_back}"

    if force_refresh:
        cache.delete(cache_key)

    records = cache.get(cache_key)
    if records is not None:
        return records

    records = TasyLentesRepository().list_requisicoes_lentes(days_back=days_back)
    cache.set(cache_key, records, settings.ORACLE_CACHE_TTL_SECONDS)
    return records


def get_dashboard_payload(
    force_refresh: bool = False,
    date_filters: dict[str, str] | None = None,
) -> dict[str, Any]:
    days_back = resolve_query_days_back(date_filters)
    records = get_oracle_records(force_refresh=force_refresh, days_back=days_back)
    requisition_numbers = [str(record.get("nr_requisicao") or "").strip() for record in records]
    local_records = {
        row.nr_requisicao: row
        for row in ControleLente.objects.filter(nr_requisicao__in=requisition_numbers)
    }

    payload = build_dashboard_payload(records, local_records)
    sync_local_cache(payload["items"])
    payload["kanban_columns"] = build_kanban_columns(payload)
    payload["status_choices"] = [(status, STATUS_LABELS[status]) for status in STATUS_ORDER]
    payload["oracle_enabled"] = settings.ORACLE_ENABLED
    payload["using_sample_data"] = settings.LENTES_USE_SAMPLE_DATA and not settings.ORACLE_ENABLED
    payload["query_days_back"] = days_back
    return payload


def sync_local_cache(items: list[dict[str, Any]]) -> None:
    if not items:
        return

    now = timezone.now()
    requisition_numbers = [item["nr_requisicao"] for item in items]
    existing = RequisicaoLente.objects.in_bulk(requisition_numbers, field_name="nr_requisicao")
    existing_controls = ControleLente.objects.in_bulk(requisition_numbers, field_name="nr_requisicao")
    to_create: list[RequisicaoLente] = []
    to_update: list[RequisicaoLente] = []
    controls_to_update: list[ControleLente] = []

    for item in items:
        nr_requisicao = item["nr_requisicao"]
        values = {
            "status_atual": item["status"],
            "dt_ultima_atualizacao": item["dt_ultima_atualizacao"],
            "cache_paciente": item["paciente"],
            "cache_telefone": item["telefone"],
        }
        local = existing.get(nr_requisicao)
        if local is None:
            to_create.append(RequisicaoLente(nr_requisicao=nr_requisicao, **values))
        else:
            changed = False
            for field, value in values.items():
                if getattr(local, field) != value:
                    setattr(local, field, value)
                    changed = True
            if changed:
                local.updated_at = now
                to_update.append(local)

        control = existing_controls.get(nr_requisicao)
        if control:
            control_changed = False
            control_values = {
                "cache_paciente": item["paciente"],
                "cache_telefone": item["telefone"],
                "cache_dt_solicitacao": item["dt_solicitacao"],
                "cache_dt_chegada_lente": item["dt_chegada_lente"],
            }
            for field, value in control_values.items():
                if getattr(control, field) != value:
                    setattr(control, field, value)
                    control_changed = True
            if control_changed:
                control.updated_at = now
                controls_to_update.append(control)

    if to_create:
        RequisicaoLente.objects.bulk_create(to_create, ignore_conflicts=True)
    if to_update:
        RequisicaoLente.objects.bulk_update(
            to_update,
            ["status_atual", "dt_ultima_atualizacao", "cache_paciente", "cache_telefone", "updated_at"],
        )
    if controls_to_update:
        ControleLente.objects.bulk_update(
            controls_to_update,
            [
                "cache_paciente",
                "cache_telefone",
                "cache_dt_solicitacao",
                "cache_dt_chegada_lente",
                "updated_at",
            ],
        )


def filter_items(
    items: list[dict[str, Any]],
    status: str = "",
    search: str = "",
    dt_solicitacao_inicio: str = "",
    dt_solicitacao_fim: str = "",
    dt_chegada_inicio: str = "",
    dt_chegada_fim: str = "",
    include_retiradas: bool = False,
) -> list[dict[str, Any]]:
    filtered = items
    if not include_retiradas and status != LensStatus.RETIRADA_PELO_PACIENTE and not search.strip():
        filtered = [item for item in filtered if item["status"] != LensStatus.RETIRADA_PELO_PACIENTE]
    if status:
        filtered = [item for item in filtered if item["status"] == status]
    if search:
        needle = search.strip().lower()
        filtered = [
            item
            for item in filtered
            if needle in item["paciente"].lower()
            or needle in item["nr_requisicao"].lower()
            or needle in item["telefone"].lower()
        ]
    filtered = [
        item
        for item in filtered
        if date_in_range(item["dt_solicitacao"], dt_solicitacao_inicio, dt_solicitacao_fim)
        and date_in_range(item["dt_chegada_lente"], dt_chegada_inicio, dt_chegada_fim)
    ]
    return filtered


def build_kanban_columns(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "status": status,
            "label": STATUS_LABELS[status],
            "items": payload["kanban"].get(status, []),
        }
        for status in STATUS_ORDER
    ]


def username_for_audit(user) -> str:
    if getattr(user, "is_authenticated", False):
        return user.get_username()
    return ""


def requisicao_defaults_from_item(item: dict[str, Any] | None) -> dict[str, Any]:
    if not item:
        return {}
    return {
        "status_atual": item["status"],
        "dt_ultima_atualizacao": item["dt_ultima_atualizacao"],
        "cache_paciente": item["paciente"],
        "cache_telefone": item["telefone"],
    }


def controle_defaults_from_item(item: dict[str, Any] | None) -> dict[str, Any]:
    if not item:
        return {}
    return {
        "cache_paciente": item["paciente"],
        "cache_telefone": item["telefone"],
        "cache_dt_solicitacao": item["dt_solicitacao"],
        "cache_dt_chegada_lente": item["dt_chegada_lente"],
    }


def find_dashboard_item(nr_requisicao: str) -> dict[str, Any] | None:
    payload = get_dashboard_payload(force_refresh=False)
    return next(
        (row for row in payload["items"] if row["nr_requisicao"] == nr_requisicao),
        None,
    )


def get_or_create_requisicao_cache(nr_requisicao: str, item: dict[str, Any] | None) -> RequisicaoLente:
    defaults = requisicao_defaults_from_item(item)
    requisicao, _ = RequisicaoLente.objects.select_for_update().get_or_create(
        nr_requisicao=nr_requisicao,
        defaults=defaults,
    )
    for field, value in defaults.items():
        setattr(requisicao, field, value)
    requisicao.save()
    return requisicao


def get_or_create_controle(nr_requisicao: str, item: dict[str, Any] | None) -> ControleLente:
    defaults = controle_defaults_from_item(item)
    controle, _ = ControleLente.objects.select_for_update().get_or_create(
        nr_requisicao=nr_requisicao,
        defaults=defaults,
    )
    for field, value in defaults.items():
        setattr(controle, field, value)
    controle.save()
    return controle


@transaction.atomic
def mark_patient_contact(nr_requisicao: str, user) -> ControleLente:
    nr_requisicao = str(nr_requisicao or "").strip()
    item = find_dashboard_item(nr_requisicao)
    requisicao = get_or_create_requisicao_cache(nr_requisicao, item)
    controle = get_or_create_controle(nr_requisicao, item)

    now = timezone.now()
    controle.paciente_contatado = True
    controle.dt_contato = now
    controle.usuario_contato = username_for_audit(user)
    controle.save()

    requisicao.dt_contatado = now
    requisicao.usuario_contatou = user if getattr(user, "is_authenticated", False) else None
    requisicao.status_atual = LensStatus.PACIENTE_CONTATADO
    requisicao.save()

    MovimentoRequisicaoLente.objects.create(
        requisicao=requisicao,
        tipo=MovimentoRequisicaoLente.TIPO_CONTATO_PACIENTE,
        usuario=user if getattr(user, "is_authenticated", False) else None,
        status_calculado=LensStatus.PACIENTE_CONTATADO,
        observacao="Contato confirmado no painel operacional.",
    )
    return controle


@transaction.atomic
def confirm_patient_withdrawal(nr_requisicao: str, user) -> ControleLente:
    nr_requisicao = str(nr_requisicao or "").strip()
    item = find_dashboard_item(nr_requisicao)
    requisicao = get_or_create_requisicao_cache(nr_requisicao, item)
    controle = get_or_create_controle(nr_requisicao, item)

    if not controle.paciente_contatado:
        controle.paciente_contatado = True
        controle.dt_contato = timezone.now()
        controle.usuario_contato = username_for_audit(user)

    controle.retirada_paciente = True
    controle.dt_retirada = timezone.now()
    controle.usuario_retirada = username_for_audit(user)
    controle.save()

    requisicao.status_atual = LensStatus.RETIRADA_PELO_PACIENTE
    requisicao.dt_ultima_atualizacao = controle.dt_retirada
    requisicao.save()

    MovimentoRequisicaoLente.objects.create(
        requisicao=requisicao,
        tipo=MovimentoRequisicaoLente.TIPO_RETIRADA_PACIENTE,
        usuario=user if getattr(user, "is_authenticated", False) else None,
        status_calculado=LensStatus.RETIRADA_PELO_PACIENTE,
        observacao="Retirada pelo paciente confirmada no painel operacional.",
    )
    return controle


def list_completed_withdrawals() -> list[dict[str, Any]]:
    controls = ControleLente.objects.filter(retirada_paciente=True).order_by("-dt_retirada", "cache_paciente")
    rows = []
    for controle in controls:
        tempo_chegada_contato = days_between(controle.cache_dt_chegada_lente, controle.dt_contato)
        tempo_contato_retirada = days_between(controle.dt_contato, controle.dt_retirada)
        tempo_total = days_between(controle.cache_dt_solicitacao, controle.dt_retirada)
        rows.append(
            {
                "paciente": controle.cache_paciente,
                "telefone": controle.cache_telefone,
                "nr_requisicao": controle.nr_requisicao,
                "dt_chegada_lente": controle.cache_dt_chegada_lente,
                "dt_contato": controle.dt_contato,
                "dt_retirada": controle.dt_retirada,
                "usuario_contato": controle.usuario_contato,
                "usuario_retirada": controle.usuario_retirada,
                "tempo_chegada_contato_label": days_label(tempo_chegada_contato),
                "tempo_contato_retirada_label": days_label(tempo_contato_retirada),
                "tempo_total_requisicao_label": days_label(tempo_total),
            }
        )
    return rows
