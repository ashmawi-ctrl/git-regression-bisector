# Git Regression Bisector

[![quality](https://github.com/ashmawi-ctrl/git-regression-bisector/actions/workflows/quality.yml/badge.svg)](https://github.com/ashmawi-ctrl/git-regression-bisector/actions/workflows/quality.yml)

A small debugging tool for locating the first commit that changes a verification command from passing to failing.

The project targets a maintenance problem that comes up in unfamiliar codebases: a test passes on an older revision, fails on a newer revision, and the useful question is **where did the behavior first change?**

Rather than repeatedly checking out commits in the caller's working directory, the tool evaluates revisions inside temporary detached Git worktrees.

## Current behavior

- validates that the target path belongs to a Git worktree
- resolves explicit known-good and known-bad revisions
- verifies the good boundary really passes
- verifies the bad boundary really fails
- walks the first-parent ancestry path between the two
- uses binary search to reduce the number of probes
- runs every probe in a temporary detached worktree
- leaves the caller's current checkout unchanged
- captures exit code, stdout, stderr, duration, and timeout state
- reports the first failing commit

## Install

Python 3.11+ and Git are required.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -e ".[dev]"
```

## Example

Suppose `v1.4.0` is known to pass and `main` is known to fail:

```bash
git-regression-bisector . \
  --good v1.4.0 \
  --bad main \
  -- python -m pytest tests/test_checkout.py -q
```

Example output:

```text
first bad commit: 8f42d8d9e0...
probes: 5
- 21f6032b45a1 pass exit=0 duration=0.311s
- 8f42d8d9e0ab fail exit=1 duration=0.284s
...
```

## Why temporary worktrees?

A debugging helper should not destroy the state you are already investigating.

Using `git worktree add --detach` means the verification command runs against an isolated checkout of each candidate commit. The original branch, staged files, and working directory are not switched during the search.

Worktrees are removed after each probe, including failed probes.

## Search model

The first version intentionally uses a **first-parent path** and assumes the behavior is monotonic across that path:

```text
pass, pass, pass, fail, fail, fail
```

With that assumption, binary search can find the first failing revision without evaluating every commit.

The tool checks both boundaries before searching. If the supplied good revision fails or the bad revision passes, it stops instead of returning a misleading answer.

## Timeout behavior

Each command has a 60-second timeout by default:

```bash
git-regression-bisector . \
  --good HEAD~20 \
  --bad HEAD \
  --timeout 15 \
  -- python -m pytest tests/test_worker.py -q
```

A timeout in the middle of the search is treated as an indeterminate probe and the search stops. The current version does not guess whether a timed-out revision is good or bad.

## Development

```bash
make install
make quality
```

The integration tests create a real temporary Git repository with multiple commits, introduce a regression, run the bisector, and verify that the caller's checkout was not moved.

## Engineering workflow

The initial implementation is tracked through:

- [Issue #1](https://github.com/ashmawi-ctrl/git-regression-bisector/issues/1)
- branch `feat/first-bad-commit`
- Git integration tests built from a temporary repository
- GitHub Actions lint and test checks
- a reviewable pull request

## Deliberate limitations

- first-parent history only
- assumes a single pass-to-fail transition
- timed-out or unbuildable middle commits stop the search
- does not clone remote repositories
- executes a trusted local command; it is not a sandbox for hostile code
- does not yet emit JSON or Markdown reports

Those constraints keep the first version small enough to reason about. Merge-heavy history and skipped commits need different search semantics rather than hidden heuristics.

## Next investigations

- machine-readable reports
- explicit skip handling for unbuildable commits
- keep/reuse worktrees for expensive dependency installs
- optional setup command per revision
- commit metadata in the final report
- comparison with native `git bisect run` behavior

## License

MIT
