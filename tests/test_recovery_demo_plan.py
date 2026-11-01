import copy
import json

import pytest

from scripts.run_recovery_demo import PLAN, build_jobs


def test_replacement_jobs_are_fixed_and_not_final_test_or_replay_remediation():
    jobs = build_jobs(json.loads(PLAN.read_text()))
    assert [job["training_seed"] for job in jobs] == [20261111, 20261112]
    for job in jobs:
        command = job["command"]
        assert command[command.index("--total-timesteps") + 1] == "100000"
        assert "--split" not in command
        assert "--successful-replay-stratification" not in command
        assert "--successful-replay-relabel" not in command
        assert command[command.index("--algo") + 1] == "uniform-pcqn"


@pytest.mark.parametrize("field,value", [("course_evidence", True), ("final_test_permitted", True)])
def test_replacement_plan_cannot_be_promoted_to_scientific_evidence(field, value):
    plan = copy.deepcopy(json.loads(PLAN.read_text()))
    plan[field] = value
    with pytest.raises(ValueError, match="expanded"):
        build_jobs(plan)


def test_replacement_plan_rejects_output_outside_artifacts():
    plan = json.loads(PLAN.read_text())
    plan["output_root"] = "../outside"
    with pytest.raises(ValueError, match="workspace artifacts"):
        build_jobs(plan)
