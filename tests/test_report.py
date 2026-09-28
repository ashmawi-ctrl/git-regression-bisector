import json

from regression_bisector.models import BisectResult, ProbeResult
from regression_bisector.report import render_json


def test_json_report_includes_first_bad_context_and_probe_output() -> None:
    result = BisectResult(
        first_bad_commit="abc123",
        first_bad_subject="introduce regression",
        probes=(
            ProbeResult(
                commit="abc123",
                subject="introduce regression",
                command=("pytest", "-q"),
                exit_code=1,
                stdout="failed output",
                stderr="",
                duration_seconds=0.25,
            ),
        ),
    )

    payload = json.loads(render_json(result))

    assert payload["first_bad"] == {
        "commit": "abc123",
        "subject": "introduce regression",
    }
    assert payload["probe_count"] == 1
    assert payload["probes"][0]["command"] == ["pytest", "-q"]
    assert payload["probes"][0]["passed"] is False
    assert payload["probes"][0]["stdout"] == "failed output"
