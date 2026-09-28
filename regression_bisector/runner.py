import subprocess
import time
from pathlib import Path

from .git import (
    commit_subject,
    detached_worktree,
    ensure_git_worktree,
    first_parent_path,
    resolve_commit,
)
from .models import BisectResult, ProbeResult


class BisectError(RuntimeError):
    pass


def run_probe(
    repo: Path,
    commit: str,
    command: tuple[str, ...],
    *,
    timeout_seconds: float = 60.0,
) -> ProbeResult:
    if not command:
        raise ValueError("verification command cannot be empty")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than 0")

    with detached_worktree(repo, commit) as workspace:
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return ProbeResult(
                commit=commit,
                subject=commit_subject(repo, commit),
                command=command,
                exit_code=None,
                stdout=_as_text(exc.stdout),
                stderr=_as_text(exc.stderr),
                duration_seconds=time.perf_counter() - started,
                timed_out=True,
            )

    return ProbeResult(
        commit=commit,
        subject=commit_subject(repo, commit),
        command=command,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.perf_counter() - started,
    )


def bisect_first_bad(
    repo: str | Path,
    *,
    good_ref: str,
    bad_ref: str,
    command: tuple[str, ...],
    timeout_seconds: float = 60.0,
) -> BisectResult:
    repo_path = ensure_git_worktree(Path(repo))
    good = resolve_commit(repo_path, good_ref)
    bad = resolve_commit(repo_path, bad_ref)

    if good == bad:
        raise BisectError("good and bad revisions resolve to the same commit")

    candidates = first_parent_path(repo_path, good, bad)
    cache: dict[str, ProbeResult] = {}
    probe_order: list[ProbeResult] = []

    def probe(commit: str) -> ProbeResult:
        if commit not in cache:
            result = run_probe(
                repo_path,
                commit,
                command,
                timeout_seconds=timeout_seconds,
            )
            cache[commit] = result
            probe_order.append(result)
        return cache[commit]

    good_result = probe(good)
    if not good_result.passed:
        raise BisectError("known-good revision does not pass verification")

    bad_result = probe(bad)
    if bad_result.passed:
        raise BisectError("known-bad revision unexpectedly passes verification")
    if bad_result.timed_out:
        raise BisectError("known-bad revision timed out during verification")

    low = 0
    high = len(candidates) - 1

    while low < high:
        middle = (low + high) // 2
        result = probe(candidates[middle])

        if result.timed_out:
            raise BisectError(
                f"verification timed out at {result.commit[:12]}"
            )

        if result.passed:
            low = middle + 1
        else:
            high = middle

    first_bad = candidates[low]
    return BisectResult(
        first_bad_commit=first_bad,
        first_bad_subject=commit_subject(repo_path, first_bad),
        probes=tuple(probe_order),
    )


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
