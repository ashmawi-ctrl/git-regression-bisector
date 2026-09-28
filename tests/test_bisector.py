import subprocess
from pathlib import Path

import pytest

from regression_bisector.runner import BisectError, bisect_first_bad


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def commit_file(repo: Path, name: str, content: str, message: str) -> str:
    (repo / name).write_text(content, encoding="utf-8")
    git(repo, "add", name)
    git(repo, "commit", "-m", message)
    return git(repo, "rev-parse", "HEAD")


@pytest.fixture
def history_repo(tmp_path: Path) -> tuple[Path, str, str, str]:
    repo = tmp_path / "fixture"
    repo.mkdir()
    git(repo, "init")
    git(repo, "config", "user.name", "Regression Fixture")
    git(repo, "config", "user.email", "fixture@example.com")

    (repo / "check.py").write_text(
        "from pathlib import Path\n"
        "raise SystemExit(0 if Path('state.txt').read_text().strip() == 'good' else 1)\n",
        encoding="utf-8",
    )
    (repo / "state.txt").write_text("good\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "known good")
    good = git(repo, "rev-parse", "HEAD")

    commit_file(repo, "notes.txt", "still fine\n", "unrelated change")
    first_bad = commit_file(repo, "state.txt", "bad\n", "introduce regression")
    bad = commit_file(repo, "notes.txt", "still broken\n", "later change")

    return repo, good, first_bad, bad


def test_finds_first_bad_commit_without_moving_caller_checkout(
    history_repo,
) -> None:
    repo, good, first_bad, bad = history_repo
    original_head = git(repo, "rev-parse", "HEAD")

    result = bisect_first_bad(
        repo,
        good_ref=good,
        bad_ref=bad,
        command=("python", "check.py"),
    )

    assert result.first_bad_commit == first_bad
    assert git(repo, "rev-parse", "HEAD") == original_head
    assert len(result.probes) <= 4


def test_rejects_a_good_revision_that_already_fails(history_repo) -> None:
    repo, _, first_bad, bad = history_repo

    with pytest.raises(BisectError, match="known-good"):
        bisect_first_bad(
            repo,
            good_ref=first_bad,
            bad_ref=bad,
            command=("python", "check.py"),
        )


def test_rejects_a_bad_revision_that_passes(history_repo) -> None:
    repo, good, _, _ = history_repo

    with pytest.raises(BisectError, match="known-bad"):
        bisect_first_bad(
            repo,
            good_ref=good,
            bad_ref=good + "^0",
            command=("python", "check.py"),
        )
