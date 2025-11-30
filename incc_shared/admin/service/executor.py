from datetime import date
from typing import Any, Dict, List

from dateutil.relativedelta import relativedelta

from incc_shared.admin.service.schedule import list_schedules_for_date
from incc_shared.auth.context import impersonate
from incc_shared.constants import EntityType
from incc_shared.exceptions.errors import IdempotencyError, InvalidState
from incc_shared.models import ConstrainedMoney
from incc_shared.models.db.boleto.base import StatusBoleto
from incc_shared.models.db.indexes.schedule import ScheduleIndexModel
from incc_shared.models.db.schedule.base import ScheduleStatus
from incc_shared.models.request.boleto.create import CreateBoletoModel
from incc_shared.models.request.schedule.update import UpdateScheduleModel
from incc_shared.service.boleto import create_boleto, get_boleto
from incc_shared.service.calculator import (
    calcula_valor,
    formata_data_indice,
    get_incc_map,
)
from incc_shared.service.organization import get_org
from incc_shared.service.schedule import update_schedule
from incc_shared.service.storage.dynamodb import acquire_idempotency_lock


class ScheduleFailed(Exception):
    pass


def validate_schedule(schedule: ScheduleIndexModel):
    today = date.today()
    issues = []
    if schedule.proximaExecucao != today:
        issues.append(
            f"Schedule should not be running today - expected: {schedule.proximaExecucao}, today: {today}"
        )

    if schedule.status != ScheduleStatus.ativo:
        issues.append(f"Non-active schedule triggered: {schedule.status.value}")

    if schedule.parcelasEmitidas >= schedule.parcelas:
        issues.append(
            f"Schedule is already complete - total: {schedule.parcelas}, current; {schedule.parcelasEmitidas}"
        )

    if schedule.dataInicio > schedule.proximaExecucao:
        issues.append(
            f"Schedule triggered before start date - expected: {schedule.dataInicio}"
        )

    if issues:
        raise InvalidState(f"{len(issues)} found with schedule {schedule.id}: {issues}")


def valor_reajustado(valor_base: ConstrainedMoney, data_inicio: date):
    data_fim = date.today()
    return calcula_valor(valor_base, data_inicio, data_fim=data_fim)


def get_data_indice():
    return date.today().replace(day=1) - relativedelta(months=1)


def get_indice_reajuste():
    mapa_incc = get_incc_map()
    return mapa_incc[formata_data_indice(get_data_indice())]


def run_schedule(schedule: ScheduleIndexModel, nosso_numero: int):
    # 1. validate consistency of fields
    validate_schedule(schedule)

    # 2. In an idempotent way, create a boleto
    valor = valor_reajustado(schedule.valorBase, schedule.dataInicio)
    vencimento = schedule.vencimento + relativedelta(months=schedule.parcelasEmitidas)
    parcela_atual = schedule.parcelasEmitidas + 1
    boleto_data = {
        "valor": valor,
        "vencimento": vencimento,
        "agendamento": f"{schedule.id}#{parcela_atual}",
        "dataBaseReajuste": schedule.dataInicio,
        "dataIndiceReajuste": get_data_indice(),
        "indiceReajuste": get_indice_reajuste(),
        "emissao": date.today(),
        "pagador": schedule.pagador,
    }
    boleto = CreateBoletoModel(**boleto_data)

    boleto_entity = f"BOLETO#{nosso_numero}"
    lock_key = f"{schedule.id}#{parcela_atual}"
    lock_metadata = {"nossoNumero": nosso_numero, "scheduleId": schedule.to_item()}
    try:
        acquire_idempotency_lock(
            EntityType.boleto, lock_key, boleto_entity, lock_metadata
        )
        create_boleto(boleto)
    except IdempotencyError as e:
        print(
            f"Failed to acquire lock while running schedule {schedule.id}. Checking if it already exists"
        )
        metadata = e.metadata
        if not metadata:
            raise InvalidState("Failed to create boleto, and to check its existance")
        existing_id = metadata.get("nossoNumero")
        if not existing_id or existing_id != nosso_numero:
            raise InvalidState(
                f"Lock contains invalid boleto id - expected: {nosso_numero} actual: {existing_id}"
            )

        existing_boleto = get_boleto(existing_id)
        if existing_boleto and StatusBoleto.emitido in existing_boleto.status:
            print("Boleto already issued")
            return

        print("Boleto likely failed to issue. Trying again")
        create_boleto(boleto)

    # 3. Update schedule data
    new_schedule_data: Dict[str, Any] = {
        "parcelasEmitidas": parcela_atual,
    }

    if parcela_atual == schedule.parcelas:
        new_schedule_data["status"] = ScheduleStatus.concluido
        proxima_execucao = None
    else:
        current_date = date.today()
        proxima_execucao = current_date + relativedelta(
            months=schedule.intervaloParcelas
        )
        new_schedule_data["proximaExecucao"] = proxima_execucao

    new_schedule = UpdateScheduleModel(**new_schedule_data)
    update_schedule(
        schedule.id, new_schedule, remove_from_index=proxima_execucao is None
    )


def group_by_org(schedule_list: List[ScheduleIndexModel]):
    schedules = {}
    for s in schedule_list:
        org_id = s.orgId
        if org_id not in schedules:
            schedules[org_id] = []

        schedules[org_id].append(s)
    return schedules


def execute_schedules():
    # 1. Get the list of schedules
    schedule_list = list_schedules_for_date(date.today())
    schedules = group_by_org(schedule_list)
    failed_schedules = {}
    # 2. For each schedule run it
    for org_id, org_schedules in schedules.items():
        with impersonate(org_id):
            org = get_org()
            if not org:
                raise InvalidState("Could not get org from schedule")

            if org.orgId != org_id:
                raise InvalidState("Failed to impersonate org")

            nosso_numero = org.nossoNumero
            for s in org_schedules:
                try:
                    run_schedule(s, nosso_numero)
                    nosso_numero += 1
                except Exception as e:
                    orgId = s.orgId
                    print(f"Failed to run schedule: {e}")
                    if orgId not in failed_schedules:
                        failed_schedules[orgId] = []

                    failed_schedules[orgId].append(
                        {
                            "schedule_id": s.id,
                            "reason": e,
                        }
                    )

    if failed_schedules:
        total = 0
        print("Summary:")
        for org, sched in failed_schedules.items():
            failed = len(sched)
            print(f"- {org}: failed {failed} schedules")
            total += failed
        print(f"Total: {total}")
        raise ScheduleFailed()
