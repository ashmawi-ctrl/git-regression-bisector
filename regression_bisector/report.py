import json
from dataclasses import asdict

from .models import BisectResult


def result_to_dict(result: BisectResult) -> dict:
    return {
        "first_bad": {
            "commit": result.first_bad_commit,
            "subject": result.first_bad_subject,
        },
        "probe_count": len(result.probes),
        "probes": [
            {
                **asdict(probe),
                "command": list(probe.command),
                "passed": probe.passed,
            }
            for probe in result.probes
        ],
    }


def render_json(result: BisectResult) -> str:
    return json.dumps(result_to_dict(result), indent=2)
