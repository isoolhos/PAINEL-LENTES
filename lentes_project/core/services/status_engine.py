from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Any, Iterable
import unicodedata

from django.utils import timezone


class LensStatus:
    REQUISITADA = "REQUISITADA"
    EM_COMPRA = "EM_COMPRA"
    COMPRADA = "COMPRADA"
    LENTE_CHEGOU = "LENTE_CHEGOU"
    PACIENTE_CONTATADO = "PACIENTE_CONTATADO"
    RETIRADA_PELO_PACIENTE = "RETIRADA_PELO_PACIENTE"
    ENTREGUE = RETIRADA_PELO_PACIENTE


STATUS_LABELS = {
    LensStatus.REQUISITADA: "Requisitada",
    LensStatus.EM_COMPRA: "Em compra",
    LensStatus.COMPRADA: "Comprada",
    LensStatus.LENTE_CHEGOU: "Lente chegou",
    LensStatus.PACIENTE_CONTATADO: "Paciente contatado",
    LensStatus.RETIRADA_PELO_PACIENTE: "Retirada pelo paciente",
}

STATUS_BADGE_CLASSES = {
    LensStatus.REQUISITADA: "text-bg-primary",
    LensStatus.EM_COMPRA: "text-bg-warning",
    LensStatus.COMPRADA: "text-bg-success",
    LensStatus.LENTE_CHEGOU: "text-bg-info",
    LensStatus.PACIENTE_CONTATADO: "text-bg-secondary",
    LensStatus.RETIRADA_PELO_PACIENTE: "text-bg-dark",
}

STATUS_ORDER = [
    LensStatus.REQUISITADA,
    LensStatus.EM_COMPRA,
    LensStatus.COMPRADA,
    LensStatus.LENTE_CHEGOU,
    LensStatus.PACIENTE_CONTATADO,
    LensStatus.RETIRADA_PELO_PACIENTE,
]


@dataclass(frozen=True)
class HistoryEntry:
    text: str
    happened_at: datetime | None


def normalize_text(value: Any) -> str:
    if value is None:
        return ""
    normalized = unicodedata.normalize("NFKD", str(value))
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return " ".join(ascii_text.upper().split())


def ensure_aware_datetime(value: Any) -> datetime | None:
    if value in {None, ""}:
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        parsed = datetime.combine(value, time.min)
    else:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(str(value), fmt)
                break
            except ValueError:
                parsed = None
        if parsed is None:
            return None

    if timezone.is_naive(parsed):
        return timezone.make_aware(parsed, timezone.get_current_timezone())
    return parsed


def days_since(value: datetime | None) -> int | None:
    if value is None:
        return None
    return max((timezone.localdate() - timezone.localtime(value).date()).days, 0)


def days_label(value: int | None) -> str:
    if value is None:
        return "-"
    suffix = "" if value == 1 else "s"
    return f"{value} dia{suffix}"


