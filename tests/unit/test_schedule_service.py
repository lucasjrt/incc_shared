from ulid import ULID

from incc_shared.models.db.schedule import ScheduleModel
from incc_shared.models.db.schedule.base import ScheduleStatus
from incc_shared.models.request.schedule.update import UpdateScheduleModel
from incc_shared.service import to_model
from incc_shared.service.schedule import (
    delete_schedule,
    get_schedule,
    list_schedules,
    update_schedule,
)


def test_customer_lifecycle(
    test_org_id: ULID,
    test_schedule: ScheduleModel,
    test_schedule_balao: ScheduleModel,
    schedule_data: dict,
):
    assert test_schedule.valorBase == schedule_data["valorBase"]
    assert test_schedule.pagador == schedule_data["pagador"]
    assert test_schedule.vencimento == schedule_data["vencimento"]
    assert test_schedule.parcelas == schedule_data["parcelas"]
    assert test_schedule.dataInicio == schedule_data["dataInicio"]

    schedule = get_schedule(test_org_id, test_schedule.id)
    assert schedule is not None

    schedules = list_schedules(test_org_id)
    assert len(schedules) == 2
    ids = [test_schedule.id, test_schedule_balao.id]
    for s in schedules:
        assert s.id in ids

    update_fields = {
        "valorBase": 15,
        "status": ScheduleStatus.cancelado.value,
    }
    update_model = to_model(update_fields, UpdateScheduleModel)

    update_schedule(test_org_id, test_schedule.id, update_model)
    updated_schedule = get_schedule(test_org_id, test_schedule.id)
    assert updated_schedule
    assert updated_schedule.valorBase == update_model.valorBase
    assert updated_schedule.status == update_model.status

    delete_schedule(test_org_id, test_schedule.id)
    assert get_schedule(test_org_id, test_schedule.id) is None
