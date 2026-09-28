from dataclasses import dataclass


@dataclass(frozen=True)
class ProbeResult:
    commit: str
    subject: str
    command: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return not self.timed_out and self.exit_code == 0


@dataclass(frozen=True)
class BisectResult:
    first_bad_commit: str
    first_bad_subject: str
    probes: tuple[ProbeResult, ...]