def days_between(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    start_date = timezone.localtime(start).date()
    end_date = timezone.localtime(end).date()
    return max((end_date - start_date).days, 0)


def compact_phone(value: Any) -> str:
    return " ".join(str(value or "").split())


def truthy_database_flag(value: Any) -> bool:
    if value in {None, "", 0, False}:
        return False
    if isinstance(value, str):
        return value.strip().upper() in {"1", "S", "SIM", "Y", "YES", "TRUE"}
    return bool(value)


def extract_history(record: dict[str, Any]) -> list[HistoryEntry]:
    history_items = record.get("historicos") or record.get("historico") or []

    if isinstance(history_items, str):
        return [HistoryEntry(text=history_items, happened_at=ensure_aware_datetime(record.get("dt_historico")))]

    entries: list[HistoryEntry] = []
    for item in history_items:
        if isinstance(item, dict):
            text = (
                item.get("ds_historico")
                or item.get("historico")
                or item.get("texto")
                or item.get("DS_HISTORICO")
                or ""
            )
            happened_at = ensure_aware_datetime(
                item.get("dt_historico")
                or item.get("dt_atualizacao")
                or item.get("DT_HISTORICO")
                or item.get("DT_ATUALIZACAO")
            )
        else:
            text = str(item)
            happened_at = None
        entries.append(HistoryEntry(text=str(text), happened_at=happened_at))

    if record.get("historico_chegada"):
        entries.append(
            HistoryEntry(
                text=str(record.get("historico_chegada")),
                happened_at=ensure_aware_datetime(record.get("dt_chegada_lente")),
            )
        )
    return entries


def history_contains(entries: Iterable[HistoryEntry], needle: str) -> bool:
    normalized_needle = normalize_text(needle)
    return any(normalized_needle in normalize_text(entry.text) for entry in entries)


def first_history_date(entries: Iterable[HistoryEntry], needle: str) -> datetime | None:
    normalized_needle = normalize_text(needle)
    dates = [
        entry.happened_at
        for entry in entries
        if entry.happened_at and normalized_needle in normalize_text(entry.text)
    ]
    return min(dates) if dates else None


def latest_datetime(*values: datetime | None) -> datetime | None:
    present = [value for value in values if value is not None]
    return max(present) if present else None


def latest_history_datetime(entries: Iterable[HistoryEntry]) -> datetime | None:
    dates = [entry.happened_at for entry in entries if entry.happened_at]
    return max(dates) if dates else None


def filter_history_since(entries: Iterable[HistoryEntry], started_at: datetime | None) -> list[HistoryEntry]:
    if started_at is None:
        return list(entries)
    return [entry for entry in entries if entry.happened_at and entry.happened_at >= started_at]


def valid_event_datetime(value: Any, started_at: datetime | None) -> datetime | None:
    event_at = ensure_aware_datetime(value)
    if event_at is None:
        return None
    if started_at and event_at < started_at:
        return None
    return event_at


def calculate_logistic_status(record: dict[str, Any], history: list[HistoryEntry]) -> str:
    if history_contains(history, "CHEG LC") or ensure_aware_datetime(record.get("dt_chegada_lente")):
        return LensStatus.LENTE_CHEGOU
    if ensure_aware_datetime(record.get("dt_baixa")):
        return LensStatus.COMPRADA
    if (
        truthy_database_flag(record.get("has_solic_compra_item"))
        or record.get("nr_solic_compra")
        or record.get("dt_solic_compra")
    ):
        return LensStatus.EM_COMPRA
    return LensStatus.REQUISITADA


def calculate_operational_status(logistic_status: str, local_record: Any | None = None) -> str:
    if logistic_status != LensStatus.LENTE_CHEGOU:
        return logistic_status
    if getattr(local_record, "retirada_paciente", False):
        return LensStatus.RETIRADA_PELO_PACIENTE
    if getattr(local_record, "paciente_contatado", False):
        return LensStatus.PACIENTE_CONTATADO
    return logistic_status


def status_reference_date(
    status: str,
    record: dict[str, Any],
    history: list[HistoryEntry],
    dt_solicitacao: datetime | None,
    dt_baixa: datetime | None,
    dt_chegada_lente: datetime | None,
    local_record: Any | None = None,
) -> datetime | None:
    if status == LensStatus.RETIRADA_PELO_PACIENTE:
        return getattr(local_record, "dt_retirada", None)
    if status == LensStatus.PACIENTE_CONTATADO:
        return getattr(local_record, "dt_contato", None)
    if status == LensStatus.LENTE_CHEGOU:
        return dt_chegada_lente or first_history_date(history, "CHEG LC")
    if status == LensStatus.COMPRADA:
        return dt_baixa
    if status == LensStatus.EM_COMPRA:
        return ensure_aware_datetime(record.get("dt_solic_compra")) or dt_solicitacao
    return dt_solicitacao


def calculate_urgency(status: str, dias_em_status: int | None) -> dict[str, str]:
    if status == LensStatus.RETIRADA_PELO_PACIENTE:
        return {"nivel": "concluido", "label": "Concluído", "class": "text-bg-secondary"}
    if dias_em_status is None or dias_em_status < 3:
        return {"nivel": "verde", "label": "No prazo", "class": "text-bg-success"}
    if dias_em_status <= 7:
        return {"nivel": "amarelo", "label": "Atenção", "class": "text-bg-warning"}
    return {"nivel": "vermelho", "label": "Atrasada", "class": "text-bg-danger"}


def calculate_kpis(items: Iterable[dict[str, Any]]) -> dict[str, int]:
    items = list(items)
    today = timezone.localdate()
    open_items = [item for item in items if item["status"] != LensStatus.RETIRADA_PELO_PACIENTE]

    return {
        "total_em_aberto": len(open_items),
        "em_compra": sum(1 for item in items if item["status"] == LensStatus.EM_COMPRA),
        "lentes_chegaram_hoje": sum(
            1
            for item in items
            if item["dt_chegada_lente"] and timezone.localtime(item["dt_chegada_lente"]).date() == today
        ),
        "atrasadas": sum(1 for item in open_items if (item["dias_em_status"] or 0) > 7),
        "aguardando_contato": sum(1 for item in items if item["status"] == LensStatus.LENTE_CHEGOU),
        "contatados_aguardando_retirada": sum(
            1 for item in items if item["status"] == LensStatus.PACIENTE_CONTATADO
        ),
        "retiradas_hoje": sum(
            1
            for item in items
            if item.get("dt_retirada") and timezone.localtime(item["dt_retirada"]).date() == today
        ),
    }


def build_lens_item(
    record: dict[str, Any],
    local_record: Any | None = None,
) -> dict[str, Any]:
    history = extract_history(record)
    dt_solicitacao = ensure_aware_datetime(record.get("dt_solicitacao"))
    history_for_request = filter_history_since(history, dt_solicitacao)
    dt_baixa = ensure_aware_datetime(record.get("dt_baixa"))
    dt_chegada_lente = valid_event_datetime(record.get("dt_chegada_lente"), dt_solicitacao) or first_history_date(
        history_for_request,
        "CHEG LC",
    )
    dt_historico = latest_history_datetime(history_for_request)
    dt_contato = getattr(local_record, "dt_contato", None)
    dt_retirada = getattr(local_record, "dt_retirada", None)
    usuario_contato = getattr(local_record, "usuario_contato", "")
    usuario_retirada = getattr(local_record, "usuario_retirada", "")
    paciente_contatado = bool(getattr(local_record, "paciente_contatado", False))
    retirada_paciente = bool(getattr(local_record, "retirada_paciente", False))

    dt_ultima_atualizacao = latest_datetime(
        ensure_aware_datetime(record.get("dt_ultima_atualizacao")),
        dt_retirada,
        dt_contato,
        dt_historico,
        dt_chegada_lente,
        dt_baixa,
        ensure_aware_datetime(record.get("dt_compra")),
        ensure_aware_datetime(record.get("dt_solic_compra")),
        dt_solicitacao,
    )

    logistic_record = {**record, "dt_chegada_lente": dt_chegada_lente}
    status_logistico = calculate_logistic_status(logistic_record, history_for_request)
    status = calculate_operational_status(status_logistico, local_record)
    dt_referencia_status = status_reference_date(
        status,
        logistic_record,
        history_for_request,
        dt_solicitacao,
        dt_baixa,
        dt_chegada_lente,
        local_record,
    )
    dias_em_status = days_since(dt_referencia_status)
    dias_desde_solicitacao = days_since(dt_solicitacao)
    dias_desde_ultima_movimentacao = days_since(dt_ultima_atualizacao)
    urgencia = calculate_urgency(status, dias_em_status)
    tempo_chegada_contato = days_between(dt_chegada_lente, dt_contato)
    tempo_contato_retirada = days_between(dt_contato, dt_retirada)
    tempo_total_requisicao = days_between(dt_solicitacao, dt_retirada) if dt_retirada else days_since(dt_solicitacao)

    return {
        "nr_requisicao": str(record.get("nr_requisicao") or "").strip(),
        "paciente": str(record.get("paciente") or "").strip(),
        "requisitante": str(record.get("requisitante") or "").strip(),
        "telefone": compact_phone(record.get("telefone") or record.get("nr_telefone_celular")),
        "dt_solicitacao": dt_solicitacao,
        "dt_chegada_lente": dt_chegada_lente,
        "dt_ultima_atualizacao": dt_ultima_atualizacao,
        "dt_ultima_atualizacao_historico": dt_historico,
        "status_logistico": status_logistico,
        "status_logistico_label": STATUS_LABELS[status_logistico],
        "status": status,
        "status_label": STATUS_LABELS[status],
        "status_class": STATUS_BADGE_CLASSES[status],
        "dias_em_status": dias_em_status,
        "dias_em_status_label": days_label(dias_em_status),
        "dias_desde_solicitacao": dias_desde_solicitacao,
        "dias_desde_solicitacao_label": days_label(dias_desde_solicitacao),
        "dias_desde_ultima_movimentacao": dias_desde_ultima_movimentacao,
        "dias_desde_ultima_movimentacao_label": days_label(dias_desde_ultima_movimentacao),
        "urgencia": urgencia,
        "paciente_contatado": paciente_contatado,
        "dt_contato": dt_contato,
        "usuario_contato": usuario_contato,
        "retirada_paciente": retirada_paciente,
        "dt_retirada": dt_retirada,
        "usuario_retirada": usuario_retirada,
        "foi_contatado": paciente_contatado,
        "foi_retirado": retirada_paciente,
        "can_mark_contact": status == LensStatus.LENTE_CHEGOU,
        "can_confirm_withdrawal": status == LensStatus.PACIENTE_CONTATADO,
        "tempo_chegada_contato_dias": tempo_chegada_contato,
        "tempo_chegada_contato_label": days_label(tempo_chegada_contato),
        "tempo_contato_retirada_dias": tempo_contato_retirada,
        "tempo_contato_retirada_label": days_label(tempo_contato_retirada),
        "tempo_total_requisicao_dias": tempo_total_requisicao,
        "tempo_total_requisicao_label": days_label(tempo_total_requisicao),
    }


def build_dashboard_payload(
    records: Iterable[dict[str, Any]],
    local_records_by_requisition: dict[str, Any] | None = None,
) -> dict[str, Any]:
    local_records_by_requisition = local_records_by_requisition or {}
    items = [
        build_lens_item(record, local_records_by_requisition.get(str(record.get("nr_requisicao") or "").strip()))
        for record in records
        if record.get("nr_requisicao")
    ]

    items.sort(
        key=lambda item: (
            item["status"] == LensStatus.RETIRADA_PELO_PACIENTE,
            -(item["dias_em_status"] or 0),
            item["paciente"],
        )
    )

    kanban = {
        status: [item for item in items if item["status"] == status]
        for status in STATUS_ORDER
    }

    return {
        "items": items,
        "kpis": calculate_kpis(items),
        "kanban": kanban,
        "status_order": STATUS_ORDER,
        "status_labels": STATUS_LABELS,
        "generated_at": timezone.now(),
    }
