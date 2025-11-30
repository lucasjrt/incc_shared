from datetime import date

from dateutil.relativedelta import relativedelta
from freezegun import freeze_time

from incc_shared.admin.service.executor import execute_schedules
from incc_shared.admin.service.schedule import list_schedules_for_date
from incc_shared.models.db.schedule import ScheduleModel
from incc_shared.models.db.schedule.base import ScheduleStatus
from incc_shared.service.boleto import list_boletos
from incc_shared.service.schedule import get_schedule
from tests.conftest import SCHEDULE_DATE

data_execucao = SCHEDULE_DATE


@freeze_time(data_execucao)
def test_executor_lifecycle(
    test_schedule: ScheduleModel,
    test_schedule_balao: ScheduleModel,
):
    assert date.today() == SCHEDULE_DATE, "Executor date is not properly set"

    schedule = get_schedule(test_schedule.id)
    assert schedule
    assert schedule.proximaExecucao == data_execucao

    schedule_balao = get_schedule(test_schedule_balao.id)
    assert schedule_balao
    assert schedule_balao.proximaExecucao == data_execucao

    schedules = list_schedules_for_date(date.today())
    assert len(schedules) == 2

    execute_schedules()
    assert len(list_schedules_for_date(date.today())) == 0
    updated_schedule = get_schedule(test_schedule.id)
    updated_schedule_balao = get_schedule(test_schedule_balao.id)

    assert updated_schedule
    assert updated_schedule.proximaExecucao == data_execucao + relativedelta(
        months=test_schedule.intervaloParcelas
    )
    assert updated_schedule.parcelasEmitidas == 1

    assert updated_schedule_balao
    assert updated_schedule_balao.proximaExecucao == data_execucao + relativedelta(
        months=test_schedule_balao.intervaloParcelas
    )
    assert updated_schedule_balao.parcelasEmitidas == 1

    boletos = list_boletos()
    assert len(boletos) == 2

    remaining = updated_schedule.parcelas - updated_schedule.parcelasEmitidas - 1
    for i in range(remaining + 1):
        mock_date = data_execucao + relativedelta(months=1 + i)
        with freeze_time(mock_date):
            today = date.today()
            assert len(list_schedules_for_date(today)) in {1, 2}
            execute_schedules()
            executed_schedule = get_schedule(test_schedule.id)
            assert executed_schedule
            assert executed_schedule.parcelasEmitidas == i + 2

    completed_schedule = get_schedule(test_schedule.id)
    assert completed_schedule
    assert completed_schedule.status == ScheduleStatus.concluido
    assert completed_schedule.parcelasEmitidas == completed_schedule.parcelas
    assert completed_schedule.proximaExecucao is None

    completed_schedule_balao = get_schedule(test_schedule_balao.id)
    assert completed_schedule_balao
    assert completed_schedule_balao.status == ScheduleStatus.concluido
    assert (
        completed_schedule_balao.parcelasEmitidas == completed_schedule_balao.parcelas
    )
    assert completed_schedule_balao.proximaExecucao is None

    # boletos = list_boletos()
    # print("Boletos:")
    # import json
    #
    # for b in boletos:
    #     print(json.dumps(b.to_item(), indent=2, default=str))

    # TODO write tests for:
    # - Non-active schedules
