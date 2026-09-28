import subprocess
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class GitError(RuntimeError):
    pass


def ensure_git_worktree(repo: Path) -> Path:
    resolved = repo.resolve()
    result = _git(resolved, "rev-parse", "--show-toplevel")
    top_level = Path(result.stdout.strip()).resolve()
    return top_level


def resolve_commit(repo: Path, ref: str) -> str:
    result = _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    return result.stdout.strip()


def commit_subject(repo: Path, commit: str) -> str:
    result = _git(repo, "show", "-s", "--format=%s", commit)
    return result.stdout.strip()


def first_parent_path(repo: Path, good: str, bad: str) -> tuple[str, ...]:
    ancestor = subprocess.run(
        ["git", "-C", str(repo), "merge-base", "--is-ancestor", good, bad],
        capture_output=True,
        text=True,
        check=False,
    )
    if ancestor.returncode != 0:
        raise GitError(
            "good revision must be an ancestor of bad revision"
        )

    result = _git(
        repo,
        "rev-list",
        "--first-parent",
        "--ancestry-path",
        "--reverse",
        f"{good}..{bad}",
    )
    commits = tuple(
        line.strip()
        for line in result.stdout.splitlines()
        if line.strip()
    )
    if not commits or commits[-1] != bad:
        raise GitError("could not build a first-parent path to bad revision")
    return commits


@contextmanager
def detached_worktree(repo: Path, commit: str) -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="regression-bisect-") as temp_dir:
        workspace = Path(temp_dir) / "worktree"
        _git(repo, "worktree", "add", "--detach", str(workspace), commit)
        try:
            yield workspace
        finally:
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo),
                    "worktree",
                    "remove",
                    "--force",
                    str(workspace),
                ],
                capture_output=True,
                text=True,
                check=False,
            )


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise GitError(detail or f"git command failed: {' '.join(args)}")
    return result
