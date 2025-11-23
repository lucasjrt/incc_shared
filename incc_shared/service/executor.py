from datetime import date

from incc_shared.exceptions.errors import InvalidState
from incc_shared.models.db.indexes.schedule import ScheduleIndexModel
from incc_shared.models.db.schedule.base import ScheduleStatus
from incc_shared.service.schedule import list_schedules_for_date
from incc_shared.service.utils import format_date

today = format_date(date.today())


class ScheduleFailed(Exception):
    pass


def validate_schedule(schedule: ScheduleIndexModel):
    issues = []
    if schedule.proximaExecucao != today:
        issues.append(
            f"Schedule should not be running today - expected: {schedule.proximaExecucao}"
        )

    if schedule.status != ScheduleStatus.ativo:
        issues.append(f"Non-active schedule triggered: {schedule.status.value}")

    if schedule.parcelas >= schedule.parcelasEmitidas:
        issues.append(
            f"Schedule is already complete - total: {schedule.parcelas}, current; {schedule.parcelasEmitidas}"
        )

    if schedule.dataInicio > schedule.proximaExecucao:
        issues.append(
            f"Schedule triggered before start date - expected: {schedule.dataInicio}"
        )

    if issues:
        raise InvalidState(f"{len(issues)} found with schedule {schedule.id}: {issues}")


def run_schedule(schedule: ScheduleIndexModel):
    validate_schedule(schedule)
    # 1. validate consistency of fields
    # 2. In an idempotent way, create a boleto
    # 3. Update schedule data
    return


def execute():
    # 1. Get the list of schedules
    schedules = list_schedules_for_date(date.today())
    failed_schedules = {}
    # 2. For each schedule run it
    for s in schedules:
        try:
            run_schedule(s)
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
