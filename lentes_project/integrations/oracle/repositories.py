from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from django.conf import settings

from .client import fetch_all_dicts, oracle_connection
from .queries import HISTORICO_PACIENTE_SQL, REQUISICOES_LENTES_SQL
from .sample_data import get_sample_lens_records


class TasyLentesRepository:
    def list_requisicoes_lentes(self, days_back: int | None = None) -> list[dict]:
        if not settings.ORACLE_ENABLED:
            return get_sample_lens_records() if settings.LENTES_USE_SAMPLE_DATA else []

        days_back = days_back or settings.ORACLE_QUERY_DAYS_BACK
        with oracle_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    REQUISICOES_LENTES_SQL,
                    {"days_back": days_back},
                )
                requisicoes = fetch_all_dicts(cursor)

                historicos = self._fetch_historicos(
                    cursor,
                    [row.get("cd_pessoa_fisica") for row in requisicoes if row.get("cd_pessoa_fisica")],
                    days_back,
                )

        for requisicao in requisicoes:
            key = str(requisicao.get("cd_pessoa_fisica") or "")
            requisicao["historicos"] = historicos.get(key, [])
        return requisicoes

    def _fetch_historicos(self, cursor, cd_pessoas: Iterable, days_back: int) -> dict[str, list[dict]]:
        ids = list(dict.fromkeys(str(cd_pessoa) for cd_pessoa in cd_pessoas if cd_pessoa))
        grouped: dict[str, list[dict]] = defaultdict(list)

        for chunk in self._chunks(ids, 900):
            bind_names = [f"pessoa_{index}" for index, _ in enumerate(chunk)]
            sql = HISTORICO_PACIENTE_SQL.format(binds=", ".join(f":{name}" for name in bind_names))
            params = {"days_back": days_back}
            params.update(dict(zip(bind_names, chunk)))
            cursor.execute(sql, params)
            for row in fetch_all_dicts(cursor):
                grouped[str(row.get("cd_pessoa_fisica"))].append(row)

        return grouped

    @staticmethod
    def _chunks(values: list[str], size: int) -> Iterable[list[str]]:
        for index in range(0, len(values), size):
            yield values[index : index + size]
